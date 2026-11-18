from recovery_tools import *
import signal,fcntl,traceback,gzip
from policy_execution import run_policy
def main():
    task=read(Path(sys.argv[1]));assert read(O/'APPROVAL.json')['models_authorized']is True,'NO_NEW_MODEL_AUTHORITY';task_contract(task)
    assert task in read(C/'TASKS.json')and source_ok()and remaining()>1600;out=Path(task['output']);assert out.is_relative_to(R/'runs/v858_nav2_verified/v1179')and not out.exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True)
    start=time.monotonic();end=time.time()+min(1500,remaining()-30)
    def halt(*_):raise TimeoutError('NATIVE_RECOVERY_ABSOLUTE_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.01,end-time.time()))
    v=None;creating=False;inside=False;kind='history';history=0;suffix=0;replayed=0;error=None;factory=None
    result=dict(passed=False,models=0,private_mujoco_native=0,training_updates=0,formal_retained_commit=False,final_stop_executed=False,universal_error_support_verified=False)
    try:
        sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'));from bindings import Adapter
        factory=load('v1179_original_cpu_factory',R/'experiments/v1114_coupled_steering_mode/physical.py');scene=load('v1179_original_scene_identity',R/'experiments/v1144_saved_entry_relay/scene_contract.py')
        creating=True;dump(out/'INITIALIZATION_ATTEMPT.json',dict(started_unix=time.time(),steps_before=0));v=factory.create(out/'physics',task);creating=False;result['models']=1;pin()
        import mujoco as mj
        from cpu_backend import require_cpu_backend
        assert v.count==0 and v.d.time==0. and v.actor is not None;setup=read(out/'physics/SETUP.json');oldsetup=read(PARENT/'physics/SETUP.json');result['scene_identity']=scene.verify(setup,oldsetup,task)
        assert sha(out/'physics/scene_model.mjb')==sha(PARENT/'physics/scene_model.mjb')
        with np.load(out/'physics/INITIAL_STATE.npz')as a,np.load(PARENT/'physics/INITIAL_STATE.npz')as b:assert np.array_equal(a['state'],b['state'])
        before={k:np.array(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};old=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=old.encoders);v.adapter.virtual_rate=.6;v.adapter.last=old.last.copy();v.adapter.integral=old.integral
        assert all(np.array_equal(a,np.asarray(getattr(v.d,k)))for k,a in before.items()),'CONTROLLER_BINDING_STATE_WRITE'
        dump(out/'CANONICAL_INITIAL_PACKET.json',packet(v))
        result['resource_policy']=dict(RESOURCE,renderer=require_cpu_backend());native=v.native
        def counted(*args):
            nonlocal inside,history,suffix,replayed
            assert time.time()<end-2 and remaining()>10,'NATIVE_DEADLINE'
            inside=True;value=native(*args);inside=False
            if kind=='history':history+=1
            elif kind=='suffix':suffix+=1
            else:replayed+=1
            return value
        v.native=counted
        with np.load(PARENT/'physics/NATIVE_TRACE.npz')as z:past={k:z[k].copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
        commands=np.array(read(PARENT/'physics/BODY_COMMANDS.json'),float);early=read(R/'runs/v858_nav2_verified/v1144/observation_main/MODE_JOURNAL.json');late=read(PARENT/'MODE_JOURNAL.json')
        assert len(commands)==HISTORY
        with gzip.open(PARENT/'physics/SENSORS.json.gz','rt')as f:scans=json.load(f)
        unique={}
        for scan in scans:
            k=scan['native_tick']
            if k<=HISTORY:unique.setdefault(k,scan)
        def scan_history():
            if v.count in unique:
                actual=v.scan();expected=unique[v.count];assert all(actual[k]==expected[k]for k in ['native_tick','time','xy','yaw','ranges']),'HISTORICAL_SENSOR_CHANGED'
        scan_history()
        maxhistorical=0.
        for i in range(HISTORY):
            assert time.time()<end-250 and remaining()>300,'HISTORY_RESERVE'
            row=None if i<20160 else early[i-20160]if i<32515 else late[i-32515]
            if row is not None:
                assert row['native']==i;v.adapter.parked_target=float(row['target'])if row['mode']else None
                assert abs(v.adapter.last-row['last_ctrl']).max()<=1e-10 and abs(v.adapter.integral-row['integral'])<=1e-10,'HISTORICAL_CONTROL_MEMORY'
            else:v.adapter.parked_target=None
            _,vr,wr,_,_,stale=commands[i];v.step(float(vr),float(wr),bool(stale))
            for k in past:
                a=np.asarray(getattr(v.d,k));b=past[k][i]
                if a.size:maxhistorical=max(maxhistorical,float(abs(a-b).max()))
            assert maxhistorical<=1e-8,'HISTORICAL_FULL_STATE_CHANGED';scan_history()
            if v.count%1000==0:dump(out/'PARTIAL_PROGRESS.json',dict(stage='original_history_reconstruction',native=v.count))
        saved=read(R/'runs/v1148_overnight_causal_recovery/actual_source/FRESH_INPUT.json');p=packet(v);assert abs(np.array(q.initial(p)['state'])-q.initial(saved['packet'])['state']).max()<=1e-8
        assert abs(v.adapter.last-saved['packet']['controller_memory']['last_ctrl']).max()<=1e-8 and abs(v.adapter.integral-saved['packet']['controller_memory']['integral'])<=1e-8
        assert not bool(getattr(v.adapter,'_steering_motion_active',False));dump(out/'ACTUAL_SOURCE_PACKET.json',p);result['historical_maximum_error']=maxhistorical;v._recovery_setup=setup
        reference,schedule=load_reference();selected=read(R/'runs/v1160_safe_terminal_connection/SELECTED.json')
        with np.load(R/selected['table_path'])as z:table={k:z[k].copy()for k in ['bounds','centers']}
        geometry=q.Geometry(selected['input'],table);raw=np.minimum(*geometry.components(reference['states'][:,:3],np.arange(5886)));assert raw.min()>=q.REQUIRED,'FROZEN_REFERENCE_RAW_REFUSED'
        assert source_ok(),'SOURCE_CHANGED_BEFORE_RECOVERY';kind='suffix'
        result.update(run_policy(v,reference,schedule,lambda:time.time()<end-150 and remaining()>200,lambda x:dump(out/'PARTIAL_PROGRESS.json',x)))
        dump(out/'ACTUAL_FINAL_PACKET.json',packet(v))
        shadow=v._recovery_shadow;shadowraw=np.minimum(*geometry.components(shadow[:,:3],np.arange(len(shadow))));assert shadowraw.min()>=q.REQUIRED,'COMPLETE_SHADOW_RAW_REFUSED';result['minimum_shadow_raw']=float(shadowraw.min())
        actual_final=np.array(packet(v)['body'][:3]);cycle=float(geometry.cycle(actual_final[None,:])[0]);assert cycle>=q.REQUIRED,'ACTUAL_TERMINAL_CYCLE_REFUSED';result['actual_terminal_cycle_raw']=cycle
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());result['passed']=False;dump(out/'ERROR.json',error)
    finally:
        result.update(error=error,models=None if creating else result['models'],historical_reconstruction_native=None if inside and kind=='history'else history,new_actual_native=None if inside and kind=='suffix'else suffix,total_actual_model_native=None if inside and kind!='replay'else v.count if v else None,own_replay_native=0,analytical_python_native=getattr(v,'_recovery_python_native',0)if v else 0,analytical_cpp_native=0,analytical_inflight_unknown=bool(v and getattr(v,'_recovery_python_inflight',False)),model_native_inflight_unknown=inside)
        if v is not None:
            dump(out/'RECOVERY_JOURNAL.json',getattr(v,'_recovery_journal',[]));shadow=getattr(v,'_recovery_shadow',np.empty((0,8)));np.savez_compressed(out/'SHADOW.npz',states=shadow)
            try:result['physical']=v.finish();result['evidence_saved']=True
            except BaseException as exc:result.update(passed=False,evidence_saved=False,save_error=repr(exc))
            result['fully_recorded_native']=len(v.rows)
            if error is None and result.get('evidence_saved')and v.count==len(v.rows)and v.count and not inside and time.time()<end-60 and remaining()>90:
                # Replay is evaluation only; it never changes the original failure.
                try:kind='replay';result['replay_state_initializations']=1;result['replay']=factory.replay(v,end,out/'physics');result['own_replay_native']=replayed;result['passed']=bool(result['passed']and result['replay']['passed'])
                except BaseException as exc:result.update(passed=False,replay_error=repr(exc),own_replay_native=None if inside else replayed)
        signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,source_unchanged=source_ok(),wall_s=time.monotonic()-start,closed_unix=time.time());dump(out/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items()if k in ['passed','new_actual_native','historical_reconstruction_native','own_replay_native','error']}));fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
