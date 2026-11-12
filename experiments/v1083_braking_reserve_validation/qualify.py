"""Fixed saved feedback tests and nominal whole-goal revalidation, zero plant."""
import sys,json,math,importlib.abc,copy
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1083_braking_reserve_validation';CORE=R/'experiments/rpccr_execution_core'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1082_guarded_saved_continuation'));from common import paths
paths();from resource_policy import apply
apply();import numpy as np
from kernel import PARAMETERS,Geometry,REQUIRED,checks,virtual,load
sys.path.insert(0,str(CORE));from prediction import Predictor,initial
from braking_reserve import Adapter,ERROR_RESERVE
REC=R/'records/nav2_v1077_v1078_20261112/v1079_dual_steering_qualification';inp=json.loads((REC/'REMAINDER_INPUT.json').read_text());setup=inp['setup'];packet=inp['packet'];source=inp['source'];rr=np.load(REC/'REMAINDER_SOURCE.npz')['requests']
def simulate(packet,requests,errors=None):
 p=Predictor(setup,initial(packet),PARAMETERS);ss=[p.state.copy()];uu=[];cert=[]
 for i,r in enumerate(requests):
  s,u=p.step(*r)
  if errors is not None:p.state[3]+=float(errors[i]);s=p.state.copy()
  ss.append(s);uu.append(u);cert.append(copy.deepcopy(p.adapter.last_braking_reserve))
 return np.array(ss),np.array(uu),cert
s,u,proofs=simulate(packet,rr);low=Geometry(setup['known'],source['periodic'],packet['sim_time']).complete(s);cc,goal=checks(s,u,rr,packet,setup,np.array(setup['case']['goal_xy']),low,REQUIRED);cc={k:bool(v)for k,v in cc.items()};np.savez_compressed(O/'COMPLETE_CANDIDATE.npz',states=s,controls=u,requests=rr)
# Exact recorded V1082 latest state: old guard rejects and mutates; new must
# accept nominal or legitimate braking, or reject without changing any memory.
new=R/'runs/v858_nav2_verified/v1082/remaining3555';z=np.load(new/'physics/NATIVE_TRACE.npz');cmd=np.array(json.loads((new/'physics/BODY_COMMANDS.json').read_text()));engine=Predictor(setup,initial(packet),PARAMETERS)
for i in range(18074,len(cmd)):
 # Preserve exact historical controller memory for this probe, not simulated new controls.
 enc=np.r_[z['qpos'][i-1,setup['steering_qpos_addresses']],z['qvel'][i-1,setup['steering_qvel_addresses']]];engine.adapter.encoders=lambda enc=enc:enc
 from governor import Adapter as Old
 old=copy.copy(engine.adapter);old.__class__=Old;old.last=engine.adapter.last.copy();old.compute(*cmd[i,[1,2,3,4,5]]);engine.adapter.last=old.last.copy();engine.adapter.integral=old.integral
enc=np.r_[z['qpos'][-1,setup['steering_qpos_addresses']],z['qvel'][-1,setup['steering_qvel_addresses']]];engine.adapter.encoders=lambda:enc;q=z['qpos'][-1];v=z['qvel'][-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));mv=float(v[0]*math.cos(yaw)+v[1]*math.sin(yaw));memory=engine.adapter.last.copy();integ=engine.adapter.integral;rejection=None
try:engine.adapter.compute(.125,0.,mv,float(v[5]));latest_accepted=True
except AssertionError as e:rejection=str(e);latest_accepted=False;assert np.array_equal(memory,engine.adapter.last)and integ==engine.adapter.integral,'REJECTED_PROPOSAL_MUTATED_MEMORY'
# Closed-loop sampled perturbations exercise actual feedback, actuator memory
# and the governor repeatedly; these are analytical tests, never MuJoCo.
patterns={'nominal':np.zeros(len(rr)),'positive':np.full(len(rr),.002),'negative':np.full(len(rr),-.002),'alternating':np.where(np.arange(len(rr))%2,.002,-.002)};feedback=[]
for name,e in patterns.items():
 try:
  a,b,c=simulate(packet,rr,e);feedback.append(dict(name=name,passed=bool(abs(a[:,3]).max()<=.13+1e-10),maximum_speed=float(abs(a[:,3]).max()),minimum_speed=float(a[:,3].min()),backup_count=sum(x is not None and x.get('backup_selected',False)for x in c)))
 except AssertionError as error:feedback.append(dict(name=name,passed=False,error=str(error)))
