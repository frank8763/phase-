"""One fresh canonical vehicle: online discovery -> stop -> recovery -> goal.

No historical command, trace, saved physical state or former sensory packet is
read. The ordinary route is generated from each task's public t0 metadata.
"""
import fcntl,signal,sys,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from resource_policy import apply
RESOURCE=apply()
from authority import authorized
from kernel import *
sys.path.insert(0,str(C))
from fresh import finite_plan,follow,approach,choose_seed
from execute import execute
def main():
 task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());end=authorized(task,receipt);assert task['kind']!='t0' and end-time.time()>300;branch=next(x for x in json.loads((C/'BRANCHES.json').read_text())if x['id']==receipt['branch_id']);lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);pin_threads();out=Path(task['output']);assert not out.exists();out.mkdir(parents=True);v=None;creating=False;inside=False;evidence=None;segments=[];r=dict(resource_policy=RESOURCE,passed=False,model_initializations=0,historical_replay_native=0,navigation_native=0,own_replay_native=0,private_mujoco_native=0,fresh_native_zero=True,training_updates=0)
 def stop(*_):raise InterruptedError('ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.setitimer(signal.ITIMER_REAL,end-time.time())
 try:
  meta=json.loads((O/(task['case_id']+'_T0_METADATA.json')).read_text());initial_source=json.loads((O/(task['case_id']+'_STATIC_SOURCE.json')).read_text());assert initial_source['passed'],'TASK_T0_STATIC_SOURCE_REJECTED'
  factory=load('v1062_declared_factory',C/'scene_binding.py');creating=True;v=factory.create_vehicle(out/'physics',task);creating=False;r['model_initializations']=1;pin_threads();assert v.count==0 and v.d.time==0.;setup=json.loads((out/'physics/SETUP.json').read_text());preflight=json.loads((O/'PREFLIGHTS.json').read_text())[task['preflight_task_id']];assert preflight['passed']and setup['model_sha256']==preflight['setup']['model_sha256'],'PREFLIGHT_MODEL_CHANGED';assert np.array_equal(v.initial,np.load(Path(preflight['output'])/'physics/INITIAL_STATE.npz')['state']),'PREFLIGHT_INITIAL_STATE_CHANGED';import mujoco as mj
  before={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};old=v.adapter;v.adapter=law.Adapter(v.m,mj,v.dt,encoders=old.encoders);v.adapter.virtual_rate=.6;v.adapter.last=old.last.copy();v.adapter.integral=old.integral;assert all(np.array_equal(x,np.asarray(getattr(v.d,k)))for k,x in before.items());native=v.native
  def counted(*args):
   nonlocal inside
   pin_threads();
   if v.count%500==0:
    from budget import check
    check(128*1024**2)
   assert v.count<85000,'REGISTERED_NATIVE_BUDGET';inside=True;answer=native(*args);inside=False;return answer
  adapter_source=Path(v.adapter.compute.__func__.__code__.co_filename).resolve();assert adapter_source==R/'experiments/v1035_signed_timed_input_source/signed_control.py','ACTIVE_CONTROL_OWNER_CHANGED';dump(out/'REGISTERED_CONTROL_OWNER.json',dict(pid=os.getpid(),one_native_actuator_owner=True,source=str(adapter_source.relative_to(R)),source_sha256=sha(adapter_source),native_tick=v.count,virtual_rate=.6,model_state_unchanged_on_binding=True))
  v.native=counted;causal=load('v1056_causal_sensor',R/'experiments/v1024_full_route_execution/causal.py');norm=load('v1056_causal_periodic_norm',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
  class Evidence(causal.Evidence):
   def __init__(self,known):super().__init__(known);self.periodic=norm.PeriodicSupport()
  from owner import navigate
  navigate(v,setup,task,end,out,r)
  evidence=r.pop('_evidence',None);segments=r.pop('_direct_segments',[])
 except BaseException as e:r.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  evidence=r.pop('_evidence',evidence);segments=r.pop('_direct_segments',segments)
  if creating:r['model_initializations']=None
  n=None if inside or(creating and v is None)else v.count if v else 0;r['completed_native']=n;r['navigation_native']=n;dump(out/'DIRECT_SEGMENTS.json',segments)
  if v is not None:
   try:r['physical']=v.finish();r['evidence_saved']=True
   except BaseException as e:r.update(passed=False,evidence_saved=False,save_error=repr(e))
   if evidence is not None:dump(out/'CAUSAL_EVIDENCE.json',dict(first=evidence.first,rows=evidence.snapshots,periodic_constraints=evidence.periodic.constraints))
   if not inside and r.get('evidence_saved')and time.time()<end-30:
    try:r['own_replay_native']=None;r['replay']=factory.replay(v,end,out/'physics');r['own_replay_native']=r['replay']['replay_native'];r['passed']=r['passed']and r['replay']['passed']
    except BaseException as e:r.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);r.update(closed=True,closed_unix=time.time());__import__('entry_record').save(out,r)
 return 0 if r['passed']else 1
if __name__=='__main__':sys.exit(main())
