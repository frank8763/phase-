"""One real phase-specific canonical initialization and scan, zero integrations."""
import sys,json,time,signal,fcntl,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(C));import worker
w=worker.load_worker()
def main():
 task,O,cfg,out=w.entry(sys.argv[1]);window=json.loads((O/'ROUND_WINDOW.json').read_text());approval=json.loads((O/'APPROVAL.json').read_text());assert approval['models_authorized']and task['task_id']in approval['allowed_task_ids'];assert task['kind']=='t0';assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==window['boot_id'];assert time.time()<window['absolute_deadline_unix']and time.monotonic()<window['hard_stop_monotonic']
 assert all(w.sha(R/p)==h for p,h in json.loads(Path(cfg['source_freeze']).read_text())['files'].items())
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True,exist_ok=False);result=dict(passed=False,vehicle_initializations=None,navigation_native=0,new_actual_native=0,own_replay_native=0,replay_state_initializations=0,historical_replay_native=0,private_mujoco_native=0,analytical_prediction_native=0,training_updates=0);v=None
 def halt(*_):raise TimeoutError('T0_OR_ROOT_DEADLINE')
 signal.signal(signal.SIGALRM,halt);signal.signal(signal.SIGTERM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,min(90,window['absolute_deadline_unix']-time.time()-10)))
 try:
  v=w.factory(O).create_vehicle(out/'physics',task);result['vehicle_initializations']=1;proof=__import__('route_scene_contract').verify_live(v,task);setup=json.loads((out/'physics/SETUP.json').read_text());meta=json.loads((O/(task['case_id']+'_T0_METADATA.json')).read_text());w.load('t0_public_setup',R/'experiments/v1067_causal_replan_brake_reserve/initial_contract.py').check_setup(setup,meta);assert w.np.max(abs(w.np.asarray(v.body())-meta['packet']['body']))<=1e-8
  scan=v.scan();summary=v.finish();assert not v.rows and v.count==0 and v.d.time==0 and not v.commands;assert v.first_detection is None and summary['bad_contacts']==0 and summary['minimum_actual_clearance_m']>=.15
  result.update(passed=True,summary=summary,scene_contract=proof,scan=scan)
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
 finally:
  if v is not None:result['physical']=v.finish()
  signal.setitimer(signal.ITIMER_REAL,0);result['closed']=True;w.dump(out/'RESULT.json',result)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
