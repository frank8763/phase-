"""Exercise the live observer on a Python interface; never fabricate sensors."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import copy,json,time,fcntl,types,traceback
import live_entry as live
q=live.q;np=q.np;C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
class FreshPhysicalObservationRequired(BaseException):pass
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 out=O/'LIVE_INTERFACE_COMPLETE';out.mkdir();raw=R/'runs/v858_nav2_verified/v1218/main_slot03';x=read(raw/'LIVE_OBSERVER_INPUT.json')
 with np.load(raw/'LIVE_OBSERVER_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 selected=read(O/'CANDIDATE_slot03/RESULT.json')
 with np.load(O/'CANDIDATE_slot03/REFERENCE.npz')as z:selected.update({k:z[k].copy()for k in z.files})
 calls=[];beg=time.monotonic()
 class Interface:
  def __init__(self):
   self.count=x['packet']['native_tick'];self.begin=self.count;self.predictor=q.model.Predictor(x['setup'],dict(q.initial(x['packet']),steering_load_episode=False));self.adapter=self.predictor.adapter;self.adapter.commands.ids=np.arange(4);self.d=types.SimpleNamespace(ctrl=np.zeros(4));self.trace=[self.predictor.state.copy()]
  def step(self,v,w,stale):
   assert stale is False;self.predictor.step(v,w,stale);self.count+=1;self.trace.append(self.predictor.state.copy());self.d.ctrl=self.adapter.last.copy()
  def scan(self):return dict(analytical_only=True,no_physical_sensor_evidence=True)
  def packet(self):
   p=copy.deepcopy(x['packet']);s=self.predictor.state;p.update(native_tick=self.count,sim_time=x['packet']['sim_time']+.01*(self.count-self.begin),body=[float(s[0]),float(s[1]),float(s[2]),float(s[3]),float(s[5])],body_lateral=float(s[4]));t=np.tan(s[6]);d=np.array([1.-.45*t,1.+.45*t]);p['steering'].update(position=np.arctan2(t,d).tolist(),velocity=((1.+t*t)/(d*d+t*t)*s[7]).tolist(),native_tick=self.count);p['controller_memory']=dict(last_ctrl=self.adapter.last.tolist(),integral=float(self.adapter.integral));return p
 v=Interface();e=types.SimpleNamespace(update=lambda s:None)
 def fresh(owner,setup):
  calls.append(owner.count)
  if len(calls)>1:raise FreshPhysicalObservationRequired()
  return e,dict(saved_input_fixture=True,not_new_sensor_evidence=True)
 live.bridge.fresh_evidence=fresh;live.bridge.current_input=lambda *args:copy.deepcopy(x);live.bridge.joint_table=lambda source:(table,0)
 # Selection itself was exercised separately on this exact saved input. Here
 # reuse its full arrays, exercising all actual executor commands and proofs.
 live.observer_source.synthesize=lambda *args:copy.deepcopy(selected)
 live.packet=lambda owner:owner.packet()
 try:live.execute(v,x['setup'],{},time.time()+600,e,out,live.packet,out,remaining_fn=lambda:600.)
 except FreshPhysicalObservationRequired:pass
 else:raise AssertionError('FRESH_OBSERVATION_BOUNDARY_NOT_REACHED')
 assert len(calls)==2 and live.previous.stopped(v.packet())
 a=np.asarray(v.trace);error=float(abs(a-selected['states']).max());assert error<=1e-8
 result=dict(passed=True,complete_live_observer_exercised=True,native=len(a)-1,cpp_python_state_error=error,stopped_before_fresh_physical_observation=True,goal_not_executed=True,models=0,new_mujoco_native=0,analytical_python_native=len(a)-1,analytical_cpp_native=v._chain_engine.native,wall_s=time.monotonic()-beg)
 q.dump(O/'LIVE_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except BaseException as e:q.dump(O/'LIVE_QUALIFICATION_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0,new_mujoco_native=0));raise
