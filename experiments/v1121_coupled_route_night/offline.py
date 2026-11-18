"""Preregistered development-state feasibility sweep; zero physical models."""
import sys,json,time,traceback,importlib.abc,signal
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch'}:raise AssertionError('NO_OFFLINE_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(C));from night_planner import plan
from source import solve,python_replay,initial,final_gate,COUNTS,SourceRefusal
import numpy as np

def main():
 job=json.loads(Path(sys.argv[1]).read_text());out=Path(job['output']);out.mkdir(parents=True,exist_ok=False);start=time.monotonic();answer={'passed':False,'models':0,'physical_integrations':0,'training_updates':0,'new_measurements':0,'scope':'development feasibility, never confirmation denominator'}
 try:
  x=json.loads(Path(job['input']).read_text());x['goal_yaw']=float(x['setup']['case']['yaw'])+job['goal_heading_offset'];p=plan(x,out/'planner',job['radius_extra']);answer['planner_passed']=p['passed']
  if p['passed']:
   result=solve(x,p['path'],p['gear']);answer.update({k:v for k,v in result.items()if k not in ['states','controls','requests']})
   if result['passed']:
    ss,uu,*_=python_replay(x['setup'],initial(x['packet']),result['rows']);COUNTS['python_native']+=len(uu);err=max(float(abs(ss-result['states']).max()),float(abs(uu-result['controls']).max()));proof,_=final_gate(x,ss,uu,result['rows']);assert err<=1e-8 and proof['passed'],'INDEPENDENT_OFFLINE_SOURCE_ANOMALY';answer.update(independent_proof=proof,maximum_model_error=err)
 except BaseException as e:answer.update(passed=False,error=repr(e),traceback=traceback.format_exc(),hard_anomaly=isinstance(e,AssertionError)and str(e)not in ['SMAC_ROTATION_IN_PLACE','DEGENERATE_OFFICIAL_PATH'])
 answer.update(closed=True,wall_s=time.monotonic()-start,counts=COUNTS,job=job);(out/'RESULT.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps({k:v for k,v in answer.items()if k not in ['rows','selected_z','iterations']}),flush=True)
if __name__=='__main__':main()
