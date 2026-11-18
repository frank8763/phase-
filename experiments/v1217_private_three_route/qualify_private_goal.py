"""Actual private runtime executor under cached legacy imports; one unchanged fixture."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('PRIVATE_GOAL_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import fcntl,copy,types,traceback,signal
import route_dispatch

def main():
 assert not(O/'PRIVATE_GOAL_QUALIFICATION.json').exists()
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 old=science();q=old.q;np=q.np;start=time.monotonic();end=start+180
 # Preload precisely the real legacy collision and unrelated generic names.
 old_admission=load('admission',R/'runtime/mk-mini/experiments/phase_rpccr_p0b57_v1/admission.py')
 poisoned={'admission':old_admission}
 for name in ['goal_entry','current_goal_source','candidate_search','connection','live_entry','audit_admission']:
  m=types.ModuleType(name);m.__file__='synthetic_wrong_'+name;sys.modules[name]=m;poisoned[name]=m
 entry=route_dispatch.current_executor().goal_entry
 p=R/'runs/v858_nav2_verified/v1210/main_WEST_EAST';x=read(p/'LIVE_GOAL_INPUT.json')
 with np.load(p/'LIVE_GOAL_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 class Interface:
  def __init__(self):
   self.count=x['packet']['native_tick'];self.begin=self.count;self._live_load=True
   self.predictor=q.model.Predictor(x['setup'],dict(q.initial(x['packet']),steering_load_episode=True));self.adapter=self.predictor.adapter;self.adapter.parked_target=None
  def step(self,v,w,stale):
   assert stale is False;self.predictor.step(float(v),float(w),False);self.count+=1
  def scan(self):return dict(analytical_interface_only=True,no_physical_sensor_evidence=True)
  def packet(self):
   p=copy.deepcopy(x['packet']);s=self.predictor.state;p['native_tick']=self.count;p['sim_time']=x['packet']['sim_time']+.01*(self.count-self.begin);p['body']=[float(s[0]),float(s[1]),float(s[2]),float(s[3]),float(s[5])];p['body_lateral']=float(s[4]);t=np.tan(s[6]);d=np.array([1.-.45*t,1.+.45*t]);p['steering'].update(position=np.arctan2(t,d).tolist(),velocity=((1.+t*t)/(d*d+t*t)*s[7]).tolist(),native_tick=self.count);p['controller_memory']=dict(last_ctrl=self.adapter.last.tolist(),integral=float(self.adapter.integral));p.update(coupled_episode=False,steering_motion_active=False);return p
 out=O/'PRIVATE_GOAL_INTERFACE';out.mkdir();v=Interface();answer=None;error=None
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('PRIVATE_QUALIFICATION180')));signal.setitimer(signal.ITIMER_REAL,180)
 try:
  answer=entry.execute(v,x['setup'],x,table,end-15,lambda:time.monotonic()<end-15,lambda owner:owner.packet(),lambda z:dump(O/'PRIVATE_PROGRESS.json',z),out)
  core=load('phase_v1217_goal_core_audit',R/'experiments/v1204_goal_audit_worker/audit_goal.py');bundle=core.load_bundle(out);core_result=core.verify(x,table,bundle,True)
  audit=load('phase_v1217_admission_audit',C/'audit_admission.py');admission=audit.verify_bundle(x,table,bundle,end-5)
  expected=R/'runs/v1214_shadow_route_integration/GOAL_INTERFACE_original_WE'
  with np.load(expected/'EXECUTED.npz')as z:
   maximum=max(float(abs(z[k]-v._goal_trace[k]).max())for k in z.files)
  assert maximum<=1e-8,'PRIVATE_NAMESPACE_CHANGED_SCIENTIFIC_EXECUTION'
  assert all(sys.modules[n]is m for n,m in poisoned.items())
  dump(out/'INDEPENDENT_CORE_AUDIT.json',core_result);dump(out/'INDEPENDENT_ADMISSION_AUDIT.json',admission)
  result=dict(passed=True,full_private_executor=True,real_legacy_admission_preloaded=True,other_generic_names_poisoned=True,trace_error_vs_qualified_V1214=maximum,native=answer['native'],core_audit=core_result,admission_audit=admission,admission_python_native=answer['admission_python_native'],generation_cpp_native=answer['analytical_cpp_native'],interface_and_shadow_python_native=2*answer['native'],models=0,new_mujoco_native=0,wall_s=time.monotonic()-start)
 except BaseException as exc:
  result=dict(passed=False,error=repr(exc),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,analytical_inflight_unknown=True)
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);dump(O/'PRIVATE_GOAL_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
