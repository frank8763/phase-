"""One physical owner, frozen measured RP-CCR capture component, not RPP comparison."""
import argparse
import copy
import fcntl
import importlib.abc
import math
import os
import signal
import sys
import traceback
import socket
import subprocess
from component_context import *
from geometry_contract import errors
from geometry_contract import Geometry,membership
from reserve import certify
from frames import SampleCache,wire_packet,CORE
from gear_handoff import GearHandoff
from stamped_contract import before_step
sys.path.insert(0,str(R/'experiments/v1372_coherent_sampling_fault'))
from native_component import binding,load
sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
from recovery_guard import check as static_guard
from dynamic_reserve import check as dynamic_guard
# Resolve by private exact path, independent of generic sys.modules caches.
import importlib.util as _iu
_prefix_spec=_iu.spec_from_file_location('phase_v1394_exact_prefix',C/'prefix_restore.py')
_prefix_module=_iu.module_from_spec(_prefix_spec);_prefix_spec.loader.exec_module(_prefix_module)
restore=_prefix_module.restore

def assert_production_bindings():
    expected={'restore':('prefix_restore.py',restore),'Geometry':('geometry_contract.py',Geometry.actual),'membership':('geometry_contract.py',membership),'certify':('reserve.py',certify),'SampleCache':('frames.py',SampleCache.__init__),'wire_packet':('frames.py',wire_packet),'GearHandoff':('gear_handoff.py',GearHandoff.select),'before_step':('stamped_contract.py',before_step)}
    for name,(path,function) in expected.items():assert Path(function.__code__.co_filename).resolve()==C/path,'PRODUCTION_SOURCE_BINDING_'+name
    return {name:str(Path(function.__code__.co_filename).resolve().relative_to(R)) for name,(_,function) in expected.items()}


