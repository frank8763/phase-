"""Original-task exact historical restoration and fully certified timed suffix."""
import fcntl,signal,sys,traceback
from kernel import *
from execute import execute,regenerate,history_files

def main():
 task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());assert task in json.loads((C/'FULL_TASKS.json').read_text());assert receipt==dict(task_id=task['task_id'],window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json'),plan_sha256=sha(O/'SELECTED_PLAN.json'))
 assert json.loads((O/'APPROVAL.json').read_text())['models_authorized'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());end=min(HARD_END-30,time.time()+900,time.time()+remaining_root()-30);assert end-time.time()>300;lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);cpu=pin_threads();out=Path(task['output']);assert not out.exists();out.mkdir(parents=True);v=None;creating=False;inside=False;evidence=None;r=dict(passed=False,model_initializations=0,historical_replay_native=0,new_navigation_suffix_native=0,own_replay_native=0,private_mujoco_native=0)
 def stop(*_):raise InterruptedError('ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.setitimer(signal.ITIMER_REAL,end-time.time())
 try:
  H,old_setup=history_files();factory=load('v1050_full_factory',R/'experiments/v1020_terminal_two_route_development/physical.py');creating=True;v=factory.create_vehicle(out/'physics',task);creating=False;r['model_initializations']=1;pin_threads();assert v.count==0 and v.d.time==0.;setup=json.loads((out/'physics/SETUP.json').read_text());assert setup['model_sha256']==old_setup['model_sha256'],'MODEL_SHA_CHANGED'
  import mujoco as mj
  old=v.adapter;adapter=law.Adapter(v.m,mj,v.dt,encoders=old.encoders);adapter.virtual_rate=.6;adapter.last=old.last.copy();adapter.integral=old.integral;v.adapter=adapter;native=v.native
  def counted(*args):
   nonlocal inside
   pin_threads();inside=True;answer=native(*args);inside=False;return answer
  v.native=counted;causal=load('v1050_original_causal',R/'experiments/v1024_full_route_execution/causal.py');norm=load('v1050_public_norm',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
  class Evidence(causal.Evidence):
   def __init__(self,known):super().__init__(known);self.periodic=norm.PeriodicSupport()
  evidence=Evidence(setup['known']);evidence.update(v.scan());cache=load('v1050_trace_cache',R/'experiments/v1040_approach_information_audit/history_cache.py');expected=next(a['sha256']for a in json.loads((O/'HISTORY_RESTORE.json').read_text())['selected']if a['destination'].endswith('/NATIVE_TRACE.npz'));trace=cache.load_trace(H/'physics/NATIVE_TRACE.npz',expected);commands=json.loads((H/'physics/BODY_COMMANDS.json').read_text());assert len(commands)==23640;maximum=0.
  for i,c in enumerate(commands):
   assert time.time()<end-240,'HISTORY_RESTORE_TIME_RESERVE';v.step(c[1],c[2],c[5])
   for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
    now=np.asarray(getattr(v.d,k));maximum=max(maximum,float(abs(now-trace[k][i]).max())if now.size else 0.)
   assert maximum<=1e-8,'HISTORICAL_STATE_CHANGED'
   if v.count%5==0:evidence.update(v.scan())
   if v.count%500==0:dump(out/'PARTIAL.json',dict(phase='HISTORICAL_RESTORE',native=v.count,maximum_error=maximum))
  x=json.loads((O/'INPUT_SOURCE.json').read_text());packet=causal.packet(v,True);source=evidence.source(v);assert source['periodic']['vertices']==x['source']['periodic']['vertices'],'CAUSAL_SOURCE_CHANGED';assert np.max(abs(np.asarray(packet['body'])-x['packet']['body']))<=1e-8;plan=json.loads((O/'SELECTED_PLAN.json').read_text());assert plan['passed']and plan['retained_suffix_audit']['passed']and plan['input_source_sha256']==sha(O/'INPUT_SOURCE.json');assert not plan.get('requires_reverse')or json.loads((O/'REVERSE_QUALIFICATION.json').read_text())['passed'],'REVERSE_NOT_QUALIFIED';ss,uu,rr,mm=regenerate(setup,packet,plan);assert len(rr)<=40000 and np.max(abs(ss-np.asarray(plan['state_path'])))<=1e-8 and np.max(abs(uu-np.asarray(plan['predicted_actuator_controls'])))<=1e-8,'FRESH_INPUT_CHANGED';geometry=Geometry(setup['known'],source['periodic'],packet['sim_time']);low=geometry.complete(ss);cc,upper=checks(ss,uu,rr,packet,setup,np.asarray(task['goal_xy']),low,REQUIRED);assert all(cc.values()),'FRESH_PROFILE_NOT_QUALIFIED';dump(out/'FRESH_PLAN.json',dict(plan,source=source,packet=packet));r['historical_replay_maximum_error']=maximum;posmax=headmax=steermax=0.
  executed=execute(v,plan,end,evidence,out);posmax=executed['maximum_position_m'];headmax=executed['maximum_heading_rad'];steermax=executed['maximum_steering_rad']
  goal=float(np.linalg.norm(np.asarray(v.body()[:2])-task['goal_xy']));assert goal<=.45 and np.linalg.norm(np.asarray(v.body()[3:]))<=.03,'ACTUAL_GOAL_OR_STOP_FAILED';r.update(passed=True,status='ACTUAL_ORIGINAL_GOAL_CONTINUATION',actual_original_goal_reached=True,maximum_position_m=posmax,maximum_heading_rad=headmax,maximum_steering_rad=steermax)
 except BaseException as e:r.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:r['model_initializations']=None
  n=None if inside or(creating and v is None)else v.count if v else 0;r['completed_native']=n;r['historical_replay_native']=min(n,23640)if n is not None else None;r['new_navigation_suffix_native']=max(0,n-23640)if n is not None else None
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