# Invalid sample must be a pure rejected transaction.
p=Predictor(setup,initial(packet),PARAMETERS);before=p.adapter.last.copy();mi=p.adapter.integral;p.adapter.encoders=lambda:np.full(4,np.nan)
try:p.adapter.compute(.125,0.,.12,0.);pure_reject=False
except AssertionError:pure_reject=np.array_equal(before,p.adapter.last)and p.adapter.integral==mi
result=dict(passed=all(cc.values())and all(x['passed']for x in feedback)and pure_reject,complete_plan_checks=cc,minimum_raw=low,goal_upper=goal,maximum_nominal_speed=float(abs(s[:,3]).max()),latest_saved_state_accepted=latest_accepted,latest_rejection=rejection,rejection_memory_is_transactional=True,invalid_encoder_rejection_pure=bool(pure_reject),closed_loop_perturbation_cases=feedback,original_request_sequence_unchanged=True,models=0,integrations=0,empirical_speed_envelope_only=True);(O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
# Reuse the actual two moving-return tests only after all-control equality.
extra=[]
for task in ['turn_left','turn_right']:
 out=R/'runs/v858_nav2_verified/v1080'/task;data=np.load(out/'physics/NATIVE_TRACE.npz');commands=np.asarray(json.loads((out/'physics/BODY_COMMANDS.json').read_text()));ip=json.loads((out/'ACTUAL_INPUT.json').read_text());p=Predictor(setup,initial(ip['packet']),PARAMETERS);err=0.
 for i,c in enumerate(commands):
  enc=np.r_[setup['initial_steering_position'],setup['initial_steering_velocity']]if i==0 else np.r_[data['qpos'][i-1,setup['steering_qpos_addresses']],data['qvel'][i-1,setup['steering_qvel_addresses']]];p.adapter.encoders=lambda enc=enc:enc;u=p.adapter.compute(*c[[1,2,3,4,5]]);err=max(err,float(abs(u-data['ctrl'][i,setup['actuator_ids']]).max()))
 extra.append(dict(case=task,maximum_control_error=err,passed=err<=1e-10))
Old=load('reserve_unmodified_old_branch',R/'experiments/v1079_dual_steering_qualification/steering_model.py').Predictor;p=Old(setup,initial(packet),PARAMETERS);q=Predictor(setup,initial(packet),PARAMETERS);exact=0.
for v,w in [(0.,0.)]*100+[(.03,.005)]*100+[(.08,0.)]*100+[(0.,0.)]*2200:
 a,u=p.step(v,w);b,z=q.step(v,w);exact=max(exact,float(abs(a-b).max()),float(abs(u-z).max()))
# Deliberately infeasible state verifies rejection remains a pure transaction.
p=Predictor(setup,initial(packet),PARAMETERS);mem=p.adapter.last.copy();integ=p.adapter.integral
try:p.adapter.compute(.125,0.,.14,0.);rejected=False
except AssertionError:rejected=True
transaction=bool(rejected and np.array_equal(mem,p.adapter.last)and p.adapter.integral==integ);r=dict(passed=all(x['passed']for x in extra)and exact==0 and transaction,reused_actual=extra,original_branch_max_error=exact,infeasible_rejection_preserves_memory=transaction,models=0,integrations=0);(O/'REGRESSION.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
