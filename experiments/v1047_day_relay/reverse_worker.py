"""One registered reverse component, isolated run_phase only."""
import fcntl,signal,sys,time,traceback
from kernel import *
from reverse_execute import execute

def main():
 task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());assert task in json.loads((C/'REVERSE_TASKS.json').read_text());assert receipt==dict(task_id=task['task_id'],window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json'));assert json.loads((O/'APPROVAL.json').read_text())['models_authorized'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());end=min(HARD_END-30,time.time()+300,time.time()+remaining_root()-30);assert end-time.time()>180
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);cpu=pin_threads();out=Path(task['output']);assert not out.exists();out.mkdir(parents=True);v=None;creating=False;inside=False;r=dict(passed=False,model_initializations=0,new_response_native=0,own_replay_native=0,private_mujoco_native=0)
 def stop(*_):raise InterruptedError('ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.setitimer(signal.ITIMER_REAL,end-time.time())
 try:
  factory=load('v1047_exact_factory',R/'experiments/v1020_terminal_two_route_development/physical.py');creating=True;v=factory.create_vehicle(out/'physics',task);creating=False;r['model_initializations']=1;pin_threads();assert v.count==0 and v.d.time==0. and v.actor is None
  import mujoco as mj
  old=v.adapter;adapter=law.Adapter(v.m,mj,v.dt,encoders=old.encoders);adapter.virtual_rate=.6;adapter.last=old.last.copy();adapter.integral=old.integral;v.adapter=adapter;dump(out/'CPU_BINDING.json',dict(cpu=cpu,all_own_threads_checked_before_every_native=True))
  setup=json.loads((out/'physics/SETUP.json').read_text());causal=load('v1047_reverse_packet',R/'experiments/v1024_full_route_execution/causal.py');packet=causal.packet(v,False);frozen=json.loads((C/('REVERSE_PLAN_'+task['task_id']+'.json')).read_text());p=Predictor(setup,initial(packet),PARAMETERS);states=[p.state.copy()];controls=[]
  for request in frozen['planned_body_requests']:s,u=p.step(*request);states.append(s);controls.append(u)
  states=np.asarray(states);assert abs(states-np.asarray(frozen['state_path'])).max()<=1e-8,'FRESH_PREDICTION_CHANGED';a,b=ref._old.Geometry(setup['known'],None).clearances(states[:,:3]);assert a.min()>=REQUIRED;plan=dict(frozen,state_path=states.tolist(),predicted_actuator_controls=np.asarray(controls).tolist());dump(out/'REGENERATED_PROFILE.json',plan);dump(out/'ACTUAL_INITIAL_PACKET.json',packet)
  native=v.native
  def counted(*args):
   nonlocal inside
   pin_threads();inside=True;answer=native(*args);inside=False;return answer
  v.native=counted;r['response']=execute(v,plan,end);r.update(passed=True,status='REVERSE_COMPONENT_AND_STOP')
 except BaseException as e:r.update(error=repr(e),traceback=traceback.format_exc(),status='FAILED')
 finally:
  if creating:r['model_initializations']=None
  r['new_response_native']=None if inside or(creating and v is None)else v.count if v else 0
  if v is not None:
   try:r['physical']=v.finish();r['evidence_saved']=True
   except BaseException as e:r.update(passed=False,save_error=repr(e),evidence_saved=False)
   if not inside and r.get('evidence_saved')and time.time()<end-30:
    try:r['own_replay_native']=None;r['replay']=factory.replay(v,end,out/'physics');r['own_replay_native']=r['replay']['replay_native'];r['passed']=r['passed']and r['replay']['passed']
    except BaseException as e:r.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);r.update(closed=True,closed_unix=time.time());dump(out/'RESULT.json',r)
 return 0 if r['passed']else 1
if __name__=='__main__':sys.exit(main())
