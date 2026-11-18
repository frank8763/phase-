"""Fixed real saved refusal, new complete-source contract and independent model."""
import sys,json,time,importlib.abc,signal
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1121_coupled_route_night'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(C));from source import solve,python_replay,initial,final_gate,digest,COUNTS
import numpy as np

def main():
 assert not(O/'SOURCE_QUALIFICATION.json').exists();x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());p=json.loads((R/'runs/v1107_reference_frame_alignment/PATH_GEARS.json').read_text());seed=json.loads((R/'runs/v1120_explicit_timing_seed/OPTIMIZATION.json').read_text())['z'];start=time.monotonic()
 # Explicit saved development seed only. Live solver must not read this file.
 result=solve(x,p['path'],p['gear'],seed=seed);ss,uu,*_=python_replay(x['setup'],initial(x['packet']),result['rows']);COUNTS['python_native']+=len(uu);error=max(float(abs(ss-result['states']).max()),float(abs(uu-result['controls']).max()));assert error<=1e-8
 proof,rr=final_gate(x,ss,uu,result['rows']);np.savez_compressed(O/'QUALIFIED_SOURCE.npz',states=ss,controls=uu,requests=rr);answer={k:v for k,v in result.items()if k not in ['states','controls','requests']};answer.update(passed=bool(proof['passed']and error<=1e-8),independent_proof=proof,cpp_python_error=error,counts=COUNTS,models=0,physical_integrations=0,wall_s=time.monotonic()-start,seed_scope='saved development only, forbidden as live policy',old_failed_geometric_contract_unchanged=True);(O/'SOURCE_QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps({k:v for k,v in answer.items()if k not in ['rows','iterations','selected_z']}),flush=True)
if __name__=='__main__':main()
