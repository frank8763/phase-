"""One physical owner, disabled by default; entry-check cannot import models."""
import argparse
import fcntl
import importlib.abc
import json
from pathlib import Path
import signal
import sys
import time
import traceback


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ENTRY_CHECK_ZERO_MODELS '+name)


if '--entry-check'in sys.argv:sys.meta_path.insert(0,NoModels())
from worker_context import *


def physical_run(task,window,lock):
    old=science();q=old.q;np=q.np;previous=old.previous;packet=old.packet;pin=old.pin
    out=Path(task['output']);out.mkdir(parents=True)
    start=time.monotonic();end=time.time()+min(1500,remaining(window)-30)
    nav_end=min(end,time.time()+1200)
    def halt(*_):raise TimeoutError('ABSOLUTE_PHYSICAL_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.01,end-time.time()))
    v=None;creating=False;inside=False;kind='actual';actual=0;replayed=0;error=None;journal=[];physical=None
    result=dict(passed=False,models=0,internal_factory_model_constructions='unknown',historical_reconstruction_native=0,historical_controls_used=0,private_mujoco_native=0,training_updates=0,formal_retained_commit=False,final_stop_executed=False,universal_error_support_verified=False)
    try:
        owner=configure_owner(O,nav_end,window);old.history_guard(out)
        sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'));from bindings import Adapter
        physical=factory();scene=load('v1204_scene_contract',R/'experiments/v1089_route_scene_contract/contract.py')
        creating=True;dump(out/'INITIALIZATION_ATTEMPT.json',dict(started_unix=time.time(),steps_before=0));v=physical.create(out/'physics',task);creating=False;result['models']=1;pin()
        import mujoco as mj
        from cpu_backend import require_cpu_backend
        setup=read(out/'physics/SETUP.json');meta=read(R/('runs/v1122_cache_entry_relay/'+task['case_id']+'_T0_METADATA.json'))
        assert v.count==0 and v.d.time==0. and v.actor is not None
        load('v1204_initial_setup',R/'experiments/v1067_causal_replan_brake_reserve/initial_contract.py').check_setup(setup,meta)
        result['scene_contract']=scene.verify_live(v,task);assert sha(out/'physics/scene_model.mjb')==setup['model_sha256']
        b=np.asarray(v.body());assert abs(b[:2]-task['start_xy']).max()<=1e-8 and abs(math.atan2(math.sin(b[2]-task['start_yaw']),math.cos(b[2]-task['start_yaw'])))<=1e-8
        before={k:np.array(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
        adapter=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=adapter.encoders);v.adapter.virtual_rate=.6;v.adapter.last=adapter.last.copy();v.adapter.integral=adapter.integral
        assert all(np.array_equal(a,np.asarray(getattr(v.d,k)))for k,a in before.items())
        dump(out/'CANONICAL_INITIAL_PACKET.json',packet(v));result['resource_policy']=dict(old.RESOURCE,renderer=require_cpu_backend());native=v.native
        def counted(*args):
            nonlocal inside,actual,replayed
            assert time.time()<end-2 and remaining(window)>10,'NATIVE_DEADLINE'
            inside=True;value=native(*args);inside=False
            if kind=='actual':actual+=1
            else:replayed+=1
            return value
        v.native=counted;step=v.step
        def applied(vr,wr,stale=False):
            assert v.count<task['native_limit'] and time.time()<nav_end,'NAVIGATION_BUDGET'
            row=dict(before_native=v.count,phase=getattr(v,'_chain_phase','fresh_normal'),parked_target=getattr(v.adapter,'parked_target',None),request=[float(vr),float(wr),bool(stale)],last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral),applied=False);journal.append(row)
            before=v.count;step(float(vr),float(wr),bool(stale));row['applied']=True
            assert v.count==before+1;previous.body_gate(packet(v))
        v.step=applied;v._chain_phase='fresh_normal'
        owner.navigate(v,setup,task,nav_end,out,result)
        result.update(models=1,full_fresh_t0_navigation=True,final_stop_executed=True)
        dump(out/'ACTUAL_FINAL_PACKET.json',packet(v))
    except BaseException as exc:
        detail=dict(error=repr(exc),traceback=traceback.format_exc())
        if isinstance(exc,AssertionError) and str(exc)in{'OBSERVER_LIBRARY_CLOCK_DOMAIN','OBSERVER_LIBRARY_SOURCE_DOMAIN'} and v is not None and previous.stopped(packet(v)) and not inside:
            result['functional_failure']=dict(reason=str(exc),safe_stopped_domain_refusal=True,detail=detail)
            dump(out/'FUNCTIONAL_REFUSAL.json',result['functional_failure'])
        else:
            error=detail;dump(out/'ERROR.json',error)
        result['passed']=False
        if v is not None and not inside:dump(out/'ACTUAL_FINAL_PACKET.json',packet(v))
    finally:
        result.pop('_evidence',None);dump(out/'DIRECT_SEGMENTS.json',result.pop('_direct_segments',[]))
        result.update(error=error,models=None if creating else result['models'],new_actual_native=None if inside and kind=='actual'else actual,total_actual_model_native=None if inside and kind=='actual'else actual,own_replay_native=0,analytical_python_native=None,analytical_cpp_native=None,analytical_total_scope='normal preview total unknown; completed recovery recorded separately',model_native_inflight_unknown=inside)
        if v is not None:
            dump(out/'APPLIED_JOURNAL.json',journal)
            result['known_recovery_counts']=dict(getattr(v,'_chain_counts',{}),observer_cpp_native=getattr(getattr(v,'_chain_engine',None),'native',None),observer_cpp_inflight=bool(getattr(getattr(v,'_chain_engine',None),'in_call',False)))
            try:result['physical']=v.finish();result['evidence_saved']=True
            except BaseException as exc:result.update(passed=False,evidence_saved=False,save_error=repr(exc))
            result['fully_recorded_native']=len(v.rows)
            if error is None and result.get('evidence_saved')and v.count==len(v.rows)and not inside and time.time()<end-60 and remaining(window)>90:
                try:
                    kind='replay';result['replay_state_initializations']=1;result['replay']=physical.replay(v,end,out/'physics');result['own_replay_native']=replayed;result['passed']=bool(result['passed']and result['replay']['passed'])
                except BaseException as exc:result.update(passed=False,replay_error=repr(exc),own_replay_native=None if inside else replayed)
        signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-start,closed_unix=time.time());dump(out/'RESULT.json',result)
    return 0 if result['passed']else 1


