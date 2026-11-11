"""One fresh canonical vehicle: online discovery -> stop -> recovery -> goal.

No historical command, trace, saved physical state or former sensory packet is
read. The ordinary route is generated from each task's public t0 metadata.
"""
import fcntl,signal,sys,traceback
from kernel import *
sys.path.insert(0,str(C))
from fresh import finite_plan,follow,approach,choose_seed
from execute import execute
def main():
 task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());assert task in json.loads((C/'TASKS.json').read_text());assert receipt==dict(task_id=task['task_id'],window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json'));approval=json.loads((O/'APPROVAL.json').read_text());assert approval['models_authorized']and task['task_id']in approval['allowed_task_ids'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());end=min(HARD_END-30,time.time()+600,time.time()+remaining_root()-30);assert end-time.time()>300;lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);pin_threads();out=Path(task['output']);assert not out.exists();out.mkdir(parents=True);v=None;creating=False;inside=False;evidence=None;segments=[];r=dict(passed=False,model_initializations=0,historical_replay_native=0,navigation_native=0,own_replay_native=0,private_mujoco_native=0,fresh_native_zero=True,training_updates=0)
 def stop(*_):raise InterruptedError('ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.setitimer(signal.ITIMER_REAL,end-time.time())
 try:
  meta=json.loads((O/(task['case_id']+'_T0_METADATA.json')).read_text());initial_source=json.loads((O/(task['case_id']+'_STATIC_SOURCE.json')).read_text());assert initial_source['passed'],'TASK_T0_STATIC_SOURCE_REJECTED'
  factory=load('v1056_original_exact_factory',R/'experiments/v1020_terminal_two_route_development/physical.py');creating=True;v=factory.create_vehicle(out/'physics',task);creating=False;r['model_initializations']=1;pin_threads();assert v.count==0 and v.d.time==0.;setup=json.loads((out/'physics/SETUP.json').read_text());assert setup['model_sha256']==json.loads((C/'CANONICAL_MODEL_SHA.json').read_text())[task['case_id']],'CANONICAL_MODEL_CHANGED';import mujoco as mj
  before={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};old=v.adapter;v.adapter=law.Adapter(v.m,mj,v.dt,encoders=old.encoders);v.adapter.virtual_rate=.6;v.adapter.last=old.last.copy();v.adapter.integral=old.integral;assert all(np.array_equal(x,np.asarray(getattr(v.d,k)))for k,x in before.items());native=v.native
  def counted(*args):
   nonlocal inside
   pin_threads();assert v.count<85000,'REGISTERED_NATIVE_BUDGET';inside=True;answer=native(*args);inside=False;return answer
  v.native=counted;causal=load('v1056_causal_sensor',R/'experiments/v1024_full_route_execution/causal.py');norm=load('v1056_causal_periodic_norm',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
  class Evidence(causal.Evidence):
   def __init__(self,known):super().__init__(known);self.periodic=norm.PeriodicSupport()
  evidence=Evidence(setup['known']);assert not evidence.update(v.scan()),'DYNAMIC_VISIBLE_AT_T0';p=causal.packet(v,False);assert np.max(abs(np.array(p['body'])-meta['packet']['body']))<=1e-8;static=finite_plan(setup,p,None,initial_source['plan']['planned_body_requests'],'FRESH_T0_STATIC_ROUTE');assert static['passed'];dump(out/'STATIC_PLAN.json',static);phase=follow(v,static,end,evidence,out,'STATIC',interrupt=True);segments.append(dict(path='STATIC_PLAN.json',origin=0,count=phase['executed']));assert phase['discovered'],'REAL_SENSOR_DISCOVERY_REQUIRED';discovery=v.count;r['first_causal_discovery_native']=discovery
  # The registered2200 zero inputs contain the original full328 discovery
  # stop and additional causal observation; no history is restored.
  requests=np.zeros((2200,3));braking=finite_plan(setup,causal.packet(v,True),evidence.source(v),requests,'FRESH_DISCOVERY_STOP_AND_OBSERVE');assert braking['passed'];dump(out/'BRAKE_PLAN.json',braking);origin=v.count;follow(v,braking,end,evidence,out,'BRAKE');segments.append(dict(path='BRAKE_PLAN.json',origin=origin,count=v.count-origin));assert np.linalg.norm(v.body()[3:])<=.03
  source=evidence.source(v);p=causal.packet(v,True);approach_plan=approach(setup,p,source,initial_source['plan']['planned_body_requests'],discovery);dump(out/'APPROACH_PLAN.json',approach_plan);origin=v.count;follow(v,approach_plan,end,evidence,out,'APPROACH');segments.append(dict(path='APPROACH_PLAN.json',origin=origin,count=v.count-origin));r['observation_approach_native']=v.count-origin
  p=causal.packet(v,True);source=evidence.source(v);warm=json.loads((C/'RECOVERY_WARM_SEED.json').read_text())['actions'];seed=choose_seed(setup,p,source,task['goal_xy'],initial_source['plan']['planned_body_requests'],discovery,approach_plan['movement_native'],warm);dump(out/'ONLINE_RECOVERY_INITIAL.json',dict(packet=p,source=source,seed=seed));r['recovery_origin_native']=v.count;executed=execute(v,setup,seed,end,evidence,out,causal.packet);r['feedback_execution']=executed;goal=float(np.linalg.norm(np.array(v.body()[:2])-task['goal_xy']));assert goal<=.45 and np.linalg.norm(v.body()[3:])<=.03,'FRESH_ORIGINAL_GOAL_AND_STOP';assert np.linalg.norm(np.array(v.body()[:2])-evidence.first['xy'])>=1.,'FRESH_ONE_METRE_AFTER_DISCOVERY';r.update(passed=True,status='FRESH_T0_GOAL_AND_STOP',actual_original_goal_reached=True,actual_goal_distance_m=goal)
 except BaseException as e:r.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:r['model_initializations']=None
  n=None if inside or(creating and v is None)else v.count if v else 0;r['completed_native']=n;r['navigation_native']=n;dump(out/'FRESH_PREFIX_SEGMENTS.json',segments)
  if v is not None:
   try:r['physical']=v.finish();r['evidence_saved']=True
   except BaseException as e:r.update(passed=False,evidence_saved=False,save_error=repr(e))
   if evidence is not None:dump(out/'CAUSAL_EVIDENCE.json',dict(first=evidence.first,rows=evidence.snapshots,periodic_constraints=evidence.periodic.constraints))
   if not inside and r.get('evidence_saved')and time.time()<end-30:
    try:r['own_replay_native']=None;r['replay']=factory.replay(v,end,out/'physics');r['own_replay_native']=r['replay']['replay_native'];r['passed']=r['passed']and r['replay']['passed']
    except BaseException as e:r.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);r.update(closed=True,closed_unix=time.time());dump(out/'RESULT.json',r)
 return 0 if r['passed']else 1
if __name__=='__main__':sys.exit(main())
