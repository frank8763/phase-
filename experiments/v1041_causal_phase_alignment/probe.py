"""Fixed original forward suffix versus 200 public waiting phases; zero models."""
import importlib.abc,importlib.util,json,math,signal,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1041_causal_phase_alignment'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1023_dense_input_route'))
from whole_input import Predictor,PARAMETERS,initial,checks
from geometry_model import ref,REQUIRED

def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
# Bind exact original forward Predictor above before the signed module inserts imports.
timed=load('v1041_existing_interval_geometry',R/'experiments/v1035_signed_timed_input_source/timed_input.py')
gate=load('v1041_conservative_cut',R/'experiments/v1033_saved_task_diagnosis/contract_gate.py')

def predict(setup,packet,requests):
 p=Predictor(setup,initial(packet),PARAMETERS);states=[p.state.copy()];ctrl=[]
 for request in requests:s,u=p.step(*request);states.append(s);ctrl.append(u)
 return np.asarray(states),np.asarray(ctrl)

def main():
 assert not (O/'RESULT.json').exists();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('180S_SOURCE_CAP')));signal.alarm(180);start=time.monotonic()
 x=json.loads((R/'runs/v1040_approach_information_audit/REBUILT_SOURCE.json').read_text());packet=x['packet'];source=x['source'];setup=x['setup'];goal=np.asarray(x['goal']);ref.snapshot_state(packet,source,packet['body_measured_at'])
 full=ref._old.Geometry(setup['known'],source['periodic']);cut=gate.select_contract(setup['known'],full.center_polygon,np.asarray(packet['body'][:2]),goal,REQUIRED);(O/'FULL_CYCLE_CUT.json').write_text(json.dumps(cut,indent=2)+'\n')
 original=json.loads((R/'runs/v858_nav2_verified/v1024/dynamic_we/STATIC_COMPLETE_PLAN.json').read_text());suffix=np.asarray(original['planned_body_requests'][19040:],float)
 assert len(suffix)>200 and np.array_equal(suffix[-200:],np.zeros((200,3))) and np.isin(suffix[:,0],[0.,.03]).all();ss,uu=predict(setup,packet,suffix)
 geometry=timed.Geometry(setup['known'],source['periodic'],packet['sim_time']);ticks=np.arange(len(ss));trials=[];best=None
 for slot in range(200):
  wait=int(round(slot*geometry.period/.01/200));low=geometry.clearances(ss[:,:3],ticks+wait,.005);i=int(low.argmin());row=dict(slot=slot,wait_ticks=wait,minimum_timed_raw_m=float(low[i]),bottleneck_native_offset=i+wait,bottleneck_pose=ss[i,:3].tolist(),goal_upper_m=float(np.linalg.norm(ss[-1,:2]-goal))+.08)
  trials.append(row)
  if best is None or row['minimum_timed_raw_m']>best['minimum_timed_raw_m']:best=row
 (O/'PHASE_CANDIDATES.json').write_text(json.dumps(trials,indent=2)+'\n')
 wait=best['wait_ticks'];requests=np.vstack([np.zeros((wait,3)),suffix]);states,controls=predict(setup,packet,requests);low=geometry.clearances(states[:,:3],np.arange(len(states)),.005);minimum=float(low.min());cc,upper=checks(states,controls,requests,packet,setup,goal,minimum,REQUIRED);a,b=full.clearances(states[-1:,:3]);cc['terminal_full_cycle_hold']=float(min(a[0],b[0]))>=REQUIRED
 i=int(low.argmin());result=dict(passed=all(cc.values()),checks=cc,best_proposal=best,minimum_exact_timed_raw_m=minimum,exact_bottleneck_native_offset=i,exact_bottleneck_pose=states[i,:3].tolist(),source_native_tick=packet['native_tick'],candidate_count=200,selected_wait_ticks=wait,input_steps=len(requests),terminal_goal_upper_m=upper,models=0,integrations=0,physical_ready=False,actuation_authority=False,wall_s=time.monotonic()-start,scope='FIXED_ORIGINAL_FORWARD_SUFFIX_WAIT_PHASE_ONLY')
 (O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 if result['passed']:(O/'QUALIFIED_PLAN.json').write_text(json.dumps(dict(result,packet=packet,source=source,state_path=states.tolist(),planned_body_requests=requests.tolist(),predicted_actuator_controls=controls.tolist()),indent=2)+'\n')
 signal.alarm(0);print(json.dumps(result))
if __name__=='__main__':main()
