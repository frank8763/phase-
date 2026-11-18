"""Future authorized physical worker. Import and qualification initialize no model."""
from response_tools import *
import fcntl
import signal
import traceback
import numpy as np
from response_execution import run_component,measured,StopCertifier,Adapter


def main():
    task=read(Path(sys.argv[1]))
    assert read(O/'APPROVAL.json')['models_authorized'] is True,'NO_NEW_MODEL_AUTHORITY'
    window=read(O/'ROUND_WINDOW.json');assert window['version']=='V1157' and remaining(window)>960,'ROOT_RESERVE'
    assert task in read(C/'TASKS.json') and source_ok(),'TASK_OR_SOURCE'
    out=Path(task['output']);assert out.is_relative_to(R/'runs/v858_nav2_verified/v1157') and not out.exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out.mkdir(parents=True)
    started=time.monotonic();end=min(time.time()+900,time.time()+remaining(window)-20)
    def halt(*_):raise TimeoutError('RESPONSE_COMPONENT_ABSOLUTE_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
    vehicle=None;factory=None;certifier=None;creating=False;inside_native=False;kind='actual'
    actual_completed=0;replayed=0;error=None;result=dict(passed=False,models=0,
        new_actual_native=0,own_replay_native=0,replay_state_initializations=0,
        private_mujoco_native=0,training_updates=0,original_goal_passed=False,
        whole_route_passed=False,three_routes=False,new24=False)
    try:
        # Original CPU/static factory is only loaded after all authority checks.
        factory=load('v1157_original_cpu_factory',R/'experiments/v1114_coupled_steering_mode/physical.py')
        contract=load('v1157_static_fixture_contract',R/'experiments/v1114_coupled_steering_mode/fixture_contract.py')
        fixture=read(R/'experiments/v1139_afternoon_observer/STATIC_T0_SOURCE_FIXTURE.json')
        contract.validate_task(task,fixture)
        creating=True;dump(out/'INITIALIZATION_ATTEMPT.json',dict(started_unix=time.time(),integrations_before=0))
        vehicle=factory.create(out/'physics',task);creating=False;result['models']=1;pin()
        assert vehicle.count==0 and vehicle.d.time==0. and vehicle.actor is None
        import mujoco as mj
        from cpu_backend import require_cpu_backend
        result['resource_policy']=dict(RESOURCE,renderer=require_cpu_backend())
        setup=read(out/'physics/SETUP.json')
        contract.validate_actual(task,fixture,setup,sha(out/'physics/scene_model.mjb'))
        old=vehicle.adapter
        before={k:np.asarray(getattr(vehicle.d,k)).copy() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
        vehicle.adapter=Adapter(vehicle.m,mj,vehicle.dt,encoders=old.encoders)
        vehicle.adapter.virtual_rate=.6;vehicle.adapter.last=old.last.copy();vehicle.adapter.integral=float(old.integral)
        assert all(np.array_equal(v,np.asarray(getattr(vehicle.d,k)))for k,v in before.items()),'BINDING_STATE_WRITE'
        vehicle._v1157_setup=setup
        initial_packet=measured(vehicle);dump(out/'ACTUAL_INITIAL_PACKET.json',initial_packet)
        from source import initial
        assert np.max(abs(np.asarray(initial(initial_packet)['state'])-np.asarray(initial(fixture['packet'])['state'])))<=1e-8,'CANONICAL_INITIAL_STATE'
        certifier=StopCertifier(setup)
        with np.load(R/'runs/v1156_response_input_preparation/PLAN.npz') as z:plan={k:z[k].copy()for k in z.files}
        native=vehicle.native
        def counted(*args):
            nonlocal inside_native,actual_completed,replayed
            assert time.time()<end-2 and remaining(window)>5,'NATIVE_ABSOLUTE_DEADLINE'
            inside_native=True;value=native(*args);inside_native=False
            if kind=='actual':actual_completed+=1
            else:replayed+=1
            return value
        vehicle.native=counted
        def permit(drive):
            return time.time()<end-(180 if drive else 90) and remaining(window)>(200 if drive else 100)
        def checkpoint(value):
            dump(out/'PARTIAL_PROGRESS.json',value)
            if value.get('stage')=='capture_origin':dump(out/'ACTUAL_CAPTURE_ORIGIN.json',value)
            if value.get('stage')=='functional_refusal':dump(out/'FUNCTIONAL_REFUSAL.json',value)
        result.update(run_component(vehicle,plan,certifier,permit,checkpoint))
    except BaseException as exc:
        error=dict(error=repr(exc),traceback=traceback.format_exc());result['passed']=False
        dump(out/'ERROR.json',error)
    finally:
        result.update(error=error,models=None if creating else result['models'],
            new_actual_native=None if inside_native and kind=='actual' else actual_completed,
            model_initialization_inflight=creating,
            analytical_cpp_native=certifier.engine.native if certifier else 0,
            analytical_cpp_inflight=bool(certifier and getattr(certifier.engine,'in_call',False)),
            analytical_python_native=getattr(vehicle,'_v1157_capture_prediction_native',0) if vehicle else 0,
            analytical_python_inflight=getattr(vehicle,'_v1157_prediction_inflight',False) if vehicle else False)
        if vehicle is not None:
            dump(out/'REQUEST_JOURNAL.json',getattr(vehicle,'_v1157_journal',[]))
            dump(out/'MEASURED_STOP_CERTIFICATES.json',certifier.rows if certifier else [])
            try:result['physical']=vehicle.finish();result['evidence_saved']=True
            except BaseException as exc:result.update(passed=False,evidence_saved=False,save_error=repr(exc))
            # No new model task after safety/evidence exception. A normal functional
            # refusal can complete its certified tail and replay that safe prefix.
            if result.get('evidence_saved') and error is None and vehicle.count>0 and actual_completed==len(vehicle.rows) and not inside_native and time.time()<end-45 and remaining(window)>60:
                try:
                    kind='replay';result['replay_state_initializations']=1;result['own_replay_native']=None
                    result['replay']=factory.replay(vehicle,end,out/'physics')
                    result['own_replay_native']=replayed
                    result['passed']=bool(result['passed']and result['replay']['passed'])
                except BaseException as exc:
                    result.update(passed=False,replay_error=repr(exc),own_replay_native=None if inside_native else replayed)
            result['fully_recorded_actual_native']=len(vehicle.rows)
        signal.setitimer(signal.ITIMER_REAL,0)
        result.update(closed=True,source_unchanged=source_ok(),closed_unix=time.time(),wall_s=time.monotonic()-started)
        dump(out/'RESULT.json',result);print(encode(result))
    return 0 if result['passed']else 1


if __name__=='__main__':sys.exit(main())
