"""Only run_phase.sh: one native vehicle and replay within a frozen new window."""
import fcntl,hashlib,importlib.util,json,math,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path[:0]=[str(C),str(R/'experiments/v1023_dense_input_route')]
from owner import Owner
from causal import Evidence,packet,brake
from input_route import construct
from certificate import audit
from whole_input import public_setup

def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def file_sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def authorized(task,receipt):
    approval=json.loads((R/'runs/v1024_full_route_execution/APPROVAL.json').read_text());window=json.loads((R/'runs/v1024_full_route_execution/ROUND_WINDOW.json').read_text());freeze=json.loads((C/'SOURCE_FREEZE.json').read_text())
    assert approval['models_authorized']is True and receipt['window_sha256']==file_sha(R/'runs/v1024_full_route_execution/ROUND_WINDOW.json')
    assert task==next(x for x in json.loads((C/'TASKS.json').read_text())if x['task_id']==receipt['task_id'])
    assert time.time()<window['absolute_deadline_unix']-900,'INSUFFICIENT_ROOT_RESERVE'
    assert receipt['source_freeze_sha256']==file_sha(C/'SOURCE_FREEZE.json')
    assert all(file_sha(R/p)==sha for p,sha in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
    assert (Path(task['output']).resolve()).is_relative_to(R/'runs/v858_nav2_verified/v1024')and not Path(task['output']).exists()
    return min(window['absolute_deadline_unix']-30,time.time()+1200)

def main():
 task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());end=authorized(task,receipt)
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{sorted(os.sched_getaffinity(0))[0]})
 out=Path(task['output']);out.mkdir(parents=True);v=None;owner=None;evidence=None;setup=None;native_calls=0;in_native=False;initialized=False;replay_started=False;result=dict(passed=False,model_initializations=None,navigation_native=None,own_replay_native=0,private_mujoco_native=0,training_updates=0,simulation_time_only=True,real_time_qualified=False,source_searches=[])
 def abort(*_):raise InterruptedError('ABSOLUTE_ROOT_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGALRM,abort);signal.signal(signal.SIGTERM,abort);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 def progress(vehicle,owner):dump(out/'PARTIAL.json',dict(native_tick=vehicle.count,sim_time=float(vehicle.d.time),body=list(vehicle.body()),phase=owner.phase,maximum_position_m=owner.maximum_position,maximum_heading_rad=owner.maximum_heading))
 try:
    factory=load('v1024_original_exact_factory',R/'experiments/v1020_terminal_two_route_development/physical.py')
    v=factory.create_vehicle(out/'physics',task);initialized=True;result['model_initializations']=1
    assert v.count==0 and v.d.time==0.,'ACTUAL_T0_NOT_CANONICAL'
    original_native=v.native
    def counted_native(*args):
        nonlocal native_calls,in_native
        in_native=True;answer=original_native(*args);native_calls+=1;in_native=False;return answer
    v.native=counted_native
    # One controller owns every new native step. No Nav2/other callback writer.
    law=load('v1024_unchanged_qualified_allocator',R/'experiments/v993_steering_transient_diagnosis/vehicle_control.py');import mujoco as mj
    before_switch={name:np.asarray(getattr(v.d,name)).copy()for name in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    old=v.adapter;adapter=law.Adapter(v.m,mj,v.dt,encoders=old.encoders);adapter.virtual_rate=.6;adapter.last=old.last.copy();adapter.integral=float(old.integral);v.adapter=adapter
    assert all(np.array_equal(value,np.asarray(getattr(v.d,name)))for name,value in before_switch.items()),'ADAPTER_SWITCH_WROTE_PHYSICAL_STATE'
    dump(out/'CONTROL_OWNER_BINDING.json',dict(original_factory='V1020_PHYSICAL',new_actual_allocator='V993',allocator_sha256=file_sha(R/'experiments/v993_steering_transient_diagnosis/vehicle_control.py'),physical_state_unchanged=True,only_one_control_writer=True,nav2_action_or_other_controller_started=False))
    actual_setup=json.loads((out/'physics/SETUP.json').read_text());setup=public_setup(actual_setup);fixture=json.loads((C/'STATIC_INITIAL.json').read_text());p=packet(v,False)
    assert np.linalg.norm(np.asarray(p['body'][:3])-fixture['packet']['body'][:3])<=1e-8,'FRESH_T0_DIFFERS'
    # Qualification fixture uses relative t0 metadata; execution prediction is
    # regenerated from this ACTUAL fresh packet, never copied physical state.
    plan=construct(p,None,task['goal_xy'],setup,min(end-300,time.time()+40),'pre_detection_static');result['source_searches'].append(dict(stage='static_complete',status=plan['status'],passed=plan['passed'],expanded=plan.get('expanded')))
    dump(out/'STATIC_COMPLETE_PLAN.json',plan);assert plan['passed'],'NO_COMPLETE_STATIC_INPUT_ROUTE'
    audit_result=audit(plan,p,None,setup,task['goal_xy']);dump(out/'STATIC_SOURCE_AUDIT.json',audit_result);assert audit_result['passed'],'STATIC_FULL_INPUT_AUDIT'
    evidence=Evidence(setup['known'])
    def observe():return evidence.update(v.scan())
    assert not observe(),'CAUSAL_DYNAMIC_VISIBLE_AT_T0'
    owner=Owner(v,end,observe,progress);first=owner.execute(plan,interrupt_on_discovery=task['dynamic']);dump(out/'STATIC_EXECUTION.json',first)
    if task['dynamic']:
        assert first['interrupted_by_causal_discovery']and evidence.first is not None,'DYNAMIC_DISCOVERY_REQUIRED'
        # Revoke static suffix before any further positive input. Every brake/
        # information-hold block has a separate full causal 200-step permission.
        owner.authorize_brake();stops=[]
        for j in range(11):
            p=packet(v,True);permission=brake(setup,p,evidence);dump(out/('BRAKE_PERMISSION_'+str(j)+'.json'),permission);r=owner.execute(permission);stops.append(r)
            assert r['completed']and abs(np.asarray(v.body()[3:])).max()<=.03,'ACTUAL_DISCOVERY_STOP_REQUIRED'
        dump(out/'DISCOVERY_STOP_AND_OBSERVE.json',dict(first_causal_scan=evidence.first,blocks=stops,original_200_step_tail_per_block=True,source=evidence.source(v)))
        p=packet(v,True);source=evidence.source(v);plan=construct(p,source,task['goal_xy'],setup,min(end-300,time.time()+100),'post_detection_full_cycle')
        result['source_searches'].append(dict(stage='dynamic_complete',status=plan['status'],passed=plan['passed'],expanded=plan.get('expanded')));dump(out/'DYNAMIC_COMPLETE_PLAN.json',dict(packet=p,source=source,plan=plan));assert plan['passed'],'NO_COMPLETE_DYNAMIC_INPUT_ROUTE'
        proof=audit(plan,p,source,setup,task['goal_xy']);dump(out/'DYNAMIC_SOURCE_AUDIT.json',proof);assert proof['passed'],'DYNAMIC_FULL_INPUT_AUDIT'
        follow=owner.execute(plan);dump(out/'DYNAMIC_EXECUTION.json',follow);assert follow['completed'],'DYNAMIC_FULL_ROUTE_NOT_COMPLETE'
        assert np.linalg.norm(np.asarray(v.body()[:2])-evidence.first['xy'])>=1.,'NO_ACTUAL_ONE_METRE_CONTINUATION'
    else:assert first['completed'],'STATIC_ROUTE_INCOMPLETE'
    assert np.linalg.norm(np.asarray(v.body()[:2])-task['goal_xy'])<=.45 and abs(np.asarray(v.body()[3:])).max()<=.03,'ACTUAL_GOAL_AND_STOP_REQUIRED'
    result.update(passed=True,status='GOAL_AND_COMPLETE_STOP',actual_goal_distance_m=float(np.linalg.norm(np.asarray(v.body()[:2])-task['goal_xy'])))
 except BaseException as error:
    result.update(passed=False,status='FAILED',error=repr(error),traceback=traceback.format_exc())
 finally:
    result['model_initializations']=1 if initialized else None;result['navigation_native']=None if in_native or v is None else v.count;result['completed_native_lower_bound']=native_calls;result['unknown_actual_count']=in_native or v is None
    if v is not None:
        try:result['physical']=v.finish();result['evidence_saved']=True
        except BaseException as error:result.update(passed=False,evidence_saved=False,save_error=repr(error))
        if evidence is not None:dump(out/'CAUSAL_EVIDENCE.json',dict(rows=evidence.snapshots,periodic_constraints=evidence.periodic.constraints,first=evidence.first))
        if owner is not None:dump(out/'OWNER_EVENTS.json',dict(phase=owner.phase,events=owner.events,maximum_position_m=owner.maximum_position,maximum_heading_rad=owner.maximum_heading))
        if not in_native and result.get('evidence_saved')and time.time()<end-30:
            try:
                replay_started=True;proof=factory.replay(v,end,out/'physics');result['replay']=proof;result['own_replay_native']=proof['replay_native'];result['passed']=result['passed']and proof['passed']
            except BaseException as error:result.update(passed=False,own_replay_native=None,replay_error=repr(error))
    result.update(closed=True,closed_unix=time.time(),task_hard_deadline_unix=end)
    signal.setitimer(signal.ITIMER_REAL,0);dump(out/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['traceback','physical']},allow_nan=False),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
