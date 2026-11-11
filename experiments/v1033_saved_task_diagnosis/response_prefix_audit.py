"""Reconstruct all executed V1032 inputs; never upgrade the failed full gate."""
import importlib.abc,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1027_timed_speed_source'))
from whole_input import Predictor,PARAMETERS,virtual

def main():
 rows=[]
 for name in ['straight','left']:
  out=R/'runs/v858_nav2_verified/v1032'/name;result=json.loads((out/'RESULT.json').read_text());setup=json.loads((out/'physics/SETUP.json').read_text());plan=json.loads((out/'REGENERATED_PROFILE.json').read_text());d=np.load(out/'physics/NATIVE_TRACE.npz');commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());n=len(commands)
  p=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);maximum=0.
  for command,actual in zip(commands,d['ctrl']):
   _,v,w,mv,mw,stale=command;u=p.adapter.compute(v,w,mv,mw,stale);maximum=max(maximum,float(abs(u-actual[setup['actuator_ids']]).max()))
  existing=json.loads((out/'EXECUTED_PREFIX_AUDIT.json').read_text());expected=np.asarray(plan['planned_body_requests'])[:n];actual=np.asarray([[r[1],r[2],float(r[5])]for r in commands]);q=d['qpos'];qv=d['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));speed=qv[:,0]*np.cos(yaw)+qv[:,1]*np.sin(yaw)
  existing['checks'].update(all_native_controller_reconstructed=maximum<=1e-10,exact_registered_request_prefix=bool(np.array_equal(actual,expected)),body_speed_cap=float(abs(speed).max())<=.13,body_yaw_cap=float(abs(qv[:,5]).max())<=.16)
  existing.update(passed=all(existing['checks'].values()),maximum_actual_controller_reconstruction_error=maximum,failed_functional_gate_preserved=name=='left'and result['passed']is False)
  (out/'EXECUTED_PREFIX_AUDIT.json').write_text(json.dumps(existing,indent=2)+'\n');assert existing['passed'];rows.append(dict(task_id=name,**existing))
 result=dict(passed=all(x['passed']for x in rows),rows=rows,models=0,integrations=0,full_speed_response_qualification_passed=False,original_dynamic_acceptance=False)
 (R/'runs/v1033_saved_task_diagnosis/ALL_EXECUTED_RESPONSE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],rows=[dict(task_id=r['task_id'],native=r['executed_native'],controller_error=r['maximum_actual_controller_reconstruction_error'])for r in rows])))
if __name__=='__main__':main()
