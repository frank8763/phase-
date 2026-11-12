import sys,importlib.abc,json
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C));from recovery_source import forecast_packet;from static_source import renew
x=json.loads((O/'EW_PREEMPTIVE_STOP_INPUT.json').read_text());s=np.array(x['complete_state_path']);ss,uu,rr,mm=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=2200)],tail=False);assert np.max(abs(ss-s))==0.;p=forecast_packet(x['packet'],ss[-1],mm[-1],2200);goal=[-4.,-2.];plan=renew(x['setup'],p,goal,wall_s=12.,max_expansions=20000);dump(O/'EW_STATIC_RENEWAL_SOURCE.json',plan);print(json.dumps({k:v for k,v in plan.items()if k not in ['state_path','predicted_actuator_controls','planned_body_requests','actions','nominal_brake_preview_checks','packet']}),flush=True)