def run(task,window):
    assert_production_bindings();old,Adapter,factory,replay=binding();assert Path(Adapter.compute.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py';factory.O=O;np=old.np;out=Path(task['output']);started=time.monotonic()
    contract=load('phase_capture_original_interface',R/'experiments/v1288_baseline_interface/contract.py')
    end=min(time.time()+900,window['absolute_deadline_unix']-10);v=None;journal=[];commands=[];observations=[];in_step=False;creating=False;finishing=False;delivery=None;parked_target=None;controller=None;peer_job=None;peer_log=None;rpc_socket=None;rpc_sequence=0;previous_ref=0;reserve_rows=[];reserve_states=[];reserve_ctrl=[]
    result=dict(passed=False,canonical_vehicle_initializations=0,internal_factory_model_constructions=None,private_mujoco_native=0,own_replay_native=0,training_updates=0,analytical_native=0,original_goal_navigation=False,producer_python=sys.version,producer_numpy=np.__version__,scope='same9390 complete forward next-segment originalRPP, no whole route')
    def stop(*_):raise TimeoutError('CAPTURE_ROOT_STOP')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,lambda *_:None if finishing else stop());signal.alarm(max(1,int(end-time.time())))
    try:
        import mujoco as mj
        creating=True;dump(out/'INITIALIZATION_ATTEMPT.json',dict(unix=time.time(),native=0))
        v=factory.create_vehicle(out/'physics',task);creating=False;result['canonical_vehicle_initializations']=1;old.pin()
        assert v.count==0 and v.d.time==0.;before={k:np.array(getattr(v.d,k)).copy() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
        previous=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral
        assert all(np.array_equal(before[k],getattr(v.d,k)) for k in before),'ADAPTER_REBIND_STATE_CHANGE'
        dump(out/'INITIAL_PACKET.json',old.packet(v));original=v.step;gate=GearHandoff();sampler=SampleCache();setup=read(out/'physics/SETUP.json');known=setup['known'];geometry=Geometry(known,task['causal_all_future_ball']);reference=np.load(R/task['response_reference_file'])['states']
        def step(vr,wr,phase):
            nonlocal in_step,gate,previous_ref
            assert time.time()<end-60 and remaining(window)>70 and v.count<task['origin_native_tick']+task['component_native_limit']+200,'COMPLETE_TAIL_REPLAY_RESERVE'
            raw=[vr,wr,False];expiry=None
            if phase!='HISTORICAL_PREFIX':
                if phase in ['COMPLETE_STOP_TAIL','ERROR_STOP_TAIL']:assert vr==wr==0.
                else:
                    vr,wr,expiry=before_step(vr,wr,delivery,time.monotonic());assert expiry['fresh'],'TIMED_SOURCE_EXPIRED'
            body=list(v.body());enc=v.steering_sample().copy();upstream=[vr,wr,False]
            candidate_gate=copy.deepcopy(gate);vr,wr,proof=candidate_gate.select(vr,wr,native_tick=v.count,body=body,last_ctrl=v.adapter.last,encoders=enc)
            if phase!='HISTORICAL_PREFIX':
                proof_reserve,states_reserve,ctrl_reserve=certify(v,setup,geometry,old.packet,Adapter,result,end)
                reserve_rows.append(proof_reserve);reserve_states.append(states_reserve);reserve_ctrl.append(ctrl_reserve)
                assert proof_reserve['passed'],'CURRENT_MEASURED_STATE_COMPLETE_BRAKING_RESERVE_REJECTED'
                if expiry is not None:
                    assert before_step(*raw[:2],delivery,time.monotonic())[2]['fresh'],'COMMAND_EXPIRED_DURING_CERTIFICATE'
                assert proof['prior_gear'] in (0,1),'UNEXPECTED_FORWARD_GEAR_MEMORY'
            row=dict(before_native=v.count,body=body,encoders=enc,last_ctrl=v.adapter.last.copy(),integral=v.adapter.integral,
                phase=phase,request=[vr,wr,False],upstream_request=upstream,raw_upstream_request=raw,gear_handoff=proof,applied=False,
                expiry_gate=expiry,delivery=delivery if expiry is not None else None,command_sequence=None if delivery is None else delivery['command_sequence'],
                parked_target=getattr(v.adapter,'parked_target',None) if phase=='HISTORICAL_PREFIX' else None,steering_motion_active_before=bool(getattr(v.adapter,'_steering_motion_active',False)))
            journal.append(row);v.adapter.parked_target=row['parked_target'];gate=candidate_gate;in_step=True;original(vr,wr,False);in_step=False;row['applied']=True;old.previous.body_gate(old.packet(v))
            if phase!='HISTORICAL_PREFIX':
                lower=geometry.actual(list(v.body()),v.count);row['post_step_causal_bound']=dict(lower_m=lower)
                assert lower>=.22-1e-8,'ACTUAL_CAUSAL22_VIOLATION'
                if phase!='ERROR_STOP_TAIL':
                    row['response_membership']=membership(list(v.body()),v.count,reference,previous_ref);previous_ref=row['response_membership']['reference_index']
            if v.count%500==0:dump(out/'PARTIAL.json',dict(native=v.count,phase=phase,body=list(v.body())))
        prefix=restore(v,task,step,end);dump(out/'PREFIX_RESTORE.json',prefix);dump(out/'COMPONENT_INITIAL_PACKET.json',old.packet(v))
        failed=None;sequence=0;setup=read(out/'physics/SETUP.json');known=setup['known'];geometry=Geometry(known,task['causal_all_future_ball']);reference=np.load(R/task['response_reference_file'])['states']
        from peer_environment import environment
        ros,peer_env=environment(out);peer_log=(out/'rpp_peer.console').open('x')
        peer_job=subprocess.Popen(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'rpp_peer.py'),str(out),task['run_id']]),cwd=R,env=peer_env,stdout=peer_log,stderr=subprocess.STDOUT,start_new_session=True)
        dump(out/'OWN_RPP_PEER.json',dict(pid=peer_job.pid,physical_models=0))
        rpc_socket=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);rpc_address=str((out/'native_rpc.sock').relative_to(R));rpc_socket.bind(rpc_address);rpc_socket.settimeout(.01);target=str((out/'peer.sock').relative_to(R));until=time.monotonic()+10
        while not (out/'peer.sock').exists():
            assert peer_job.poll() is None and time.monotonic()<until,'RPP_PEER_ENTRY';time.sleep(.02)
        sent={}
        def request_command():
            nonlocal rpc_sequence
            until=time.monotonic()+(55 if not commands else 3);next_send=0.
            while time.monotonic()<until:
                assert peer_job.poll() is None,'RPP_PEER_EXIT'
                if time.monotonic()>=next_send:
                    wire=wire_packet(sampler,v,task['run_id'],rpc_sequence);contract.observation({k:wire[k] for k in CORE},run_id=task['run_id'],now=time.monotonic(),previous_sequence=rpc_sequence-1)
                    observations.append(wire);sent[rpc_sequence]=wire
                    rpc_socket.sendto(json.dumps(dict(kind='ACTUAL_FRAME',run_id=task['run_id'],sequence=rpc_sequence,native_tick=v.count,body=wire['body'],wire=wire),allow_nan=False).encode(),target);rpc_sequence+=1;next_send=time.monotonic()+.05
                try:reply=json.loads(rpc_socket.recv(65536))
                except socket.timeout:continue
                assert reply['run_id']==task['run_id'] and reply['sequence'] in sent,'UNBOUND_RPP_REPLY'
                source=sent[reply['sequence']];assert source['native_tick']==v.count,'RPP_REPLY_WRONG_ACTUAL_STATE'
                assert 0<=time.monotonic()-source['sampled_at']<=.2,'RPP_REPLY_OBSERVATION_EXPIRED'
                if reply['kind']=='RPP_ACTION_DONE':return reply,source
                assert reply['kind']=='ORIGINAL_RPP_ACTUAL_COMMAND' and reply['actual_frame_bound']
                assert reply['body']==source['body'] and reply['observation_sequence']==source['sequence'] and reply['observation_sampled_at']==source['sampled_at'] and reply['observation_native_tick']==source['native_tick'],'RPP_SOURCE_BINDING'
                assert 0<=time.monotonic()-reply['origin']['generated_monotonic']<=.2,'RPP_GENERATION_EXPIRED'
                return reply,source
            raise TimeoutError('ACTUAL_RPP_COMMAND_TIMEOUT')
        complete=False
        while v.count-task['origin_native_tick']<task['component_native_limit']-200:
            reply,wire=request_command()
            if reply['kind']=='RPP_ACTION_DONE':
                if reply['status']!=4 or reply['error_code']!=0:failed='ORIGINAL_RPP_ACTION_REFUSAL'
                else:complete=True
                dump(out/'ORIGINAL_RPP_ACTION_RESULT.json',reply);break
            vr,wr=reply['v'],reply['w'];contract.twist(vr,wr);assert abs(vr)<.005 or vr>0.,'RPP_FORWARD_DIRECTION'
            now=time.monotonic();delivery=dict(origin=reply['origin'],validated_monotonic=now,observation_sequence=wire['sequence'],observation_native_tick=wire['native_tick'],observation_sampled_at=wire['sampled_at'],command_sequence=sequence)
            commands.append(dict(packet=dict(run_id=task['run_id'],sequence=sequence,issued_at=reply['origin']['generated_monotonic'],v=vr,w=wr),before_native=v.count,delivery=delivery,rpp_reply=reply,applied_native=0));sequence+=1
            for _ in range(5):step(vr,wr,'ORIGINAL_RPP_FORWARD');commands[-1]['applied_native']+=1
        else:failed='COMPONENT_NATIVE_LIMIT'
        for _ in range(200):
            step(0.,0.,'COMPLETE_STOP_TAIL')
            if v.count%5==0:v.scan()
        final=old.packet(v);dump(out/'FINAL_PACKET.json',final);position,heading=errors(final['body'],task['target_segment'])
        def virtual(front):
            a,b=map(math.tan,front);return math.atan(.6*(a/(.6+.27*a)+b/(.6-.27*b))/2)
        initial_component=read(out/'COMPONENT_INITIAL_PACKET.json')
        front_change=abs(virtual(final['steering']['position'])-virtual(initial_component['steering']['position']))
        checks=dict(full_original_RPP_action_complete=complete,no_reserve_refusal=failed is None,
            original_position_bound=position<=.12,original_heading_bound=heading<=.20,body_stopped=max(abs(x) for x in final['body'][3:])<=.003,
            steering_rest=max(abs(x) for x in final['steering']['velocity'])<=.03,drive_zero=max(abs(x) for x in final['controller_memory']['last_ctrl'][2:])<=1e-10,
            full200_applied_stop=len(journal)>=200 and all(r['applied'] and r['request']==[0.,0.,False] and r['phase']=='COMPLETE_STOP_TAIL' for r in journal[-200:]))
        result.update(passed=all(checks.values()),functional_checks=checks,functional_stop=failed,position_error_m=position,heading_error_rad=heading,measured_virtual_front_angle_change_rad=front_change)
    except BaseException as exc:
        result.update(passed=False,error=repr(exc),traceback=traceback.format_exc())
        if v is not None and not in_step and remaining(window)>100:
            try:
                for _ in range(200):step(0.,0.,'ERROR_STOP_TAIL')
                dump(out/'FINAL_PACKET.json',old.packet(v));result['error_stop_tail_completed']=True
            except BaseException as error:result['error_stop_tail_error']=repr(error)
    finally:
        finishing=True
        if rpc_socket is not None:
            try:rpc_socket.sendto(json.dumps(dict(kind='STOP',run_id=task['run_id'])).encode(),target)
            except OSError:pass
        if peer_job is not None:
            try:peer_job.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(peer_job.pid,signal.SIGTERM)
                try:peer_job.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(peer_job.pid,signal.SIGKILL);peer_job.wait(timeout=3)
        if peer_log is not None:peer_log.close()
        if rpc_socket is not None:rpc_socket.close();(out/'native_rpc.sock').unlink(missing_ok=True)
        dump(out/'APPLIED_JOURNAL.json',journal);dump(out/'CAPTURE_COMMANDS.json',commands);dump(out/'OBSERVATIONS_SENT.json',observations);dump(out/'BRAKING_PROOFS.json',reserve_rows)
        if reserve_states:np.savez_compressed(out/'BRAKING_ALTERNATIVES.npz',states=np.asarray(reserve_states),ctrl=np.asarray(reserve_ctrl))
        result['canonical_vehicle_initializations']=None if creating else result['canonical_vehicle_initializations']
        result['actual_total_native']=None if in_step else v.count if v is not None else 0
        result['historical_prefix_replay_native']=None if in_step and v is not None and v.count<10775 else min(10775,v.count) if v is not None else 0
        result['new_component_native']=None if in_step else max(0,v.count-10775) if v is not None else 0
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
    assert_production_bindings();p=argparse.ArgumentParser();p.add_argument('task');p.add_argument('--entry-check',action='store_true');a=p.parse_args();task=read(a.task);task_check(task)
    if a.entry_check:
        class NoModel(importlib.abc.MetaPathFinder):
            def find_spec(self,name,*args):
                if name.split('.')[0] in {'mujoco','vehicle','torch'}:raise AssertionError('ENTRY_PHYSICAL_IMPORT '+name)
        sys.meta_path.insert(0,NoModel());binding();print(json.dumps(dict(passed=True,production_callable_sources=assert_production_bindings(),models=0,physical_native=0)));return 0
    window=read(O/'ROUND_WINDOW.json');authorize(task,window);assert not (R/'REVIEW_PENDING').exists()
    with (R/'runs/v648_static_unknown/execution.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=run(task,window)
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
