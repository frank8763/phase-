"""Actual registered t0 construction and zero-integration scene checks."""
from campaign_context import *
import signal,fcntl,traceback
def main():
    task=read(Path(sys.argv[1]));assert read(O/'APPROVAL.json')['models_authorized'],'NO_NEW_MODEL_AUTHORITY';task_contract(task);assert not read(O/'APPROVAL.json').get('synthetic_qualification_only',False) and task['role']=='t0'and task in read(C/'TASKS.json')and source_ok()and remaining()>150
    out=Path(task['output']);assert not out.exists();f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True)
    end=time.time()+min(120,remaining()-10);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('T0_120S')));signal.setitimer(signal.ITIMER_REAL,end-time.time())
    r=dict(passed=False,models=0,new_actual_native=0,own_replay_native=0,historical_reconstruction_native=0,total_actual_model_native=0,analytical_cpp_native=0,analytical_python_native=0);creating=False;v=None
    try:
        physical=factory();creating=True;v=physical.create(out/'physics',task);creating=False;r['models']=1;pin()
        assert v.count==0 and v.d.time==0. and v.actor is not None
        scene=load('v1242_t0_scene',R/'experiments/v1089_route_scene_contract/contract.py');r['scene_contract']=scene.verify_live(v,task)
        setup=read(out/'physics/SETUP.json');meta=read(R/('runs/v1122_cache_entry_relay/'+task['case_id']+'_T0_METADATA.json'));load('v1242_public',R/'experiments/v1067_causal_replan_brake_reserve/initial_contract.py').check_setup(setup,meta)
        p=packet(v);assert abs(np.array(p['body'][:2])-task['start_xy']).max()<=1e-8 and abs(math.atan2(math.sin(p['body'][2]-task['start_yaw']),math.cos(p['body'][2]-task['start_yaw'])))<=1e-8
        assert previous.stopped(p)and not p['dynamic_discovered'];scan=v.scan();assert v.first_detection is None
        causal=load('v1242_t0_estimator',R/'experiments/v1024_full_route_execution/causal.py');e=causal.Evidence(setup['known']);assert not e.update(scan),'DYNAMIC_VISIBLE_AT_T0'
        assert v.bad==0 and v.min_clear>=.15-1e-8 and v.min_self>=-1e-10 and len(v.contacts)==1
        dump(out/'INITIAL_CONTACTS.json',v.contacts[0]);dump(out/'INITIAL_SENSOR.json',scan)
        r.update(passed=True,canonical_initial_packet=p,initial_safety=dict(minimum_actual_clearance_m=v.min_clear,minimum_self_margin_m=v.min_self,bad_contacts=v.bad),original_sensor_actor_not_discovered=True,model_sha256=setup['model_sha256'],internal_factory_constructions='unknown',error=None)
    except BaseException as exc:r.update(error=dict(error=repr(exc),traceback=traceback.format_exc()),models=None if creating else r['models'])
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);r.update(closed=True,closed_unix=time.time());dump(out/'RESULT.json',r)
    print(json.dumps({k:v for k,v in r.items()if k in['passed','models','error']}));return 0 if r['passed']else 1
if __name__=='__main__':sys.exit(main())
