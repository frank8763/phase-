import sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1023_dense_input_route'))
from whole_input import Predictor,PARAMETERS,initial
from geometry_model import ref,REQUIRED

def plan(packet,source,setup,requests):
 ref.snapshot_state(packet,source,packet['body_measured_at']);requests=np.asarray(requests,float)
 assert packet['dynamic_discovered']is True and requests.shape==(6900,3)and np.isfinite(requests).all(),'INVALID_COMPONENT_SOURCE_OR_INPUT'
 engine=Predictor(setup,initial(packet),PARAMETERS);states=[engine.state.copy()];controls=[]
 for request in requests:s,u=engine.step(*request);states.append(s);controls.append(u)
 states=np.asarray(states);controls=np.asarray(controls);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(states[:,:3]);minimum=float(np.minimum(a,b).min());limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01
 checks=dict(exact_request_count=len(requests)==6900,original_forward_domain=bool(np.isin(requests[:,0],[0.,.03]).all()and(requests[:,2]==0).all()),all_native_full_cycle_geometry=minimum>=REQUIRED,all_2400_final_zero_inputs=bool((requests[-2400:]==0).all()),complete_stop=bool(abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03),body_caps=bool(abs(states[:,3]).max()<=.13 and abs(states[:,5]).max()<=.16 and abs(states[:,4]).max()<=.03),legal_ctrl=bool((controls>=limits[:,0]-1e-10).all()and(controls<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([packet['controller_memory']['last_ctrl'],controls]),axis=0))<=rates+1e-10).all()),predicted_displacement_at_least_1m=float(np.linalg.norm(states[-1,:2]-states[0,:2]))>=1.)
 return dict(passed=all(checks.values()),checks=checks,state_path=states.tolist(),planned_body_requests=requests.tolist(),predicted_actuator_controls=controls.tolist(),minimum_full_cycle_raw_m=minimum,required_raw_m=REQUIRED,source_native_tick=source['source_native_tick'],predicted_displacement_m=float(np.linalg.norm(states[-1,:2]-states[0,:2])),terminal_pose=states[-1,:3].tolist(),scope='FULL_CERTIFIED_FINITE_OBSERVATION_APPROACH_ONLY',original_goal_arrival_claim=False,models=0,integrations=0)

