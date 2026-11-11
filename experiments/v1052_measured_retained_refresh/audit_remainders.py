"""Independent full Python regeneration and uncached native-time geometry."""
import importlib.abc,sys,json,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1052_measured_retained_refresh'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from refresh import roll
from kernel import predict,load,ref,REQUIRED,checks,dump,sha
def main():
 x=json.loads((R/'runs/v1051_retained_corridor_entry/INPUT_SOURCE.json').read_text());interval=load('v1052_exact_native_interval',R/'experiments/v1035_signed_timed_input_source/time_geometry.py');geo=ref._old.Geometry(x['setup']['known'],None);normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];rows=[]
 for tick in [2000,4000,6000,8000,10000,12000,14000]:
  packet=json.loads((O/('SAVED_PACKET_%05d.json'%tick)).read_text());result=json.loads((O/('REFRESH_%05d.json'%tick)).read_text());assert result['passed'];ss,uu,rr,mm=predict(x['setup'],packet,result['actions'],tail=False);fast,_,_,_=roll(x['setup'],packet,result['actions']);difference=float(np.max(abs(ss-fast)));assert difference<=1e-10;minimum=math.inf
  for first in range(0,len(ss),512):
   q=ss[first:first+512];t=packet['sim_time']+(first+np.arange(len(q)))*.01;support=interval.interval_support(x['source']['periodic']['vertices'],t-.055,t+.055);a=q[:,2];front=np.c_[np.cos(a),np.sin(a)];left=np.c_[-np.sin(a),np.cos(a)];body=q[:,:2]@normals.T-.44*abs(front@normals.T)-.375*abs(left@normals.T);dynamic=(body-support-.1).max(axis=1);static=geo.clearances(q[:,:3])[0];minimum=min(minimum,float(np.minimum(static,dynamic).min()))
  cc,upper=checks(ss,uu,rr,packet,x['setup'],np.array(x['goal']),minimum,REQUIRED);assert all(cc.values());a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[-1:,:3]);terminal=float(min(a[0],b[0]));assert terminal>=REQUIRED;rows.append(dict(saved_native=tick,passed=True,all_native_intervals=len(ss),cpp_python_difference=difference,minimum_independent_raw_m=minimum,terminal_full_cycle_hold_raw_m=terminal,goal_upper_m=upper,packet_sha256=sha(O/('SAVED_PACKET_%05d.json'%tick)),candidate_sha256=sha(O/('REFRESH_%05d.json'%tick))))
 dump(O/'INDEPENDENT_REMAINDER_AUDIT.json',dict(passed=True,rows=rows,all_native_intervals=sum(r['all_native_intervals']for r in rows),models=0,integrations=0,actual_goals=0,new_independent_navigation_samples=0,uses_frozen_preexisting_causal_prior=True,not_live_sensor_timing_qualification=True,physical_ready=False));print(json.dumps(dict(passed=True,rows=rows,models=0)))
if __name__=='__main__':main()