def main():
    parser=argparse.ArgumentParser();parser.add_argument('task');parser.add_argument('--entry-check',action='store_true');parser.add_argument('--approval');parser.add_argument('--window');args=parser.parse_args()
    entered_physical=False
    try:
        assert args.entry_check or not args.approval and not args.window,'PHYSICAL_CONTEXT_OVERRIDE_FORBIDDEN'
        task=read(args.task);approval=read(args.approval or O/'APPROVAL.json')
        assert approval.get('models_authorized')is True,'NO_NEW_MODEL_AUTHORITY'
        window=read(args.window or O/'ROUND_WINDOW.json');envelope(task,approval,window,entry_check=args.entry_check)
        lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise AssertionError('EXECUTION_LOCK_BUSY')
        try:
            if args.entry_check:
                print(json.dumps(dict(passed=True,entry_check=True,models=0,new_mujoco_native=0,lock_acquired=True,physical_started=False)));return 0
            entered_physical=True
            return physical_run(task,window,lock)
        finally:fcntl.flock(lock,fcntl.LOCK_UN)
    except BaseException as exc:
        print(json.dumps(dict(passed=False,entry_rejected=not entered_physical,reason=str(exc),models=None if entered_physical else 0,new_mujoco_native=None if entered_physical else 0,physical_started=entered_physical)));return 2


if __name__=='__main__':sys.exit(main())
