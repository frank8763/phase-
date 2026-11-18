"""Actual NS live adapter with saved real rays and analytical dynamics only."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from campaign_context import *
import types,gzip,copy,traceback,fcntl
from route_dispatch import ns_executor

def main():
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 live=ns_executor();helper=load('v1235_analytical_interface',R/'experiments/v1203_goal_entry_handoff/qualify_entry.py')
 raw=R/'runs/v858_nav2_verified/v1230/main_slot10';x=read(raw/'LIVE_GOAL_INPUT.json')
 with gzip.open(raw/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
 class Interface(helper.AnalyticalInterface):
  def __init__(self,x):
   super().__init__(x);self.sensor_rows=copy.deepcopy(sensors);self.first_detection=dict(saved_real_discovery=True)
  def body(self):return self.packet()['body']
  def steering_sample(self):
   s=self.packet()['steering'];return np.array(s['position']+s['velocity'])
  @property
  def d(self):
   s=self.predictor.state;a=s[2];return types.SimpleNamespace(time=self.packet()['sim_time'],qvel=np.array([s[3]*np.cos(a)-s[4]*np.sin(a),s[3]*np.sin(a)+s[4]*np.cos(a)]))
 v=Interface(x);out=O/'LIVE_ANALYTICAL';out.mkdir();start=time.monotonic()
 answer=live.execute(v,x['setup'],None,time.time()+500,None,out,None,output=out,remaining_fn=lambda:1000.)
 fresh=read(out/'LIVE_GOAL_INPUT.json');assert fresh['goal']==x['goal'] and fresh['setup']==x['setup'] and fresh['packet']['native_tick']==x['packet']['native_tick']
 auditor=load('v1235_ns_live_qualification_audit',C/'ns_audit.py')
 table=auditor.causal.table_check(out,'LIVE_GOAL',fresh,sensors)
 bundle=auditor.load_ns_bundle(out/'CURRENT_GOAL_ENTRY');external={k:bundle['trace'][k]for k in ['states','controls','memory','requests']}
 result=auditor.verify_goal(fresh,table,bundle,external,time.monotonic()+100)
 bad=copy.deepcopy(external);bad['controls']=bad['controls'].copy();bad['controls'][0,0]+=.01
 try:auditor.verify_goal(fresh,table,bundle,bad,time.monotonic()+100)
 except AssertionError:pass
 else:raise AssertionError('TAMPERED_EXTERNAL_CTRL_ACCEPTED')
 result.update(passed=True,models=0,new_mujoco_native=0,actual_live_adapter=True,real_saved_causal_rays=True,not_physical_acceptance=True,negative_external_ctrl_rejected=True,wall_s=time.monotonic()-start,entry_native=v.begin,analytical_python_native=v.count-v.begin)
 dump(O/'LIVE_ADAPTER_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':
 try:main()
 except BaseException as e:dump(O/'LIVE_QUALIFICATION_02_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,unfinished_analytical_unknown=True));raise
