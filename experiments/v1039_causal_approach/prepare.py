"""One fixed certified observation approach, original .03 controller only."""
import importlib.abc,json,sys,hashlib
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1039_causal_approach'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path[:0]=[str(R/'experiments/v1023_dense_input_route'),str(R/'experiments/v1024_full_route_execution')]
from whole_input import Predictor,PARAMETERS,initial
from geometry_model import ref,REQUIRED

def plan(packet,source,setup,requests):
 engine=Predictor(setup,initial(packet),PARAMETERS);states=[engine.state.copy()];controls=[]
 for request in requests:s,u=engine.step(*request);states.append(s);controls.append(u)
 states=np.asarray(states);controls=np.asarray(controls);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(states[:,:3]);minimum=float(np.minimum(a,b).min());limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01
 checks=dict(exact_request_count=len(requests)==6900,original_forward_domain=bool(np.isin(requests[:,0],[0.,.03]).all()and(requests[:,2]==0).all()),all_native_full_cycle_geometry=minimum>=REQUIRED,all_2400_final_zero_inputs=bool((requests[-2400:]==0).all()),complete_stop=bool(abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03),body_caps=bool(abs(states[:,3]).max()<=.13 and abs(states[:,5]).max()<=.16 and abs(states[:,4]).max()<=.03),legal_ctrl=bool((controls>=limits[:,0]-1e-10).all()and(controls<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([packet['controller_memory']['last_ctrl'],controls]),axis=0))<=rates+1e-10).all()),predicted_displacement_at_least_1m=float(np.linalg.norm(states[-1,:2]-states[0,:2]))>=1.)
 return dict(passed=all(checks.values()),checks=checks,state_path=states.tolist(),planned_body_requests=requests.tolist(),predicted_actuator_controls=controls.tolist(),minimum_full_cycle_raw_m=minimum,required_raw_m=REQUIRED,source_native_tick=source['source_native_tick'],predicted_displacement_m=float(np.linalg.norm(states[-1,:2]-states[0,:2])),terminal_pose=states[-1,:3].tolist(),scope='FULL_CERTIFIED_FINITE_OBSERVATION_APPROACH_ONLY',original_goal_arrival_claim=False,models=0,integrations=0)

def main():
 p=R/'runs/v858_nav2_verified/v1024/dynamic_we';row=json.loads((p/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((p/'physics/SETUP.json').read_text());static=json.loads((p/'STATIC_COMPLETE_PLAN.json').read_text());first=json.loads((p/'STATIC_EXECUTION.json').read_text())['end_native'];assert first==14540 and row['packet']['native_tick']==16740
 requests=np.vstack([np.asarray(static['planned_body_requests'])[first:first+4500],np.zeros((2400,3))]);result=plan(row['packet'],row['source'],setup,requests)
 (C/'REQUESTS.json').write_text(json.dumps(requests.tolist(),separators=(',',':'))+'\n');(O/'SOURCE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['state_path','planned_body_requests','predicted_actuator_controls']}));assert result['passed']
 task=dict(task_id='original_we_observation_approach',run_id='v1039-original-we-approach',case_id='WEST_EAST',seed=10010001,phase=.6573753567727383,dynamic=True,goal_xy=[4.,-2.],output=str(R/'runs/v858_nav2_verified/v1039/approach'),historical_native=16740,new_component_native=6900)
 (C/'TASK.json').write_text(json.dumps(task,indent=2)+'\n')
if __name__=='__main__':main()
