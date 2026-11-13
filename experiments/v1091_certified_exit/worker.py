"""One saved WE rejection -> certified actual brake component, never a route."""
import sys, json, time, signal, fcntl, traceback, gzip, hashlib
from pathlib import Path
C=Path(__file__).resolve().parent; R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
RESOURCE=apply()
sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));sys.path.insert(0,str(C))
import numpy as np
from physical_ops import factory,bind,dump
from kernel import law,load
from braking_reserve import Adapter
import stop
ARCH=R/'runs/v858_nav2_verified/v1090/main_west_east'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    O=Path(sys.argv[1]);task=json.loads((O/'TASK.json').read_text());out=Path(task['output'])
    window=json.loads((O/'ROUND_WINDOW.json').read_text());approval=json.loads((O/'APPROVAL.json').read_text())
    assert approval['models_authorized'] and task['task_id'] in approval['allowed_task_ids']
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==window['boot_id']
    assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items())
    deadline=min(window['absolute_deadline_unix']-30,time.time()+900)
    assert min(deadline-time.time(),window['hard_stop_monotonic']-time.monotonic())>180
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out.mkdir(parents=True,exist_ok=False);v=None;native=None;inside=False;creating=False
    result=dict(passed=False,scope='SAVED_REJECTION_EXIT_COMPONENT_ONLY',navigation_passed=False,
                vehicle_initializations=0,historical_replay_native=0,new_actual_native=0,
                own_replay_native=0,replay_state_initializations=0,private_mujoco_native=0,
                training_updates=0,internal_factory_model_constructions='unknown',resource_policy=RESOURCE)
    def halt(*_):raise TimeoutError('NEW_COMPONENT_TASK_OR_ROOT_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt)
    signal.setitimer(signal.ITIMER_REAL,max(.001,deadline-time.time()))
    f=factory(O)
    try:
        creating=True;v=f.create_vehicle(out/'physics',task);creating=False;result['vehicle_initializations']=1
        import mujoco as mj
        contract=load('exit_route_scene_contract',R/'experiments/v1089_route_scene_contract/contract.py')
        contract.verify_live(v,task)
        setup=json.loads((out/'physics/SETUP.json').read_text());old_setup=json.loads((ARCH/'physics/SETUP.json').read_text())
        assert setup['model_sha256']==old_setup['model_sha256']
        assert np.array_equal(v.initial,np.load(ARCH/'physics/INITIAL_STATE.npz')['state'])
        bind(v,law.Adapter,mj);native=v.native
        def counted(*args):
            nonlocal inside
            assert v.count<26735 and time.time()<deadline-120,'NATIVE_OR_REPLAY_RESERVE'
            inside=True;x=native(*args);inside=False;return x
        v.native=counted
        commands=np.asarray(json.loads((ARCH/'physics/BODY_COMMANDS.json').read_text()))
        assert len(commands)==24535
        with gzip.open(ARCH/'physics/CONTACTS.json.gz','rt')as file:contacts=json.load(file)
        with gzip.open(ARCH/'physics/SENSORS.json.gz','rt')as file:sensors={s['native_tick']:s for s in json.load(file)}
        maximum=0.;range_error=0.
        def scan():
            nonlocal range_error
            s=v.scan()
            if v.count<=24535:
                range_error=max(range_error,float(np.max(abs(np.array(s['ranges'])-sensors[v.count]['ranges']))))
                assert range_error<=1e-6,'HISTORY_SENSOR_MISMATCH'
        scan()
        with np.load(ARCH/'physics/NATIVE_TRACE.npz')as trace:
            saved={key:trace[key]for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
            for i,row in enumerate(commands):
                v.step(*row[[1,2,5]])
                for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
                    value=np.asarray(getattr(v.d,key));expected=saved[key][i]
                    if value.size:maximum=max(maximum,float(abs(value-expected).max()))
                assert maximum<=1e-8,'EXACT_FAILED_PREFIX_MISMATCH'
                a=v.contacts[-1];b=contacts[i+1]
                assert len(a)==len(b)and all(list(x[:3])==list(y[:3])and abs(x[3]-y[3])<=1e-8 for x,y in zip(a,b)),'HISTORY_CONTACT_MISMATCH'
                if v.count%5==0:scan()
                if v.count%1000==0:dump(out/'PARTIAL.json',dict(phase='EXACT_HISTORY',native=v.count,maximum_state_error=maximum))
        dump(out/'HISTORICAL_REPLAY_PROOF.json',dict(passed=True,native=24535,maximum_state_ctrl_mocap_error=maximum,maximum_sensor_error=range_error,contacts_identical=True,no_external_state_restore=True))
        bind(v,Adapter,mj)
        causal=load('exit_actual_packet',R/'experiments/v1024_full_route_execution/causal.py')
        packet=causal.packet(v,True);packet['speed_episode']=False
        fixture=json.loads((R/'runs/v1090_recert_failure_diagnosis/ACTUAL_SAVED_INPUT.json').read_text())
        def vector(p):return np.r_[p['body'],p['steering']['position'],p['steering']['velocity'],p['controller_memory']['last_ctrl'],p['controller_memory']['integral'],p['sim_time']]
        assert np.max(abs(vector(packet)-vector(fixture['packet'])))<=1e-8
        stage=json.loads((ARCH/'ACTIVE_CORRIDOR_STAGES.json').read_text())[0];source=stage['source']
        dump(out/'ACTUAL_EXIT_INPUT.json',dict(packet=packet,setup=setup,source=source))
        def rejected_operation():
            proof,_,_=stop.corridor.proof(setup,packet,source,np.array(stage['requests'])[4375:])
            dump(out/'ORIGINAL_REJECTION.json',proof)
            assert proof['passed'],stop.REJECTION
        try:
            stop.after_rejection(rejected_operation,v,setup,causal.packet,source,out,lambda s:None)
            raise AssertionError('EXPECTED_REJECTION_NOT_OBSERVED')
        except stop.ControlledStop as completed:
            result.update(passed=completed.record['completed'],exit=completed.record)
    except BaseException as e:
        result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
    finally:
        if creating:result['vehicle_initializations']=None
        if v is not None:
            result['historical_replay_native']=None if inside else min(v.count,24535)
            result['new_actual_native']=None if inside else max(0,v.count-24535)
            try:result['physical']=v.finish();result['evidence_saved']=True
            except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
            if not inside and result.get('evidence_saved') and v.count and time.time()<deadline-15:
                try:
                    v.native=native;result['own_replay_native']=None;result['replay_state_initializations']=None
                    replay=f.replay(v,deadline,out/'physics');result.update(replay=replay,own_replay_native=replay['replay_native'],replay_state_initializations=1)
                    result['passed']=result['passed']and replay['passed']
                except BaseException as e:result.update(passed=False,replay_error=repr(e))
        import live_reference
        result['analytical_prediction_native']=live_reference.PREDICTION_NATIVE
        signal.setitimer(signal.ITIMER_REAL,0);result['closed']=True;dump(out/'RESULT.json',result)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
