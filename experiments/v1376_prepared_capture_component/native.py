"""One physical owner, frozen measured RP-CCR capture component, not RPP comparison."""
import argparse
import fcntl
import importlib.abc
import os
import signal
import sys
import traceback
from component_context import *
from controller import Capture,errors
from frames import SampleCache,wire_packet,CORE
from gear_handoff import GearHandoff
from stamped_contract import before_step
sys.path.insert(0,str(R/'experiments/v1372_coherent_sampling_fault'))
from native_component import binding,load
sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
from recovery_guard import check as static_guard
from dynamic_reserve import check as dynamic_guard
from prefix_restore import restore

def run(task,window):
    old,Adapter,factory,replay=binding();factory.O=O;np=old.np;out=Path(task['output']);started=time.monotonic()
    contract=load('phase_capture_original_interface',R/'experiments/v1288_baseline_interface/contract.py')
    end=min(time.time()+900,window['absolute_deadline_unix']-10);v=None;journal=[];commands=[];observations=[];in_step=False;creating=False;finishing=False;delivery=None;parked_target=None
    result=dict(passed=False,canonical_vehicle_initializations=0,internal_factory_model_constructions=None,private_mujoco_native=0,own_replay_native=0,training_updates=0,original_goal_navigation=False,producer_python=sys.version,producer_numpy=np.__version__,scope='measured RPCCR two-arc pose capture only; no Nav2 performance claim')
    def stop(*_):raise TimeoutError('CAPTURE_ROOT_STOP')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,lambda *_:None if finishing else stop());signal.alarm(max(1,int(end-time.time())))
    try:
        import mujoco as mj
        creating=True;dump(out/'INITIALIZATION_ATTEMPT.json',dict(unix=time.time(),native=0))
        v=factory.create_vehicle(out/'physics',task);creating=False;result['canonical_vehicle_initializations']=1;old.pin()
        assert v.count==0 and v.d.time==0.;before={k:np.array(getattr(v.d,k)).copy() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
        previous=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral
        assert all(np.array_equal(before[k],getattr(v.d,k)) for k in before),'ADAPTER_REBIND_STATE_CHANGE'
        dump(out/'INITIAL_PACKET.json',old.packet(v));original=v.step;gate=GearHandoff();sampler=SampleCache()
        def step(vr,wr,phase):
            nonlocal in_step
            assert time.time()<end-60 and remaining(window)>70 and v.count<task['origin_native_tick']+task['component_native_limit']+200,'COMPLETE_TAIL_REPLAY_RESERVE'
            raw=[vr,wr,False];expiry=None
            if phase!='HISTORICAL_PREFIX':
                if phase=='COMPLETE_STOP_TAIL':assert vr==wr==0.
                else:vr,wr,expiry=before_step(vr,wr,delivery,time.monotonic())
            body=list(v.body());enc=v.steering_sample().copy();upstream=[vr,wr,False]
            vr,wr,proof=gate.select(vr,wr,native_tick=v.count,body=body,last_ctrl=v.adapter.last,encoders=enc)
            row=dict(before_native=v.count,body=body,encoders=enc,last_ctrl=v.adapter.last.copy(),integral=v.adapter.integral,
                phase=phase,request=[vr,wr,False],upstream_request=upstream,raw_upstream_request=raw,gear_handoff=proof,applied=False,
                expiry_gate=expiry,delivery=delivery if expiry is not None else None,command_sequence=None if delivery is None else delivery['command_sequence'],
                parked_target=parked_target if phase=='PREPARE_FORWARD' and (expiry is None or expiry['fresh']) else None,steering_motion_active_before=bool(getattr(v.adapter,'_steering_motion_active',False)))
            journal.append(row);v.adapter.parked_target=row['parked_target'];in_step=True;original(vr,wr,False);in_step=False;row['applied']=True;old.previous.body_gate(old.packet(v))
            if v.count%500==0:dump(out/'PARTIAL.json',dict(native=v.count,phase=phase,body=list(v.body())))
        prefix=restore(v,task,step,end);dump(out/'PREFIX_RESTORE.json',prefix);dump(out/'COMPONENT_INITIAL_PACKET.json',old.packet(v))
        controller=Capture(task);failed=None;sequence=0;known=read(out/'physics/SETUP.json')['known']
        while v.count-task['origin_native_tick']<task['component_native_limit']:
            wire=wire_packet(sampler,v,task['run_id'],sequence);contract.observation({k:wire[k] for k in CORE},run_id=task['run_id'],now=time.monotonic(),previous_sequence=sequence-1);observations.append(wire)
            vr,wr,state=controller.select(wire['body'],v.count,v.steering_sample().tolist(),v.adapter.last.tolist());parked_target=state['parked_target']
            if state['phase']=='CAPTURE_COMPLETE':break
            dynamic,dp=dynamic_guard(wire['body'],task['causal_all_future_ball'],vr,wr);static,sp=static_guard(known,wire['body'],vr,wr)
            now=time.monotonic();core=dict(run_id=task['run_id'],sequence=sequence,issued_at=now,v=vr,w=wr)
            contract.command(core,run_id=task['run_id'],now=now,previous_sequence=sequence-1)
            delivery=dict(origin=dict(kind='RPCCR_CAPTURE_NATIVE',generated_monotonic=now),validated_monotonic=now,
                observation_sequence=wire['sequence'],observation_native_tick=wire['native_tick'],observation_sampled_at=wire['sampled_at'],command_sequence=sequence)
            commands.append(dict(packet=core,before_native=v.count,delivery=delivery,controller_state=state,dynamic_allowed=dynamic,dynamic_proof=dp,static_allowed=static,static_proof=sp,applied_native=0));sequence+=1
            if not dynamic or not static:failed='ORIGINAL_DYNAMIC_OR_STATIC_RESERVE_REFUSAL';break
            for _ in range(5):step(vr,wr,state['phase']);commands[-1]['applied_native']+=1
        else:failed='COMPONENT_NATIVE_LIMIT'
        for _ in range(200):
            step(0.,0.,'COMPLETE_STOP_TAIL')
            if v.count%5==0:v.scan()
        final=old.packet(v);dump(out/'FINAL_PACKET.json',final);position,heading=errors(final['body'],task['target_segment'])
        checks=dict(capture_complete=controller.phase=='CAPTURE_COMPLETE',no_reserve_refusal=failed is None,
            original_position_bound=position<=.12,original_heading_bound=heading<=.20,body_stopped=max(abs(x) for x in final['body'][3:])<=.003,
            steering_rest=max(abs(x) for x in final['steering']['velocity'])<=.03,drive_zero=max(abs(x) for x in final['controller_memory']['last_ctrl'][2:])<=1e-10)
        result.update(passed=all(checks.values()),functional_checks=checks,functional_stop=failed,position_error_m=position,heading_error_rad=heading)
    except BaseException as exc:
        result.update(passed=False,error=repr(exc),traceback=traceback.format_exc())
        if v is not None and not in_step and remaining(window)>100:
            try:
                for _ in range(200):step(0.,0.,'COMPLETE_STOP_TAIL')
                dump(out/'FINAL_PACKET.json',old.packet(v));result['error_stop_tail_completed']=True
            except BaseException as error:result['error_stop_tail_error']=repr(error)
    finally:
        finishing=True;dump(out/'APPLIED_JOURNAL.json',journal);dump(out/'CAPTURE_COMMANDS.json',commands);dump(out/'OBSERVATIONS_SENT.json',observations)
        result['canonical_vehicle_initializations']=None if creating else result['canonical_vehicle_initializations']
        result['actual_total_native']=None if in_step else v.count if v is not None else 0
        result['historical_prefix_replay_native']=None if in_step and v is not None and v.count<9390 else min(9390,v.count) if v is not None else 0
        result['new_component_native']=None if in_step else max(0,v.count-9390) if v is not None else 0
        result['model_native_inflight_unknown']=in_step
        dump(out/'RESULT_PROGRESS.json',dict(result,phase='BEFORE_FULL_EVIDENCE_SAVE'))
        if v is not None:
            try:result['physical']=v.finish();result['evidence_saved']=True
            except BaseException as exc:result.update(passed=False,save_error=repr(exc))
            if not in_step and result.get('evidence_saved'):
                try:
                    initial=read(out/'INITIAL_PACKET.json');cursor=[None];owner=Adapter(v.m,mj,v.dt,encoders=lambda:np.asarray(cursor[0]['encoders']))
                    owner.virtual_rate=.6;owner.last=np.asarray(initial['controller_memory']['last_ctrl']);owner.integral=initial['controller_memory']['integral'];maximum=memory=0.
                    for i,row in enumerate(journal):
                        cursor[0]=row;assert row['applied'] and row['before_native']==i
                        memory=max(memory,float(abs(owner.last-row['last_ctrl']).max()),abs(owner.integral-row['integral']))
                        assert bool(getattr(owner,'_steering_motion_active',False))==row['steering_motion_active_before']
                        owner.parked_target=row['parked_target'];u=owner.compute(*row['request'][:2],*row['body'][3:],False);maximum=max(maximum,float(abs(u-v.rows[i]['ctrl'][v.adapter.commands.ids]).max()))
                    result['independent_allocation']=dict(passed=max(memory,maximum)<=1e-8,control_error=maximum,memory_error=memory)
                    result['passed']=result['passed'] and result['independent_allocation']['passed']
                except BaseException as exc:result.update(passed=False,allocation_error=repr(exc))
                try:
                    dump(out/'REPLAY_ATTEMPT.json',dict(maximum_native=len(v.rows)));result['own_replay_native']=None
                    proof=replay(v,end,out/'physics');result.update(replay=proof,own_replay_native=proof['replay_native'],passed=result['passed'] and proof['passed'])
                except BaseException as exc:result.update(passed=False,replay_error=repr(exc))
        signal.alarm(0);result.update(closed=True,wall_s=time.monotonic()-started,source_unchanged=sources());dump(out/'RESULT.json',result)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('task');p.add_argument('--entry-check',action='store_true');a=p.parse_args();task=read(a.task);task_check(task)
    if a.entry_check:
        class NoModel(importlib.abc.MetaPathFinder):
            def find_spec(self,name,*args):
                if name.split('.')[0] in {'mujoco','vehicle','torch'}:raise AssertionError('ENTRY_PHYSICAL_IMPORT '+name)
        sys.meta_path.insert(0,NoModel());binding();print(json.dumps(dict(passed=True,models=0,physical_native=0)));return 0
    window=read(O/'ROUND_WINDOW.json');authorize(task,window);assert not (R/'REVIEW_PENDING').exists()
    with (R/'runs/v648_static_unknown/execution.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=run(task,window)
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
