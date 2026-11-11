"""Production asynchronous executor with metadata-only plant, no vehicle load."""
import copy,importlib.abc,json,math,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1053_parked_refresh_handoff';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import Predictor,initial,PARAMETERS,dump
from execute import execute,ProcessJob,HOLD_NATIVE
def main():
 x=json.loads((R/'runs/v1051_retained_corridor_entry/INPUT_SOURCE.json').read_text());original=json.loads((R/'runs/v1051_retained_corridor_entry/SELECTED_PLAN.json').read_text());original['goal']=x['goal'];packet=x['packet'];setup=x['setup']
 class Plant:
  def __init__(self):self.p=Predictor(setup,initial(packet),PARAMETERS);self.count=23640;self.adapter=self.p.adapter;self.requests=[]
  def step(self,*request):self.p.step(*request);self.count+=1;self.requests.append(list(request))
  def body(self):s=self.p.state;return [*s[:4],s[5]]
  def steering_sample(self):s=self.p.state;k=math.tan(s[6])/.6;front=np.array([math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]);kd=(1+math.tan(s[6])**2)/.6*s[7];rates=.6*kd/(np.array([1-.27*k,1+.27*k])**2+(np.array([.6*k,.6*k]))**2);return np.r_[front,rates]
  def scan(self):return dict(native_tick=self.count)
 def measured(v,discovered):
  enc=v.steering_sample();now=time.monotonic();return dict(body=list(v.body()),native_tick=v.count,sim_time=packet['sim_time']+(v.count-23640)*.01,body_measured_at=now,sent_at=now,dynamic_discovered=True,steering=dict(position=enc[:2].tolist(),velocity=enc[2:].tolist(),native_tick=v.count,measured_at=now),controller_memory=dict(last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral)))
 class Evidence:
  def update(self,scan):pass
  def source(self,v):return dict(source_native_tick=v.count,source_age_s=0.,decision_at=time.monotonic(),periodic=copy.deepcopy(x['source']['periodic']))
 # The real subprocess is intentionally not given enough hold time in this
 # case. It must be killed without ever receiving an actuator interface.
 early=O/'software_producer_deadline';early.mkdir();plant=Plant()
 try:execute(plant,setup,original,time.time()+300,Evidence(),early,measured,pace=False)
 except AssertionError as e:assert str(e)=='SOURCE_MISSED_FIXED_HOLD_DEADLINE',str(e)
 else:raise AssertionError('SOURCE_DEADLINE_NOT_REJECTED')
 assert len(plant.requests)==HOLD_NATIVE and np.array_equal(np.array(plant.requests),np.zeros((HOLD_NATIVE,3)));negative=dict(passed=True,native_metadata_steps=len(plant.requests),moving_commands=0,no_model_loaded=True);dump(early/'RESULT.json',negative)
 full=O/'software_full_executor';full.mkdir();plant=Plant();started=time.monotonic();result=execute(plant,setup,original,time.time()+600,Evidence(),full,measured,pace=True);goal=float(np.linalg.norm(np.asarray(plant.body()[:2])-x['goal']));assert goal<=.45 and np.linalg.norm(plant.body()[3:])<=.03;segments=json.loads((full/'EXECUTION_SEGMENTS.json').read_text());cursor=23640
 for segment in segments:assert segment['start_native']==cursor;cursor+=segment['executed_native']
 assert cursor==plant.count;result.update(passed=True,goal_distance_m=goal,software_metadata_dynamics_only=True,actual_physics_native=0,models=0,integrations=0,wall_s=time.monotonic()-started,no_model_imports=True,deadline_negative=negative);dump(O/'EXECUTOR_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
