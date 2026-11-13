"""Fixed nominal source preparation, no physical imports or initialization."""
import sys,json,importlib.abc
from common import C,R,O,dump
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from logic import predict_profile,kernel
import numpy as np
def main():
 assert not(O/'PREPARATION.json').exists()
 f=json.loads((C/'STATIC_T0_SOURCE_FIXTURE.json').read_text());s=f['setup'];tasks=[];proof=[]
 base=json.loads((R/'experiments/v1044_curvature_speed_prediction/TASKS.json').read_text())[0]
 for sign,name in [(1,'negative_to_positive'),(-1,'positive_to_negative')]:
  task=dict(base,task_id=name,run_id='v1114-'+name,slot=len(tasks),sign=sign,output=str(R/'runs/v858_nav2_verified/v1114'/name));plan,phases=predict_profile(s,f['packet'],sign)
  ss=plan['states'];u=plan['controls'];a,_=kernel.ref._old.Geometry(s['known'],None).clearances(ss[:,:3]);limits=np.asarray(s['limits']);rates=np.asarray(s['slew_per_second'])*.01
  checks=dict(complete=len(u)==8100,full_static=float(a.min())>=kernel.REQUIRED,body_caps=bool((abs(ss[:,3:6])<=np.array([.13,.03,.16])).all()),legal_ctrl=bool((u>=limits[:,0]-1e-10).all()and(u<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),u]),axis=0))<=rates+1e-10).all()),parked_rear_zero=bool((u[plan['modes']==1,2:]==0).all()),complete_stop=bool((plan['requests'][-2200:]==0).all()and abs(ss[-50:,3:6]).max()<=.003 and abs(ss[-50:,7]).max()<=.015),coupled_speed_reserve=bool(abs(ss[1:][plan['coupled'],3]).max()+.002<=.01))
  assert all(checks.values()),checks
  with np.load(R/'experiments/v1112_parked_mode_response'/('PLAN_'+name+'.npz'))as old:
   assert np.array_equal(plan['states'][:2201],old['states'][:2201])and np.array_equal(plan['controls'][:2200],old['controls'][:2200]),'INITIAL_HOLD_CHANGED'
  checks['old_initial_hold_exact']=True
  np.savez_compressed(C/('PLAN_'+name+'.npz'),**plan);dump(C/('PHASES_'+name+'.json'),phases);dump(C/('TASK_'+name+'.json'),task);tasks.append(task);proof.append(dict(task_id=name,checks=checks,minimum_raw_m=float(a.min()),nominal_native=len(u)))
 dump(C/'TASKS.json',tasks);dump(O/'PREPARATION.json',dict(passed=True,profiles=proof,analytical_native=16200,models=0,physical_integrations=0))
 print(json.dumps(proof))
if __name__=='__main__':main()
