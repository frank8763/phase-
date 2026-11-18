"""Same saved rejected state, actual new stop executor on analytical interface."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('STOP_QUALIFICATION_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import copy,json,time,fcntl
from stop_policy import decision,execute_current_stop,q,np,original
import stop_certificates as stops
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 raw=R/'runs/v858_nav2_verified/v1218/main_slot03';x=read(raw/'LIVE_OBSERVER_INPUT.json');last=read(raw/'LIVE_OBSERVER_CERTIFICATES.json')[-1];origin=last['packet']
 with np.load(raw/'LIVE_OBSERVER_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 rows=read(raw/'LIVE_OBSERVER_SELECTION.json')['rows'];block=original.front(original.remaining_rows(rows,last['offset']),last['prefix']);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);proofs,pred=stops.prove(engine,q.Geometry(x,table),x,origin,dict(q.initial(origin),steering_load_episode=last['steering_load_episode']),block)
 assert decision(proofs)=='EXECUTE_CURRENT_STOP';assert decision([dict(passed=False),dict(passed=True)])=='REFUSE_NO_CURRENT_CERTIFICATE';assert decision([dict(passed=True),dict(passed=True)])=='CONTINUE'
 class Interface:
  def __init__(self):
   self.count=origin['native_tick'];self.start=self.count;self.calls=[];self.predictor=q.model.Predictor(x['setup'],dict(q.initial(origin),steering_load_episode=last['steering_load_episode']));self.adapter=self.predictor.adapter
  def step(self,v,w,stale):self.calls.append((v,w,stale));self.predictor.step(v,w,stale);self.count+=1
  def scan(self):return {'analytical_only':True}
  def packet(self):
   p=copy.deepcopy(origin);s=self.predictor.state;p.update(native_tick=self.count,sim_time=origin['sim_time']+.01*(self.count-self.start),body=[float(s[0]),float(s[1]),float(s[2]),float(s[3]),float(s[5])],body_lateral=float(s[4]))
   t=np.tan(s[6]);d=np.array([1.-.45*t,1.+.45*t]);p['steering'].update(position=np.arctan2(t,d).tolist(),velocity=((1.+t*t)/(d*d+t*t)*s[7]).tolist(),native_tick=self.count);p['controller_memory']=dict(last_ctrl=self.adapter.last.tolist(),integral=float(self.adapter.integral));return p
 captured=[]
 def save(meta,actual,expected,journal):
  captured.append(meta);q.dump(O/'STOP_EXECUTOR_RECORD.json',meta);np.savez_compressed(O/'STOP_EXECUTOR_TRACE.npz',actual=actual,expected=expected);q.dump(O/'STOP_EXECUTOR_JOURNAL.json',journal)
 v=Interface();answer=execute_current_stop(v,proofs,pred,origin,lambda v:v.packet(),lambda _:None,lambda:True,save)
 assert answer['passed']and not answer['functional_goal_passed']and v.calls==[(0.,0.,False)]*2200 and captured[-1]['complete']
 negatives=[]
 for name,pp,ss,packet in [('current_refused',[dict(passed=False),proofs[1]],pred,origin),('incomplete_tail',proofs,[pred[0][:-1],pred[1]],origin),('changed_origin',proofs,pred,dict(origin,native_tick=origin['native_tick']+1))]:
  vv=Interface()
  try:execute_current_stop(vv,pp,ss,packet,lambda v:v.packet(),lambda _:None,lambda:True,lambda *args:None)
  except AssertionError:assert not vv.calls;negatives.append(name)
  else:raise AssertionError('NEGATIVE_ACCEPTED '+name)
 maxerror=float(np.max(abs(v.predictor.state-pred[0][-1])));assert maxerror<=1e-8
 result=dict(passed=True,original_prospective_refusal_reproduced=True,actual_new_executor_exercised=True,analytical_cpp_native=engine.native,analytical_python_native=2200,complete_stop_length=2200,independent_cpp_python_error=maxerror,refused_nonzero_commands=0,negative_cases=negatives,models=0,new_mujoco_native=0,not_physical_validation=True)
 q.dump(O/'STOP_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
