"""Reproduce the exact V1082 rejected command from14 saved steps, no physics."""
import sys,json,math,importlib.util,importlib.abc
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/navigation_review_20261112'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_PHYSICAL_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1082_guarded_saved_continuation'));from common import paths
paths();from resource_policy import apply
apply();import numpy as np
from science import Predictor,initial,PARAMETERS
from governor import P

def main():
 out=R/'runs/v858_nav2_verified/v1082/remaining3555';inp=json.loads((out/'ACTUAL_INPUT.json').read_text());setup=inp['setup'];z=np.load(out/'physics/NATIVE_TRACE.npz');cmd=np.asarray(json.loads((out/'physics/BODY_COMMANDS.json').read_text()));plan=np.load(out/'PLAN.npz');hist=18074;p=Predictor(setup,initial(inp['packet']),PARAMETERS);rows=[];ce=0.
 def observe(i):
  enc=np.r_[z['qpos'][i-1,setup['steering_qpos_addresses']],z['qvel'][i-1,setup['steering_qvel_addresses']]];p.adapter.encoders=lambda enc=enc:enc
 for i in range(hist,len(cmd)):
  observe(i);c=cmd[i];u=p.adapter.compute(float(c[1]),float(c[2]),float(c[3]),float(c[4]),bool(c[5]));ce=max(ce,float(abs(u-z['ctrl'][i,setup['actuator_ids']]).max()));g=p.adapter.last_speed_projection;rows.append(dict(native=i+1,limited=bool(g['limited']),common=float(u[2:].mean()),predicted_next_upper=g['offset']+g['gain']*g['common']+g['reserve'],actual_speed_next=None))
 q=z['qpos'];vv=z['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));speed=vv[:,0]*np.cos(yaw)+vv[:,1]*np.sin(yaw)
 for j,row in enumerate(rows):row['actual_speed_next']=float(speed[hist+j])
 observe(len(cmd));n=len(cmd)-hist;req=plan['requests'][n];capture={}
 def trace(frame,event,arg):
  if event=='exception'and frame.f_code.co_filename.endswith('v1081_transient_speed_guard/governor.py'):
   for name in ['offset','gain','target','lo','hi','feasible']:
    if name in frame.f_locals:capture[name]=bool(frame.f_locals[name])if name=='feasible'else float(frame.f_locals[name])
  return trace
 before_memory=p.adapter.last.copy();before_integral=p.adapter.integral;error=None;sys.settrace(trace)
 try:p.adapter.compute(float(req[0]),float(req[1]),float(speed[-1]),float(vv[-1,5]),bool(req[2]))
 except AssertionError as e:error=str(e)
 finally:sys.settrace(None)
 assert error=='NO_SLEW_LEGAL_SPEED_PROJECTION'and ce<=1e-10 and capture['lo']>capture['hi'],'EXACT_FAILURE_NOT_REPRODUCED'
 result=dict(reproduced=True,rejected_command_local=n+1,executed_new=n,unexecuted_new=3555-n,original_owner_ctrl_error=ce,actual_longitudinal_speed_at_rejection=float(speed[-1]),minimum_legal_next_speed_upper=capture['offset']+capture['gain']*capture['lo']+P['empirical_one_step_error_reserve'],configured_next_upper=P['projected_speed_cap'],rejection=capture,rejected_proposal_mutates_adapter_memory=bool(np.max(abs(p.adapter.last-before_memory))>1e-12 or abs(p.adapter.integral-before_integral)>1e-12),adapter_last_change_without_native=float(np.max(abs(p.adapter.last-before_memory))),adapter_integral_change_without_native=float(p.adapter.integral-before_integral),rows=rows,physical_models=0,physical_integrations=0,scope='Actual production governor on exact saved causal encoder/body/control memory input; failure reproduced without plant')
 (O/'LATEST_REJECTION_REPRODUCED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))
 if '--require-feasible'in sys.argv:assert error is None,'V1082_SAVED_TRANSIENT_IS_NOT_RECURSIVELY_FEASIBLE'
if __name__=='__main__':main()
