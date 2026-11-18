"""Fresh physical owner. No archived control/state/sensor reads after entry."""
from route_tools import *
import signal,fcntl,traceback,gzip
def main():
    task=read(Path(sys.argv[1]));assert read(O/'APPROVAL.json')['models_authorized']is True,'NO_NEW_MODEL_AUTHORITY';task_contract(task);assert task in read(C/'TASKS.json')and source_ok()and remaining()>1700
    out=Path(task['output']);assert not out.exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True)
    start=time.monotonic();end=time.time()+min(1500,remaining()-30)
    def halt(*_):raise TimeoutError('FRESH_CHAIN_ABSOLUTE_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.01,end-time.time()))
    v=None;creating=False;inside=False;kind='actual';actual=0;replayed=0;error=None;journal=[]
    result=dict(passed=False,models=0,internal_factory_model_constructions='unknown',historical_reconstruction_native=0,historical_controls_used=0,private_mujoco_native=0,training_updates=0,formal_retained_commit=False,final_stop_executed=False,universal_error_support_verified=False)
    try:
        owner=configure_owner(O,end);old.history_guard(out)
        sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'));from bindings import Adapter
        physical=factory();scene=load('v1184_route_scene',R/'experiments/v1089_route_scene_contract/contract.py')
        creating=True;dump(out/'INITIALIZATION_ATTEMPT.json',dict(started_unix=time.time(),steps_before=0));v=physical.create(out/'physics',task);creating=False;result['models']=1;pin()
        import mujoco as mj
        from cpu_backend import require_cpu_backend
        setup=read(out/'physics/SETUP.json');meta=read(R/('runs/v1122_cache_entry_relay/'+task['case_id']+'_T0_METADATA.json'));assert v.count==0 and v.d.time==0. and v.actor is not None
        load('v1184_public_setup',R/'experiments/v1067_causal_replan_brake_reserve/initial_contract.py').check_setup(setup,meta)
        result['scene_contract']=scene.verify_live(v,task)
        assert sha(out/'physics/scene_model.mjb')==setup['model_sha256']
        b=np.asarray(v.body());assert abs(b[:2]-task['start_xy']).max()<=1e-8 and abs(math.atan2(math.sin(b[2]-task['start_yaw']),math.cos(b[2]-task['start_yaw'])))<=1e-8
        before={k:np.array(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};previous_adapter=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=previous_adapter.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous_adapter.last.copy();v.adapter.integral=previous_adapter.integral
        assert all(np.array_equal(a,np.asarray(getattr(v.d,k)))for k,a in before.items());dump(out/'CANONICAL_INITIAL_PACKET.json',packet(v));result['resource_policy']=dict(RESOURCE,renderer=require_cpu_backend());native=v.native
        def counted(*args):
            nonlocal inside,actual,replayed
            assert time.time()<end-2 and remaining()>10,'NATIVE_DEADLINE';inside=True;value=native(*args);inside=False
            if kind=='actual':actual+=1
            else:replayed+=1
            return value
        v.native=counted;step=v.step
        def applied(vr,wr,stale=False):
            assert v.count<task['native_limit'];old=v.count;row=dict(before_native=old,phase=getattr(v,'_chain_phase','fresh_normal'),parked_target=getattr(v.adapter,'parked_target',None),request=[float(vr),float(wr),bool(stale)],last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral),applied=False);journal.append(row)
            step(float(vr),float(wr),bool(stale));row['applied']=True;assert v.count==old+1;previous.body_gate(packet(v))
        v.step=applied;v._chain_phase='fresh_normal'
        owner.navigate(v,setup,task,end,out,result);result.update(models=1,full_fresh_t0_navigation=True,final_stop_executed=True,formal_retained_commit=False)
        dump(out/'ACTUAL_FINAL_PACKET.json',packet(v))
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());result['passed']=False;dump(out/'ERROR.json',error)
    finally:
        result.pop('_evidence',None);segments=result.pop('_direct_segments',[]);dump(out/'DIRECT_SEGMENTS.json',segments)
        result.update(error=error,models=None if creating else result['models'],new_actual_native=None if inside and kind=='actual'else actual,total_actual_model_native=None if inside and kind=='actual'else actual,own_replay_native=0,analytical_python_native=None,analytical_cpp_native=None,analytical_total_scope='Original static preview work not instrumented; total unknown, recorded recovery counts separately',model_native_inflight_unknown=inside)
        if v is not None:
            dump(out/'APPLIED_JOURNAL.json',journal);result['known_recovery_counts']=dict(getattr(v,'_chain_counts',{}),observer_cpp_native=getattr(getattr(v,'_chain_engine',None),'native',None),observer_cpp_inflight=bool(getattr(getattr(v,'_chain_engine',None),'in_call',False)))
            try:result['physical']=v.finish();result['evidence_saved']=True
            except BaseException as exc:result.update(passed=False,evidence_saved=False,save_error=repr(exc))
            result['fully_recorded_native']=len(v.rows)
            if error is None and result.get('evidence_saved')and v.count==len(v.rows)and not inside and time.time()<end-60 and remaining()>90:
                try:kind='replay';result['replay_state_initializations']=1;result['replay']=physical.replay(v,end,out/'physics');result['own_replay_native']=replayed;result['passed']=bool(result['passed']and result['replay']['passed'])
                except BaseException as exc:result.update(passed=False,replay_error=repr(exc),own_replay_native=None if inside else replayed)
        signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-start,closed_unix=time.time());dump(out/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items()if k in ['passed','new_actual_native','own_replay_native','error']}));fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
