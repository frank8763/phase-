"""RP-CCR learned candidate seam with the unchanged complete-tail safety gate.

Body-command adaptation is new; it does NOT reinterpret the old normalized
wheel residual as an actuator control. The historical steering gain .45*.12
is used for the bounded virtual-steering proposal. This module never writes
ctrl/qpos, calls an integrator, or declares goal success.
"""
import math,sys,importlib.util
from pathlib import Path
import numpy as np
from policy import SACProposer
from observation import assemble
R=Path(__file__).resolve().parents[2];CAP=.42722137342572125
class ShieldedSAC:
 def __init__(self):self.policy=SACProposer();self.counts=dict(proposed=0,admitted=0,rejected=0,executed=0)
 def propose(self,setup,packet,source,blocks,measurement_native_tick,nominal_request,prefix_native=5):
  assert 1<=prefix_native<=125,'BOUNDED_PROPOSAL_PREFIX';obs=assemble(blocks,self.policy.base,packet['native_tick'],measurement_native_tick);proposal=self.policy.predict(obs);self.counts['proposed']+=1
  v,w,stale=nominal_request;assert not stale and v>=0,'FORWARD_NOMINAL_REQUIRED';normalized=np.asarray(proposal['combined_normalized_action']);steer=0. if abs(v)<.005 else math.atan(.6*w/v);target=float(np.clip(steer+.054*normalized[0],-CAP,CAP));speed=float(np.clip(v*(1+.08*normalized[1]),0.,.08));request=[speed,speed*math.tan(target)/.6,False]
  folder=R/'experiments/v1067_causal_replan_brake_reserve';sys.path.insert(0,str(folder));spec=importlib.util.spec_from_file_location('v1070_original_full_tail_gate',folder/'fresh.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  requests=np.vstack([np.tile(request,(prefix_native,1)),np.zeros((2200,3))])
  try:certificate=module.finite_plan(setup,packet,source,requests,'SAC_PROPOSAL_PLUS_UNCHANGED_COMPLETE2200_STOP');accepted=bool(certificate['passed']);error=None
  except AssertionError as e:certificate=None;accepted=False;error=repr(e)
  self.counts['admitted'if accepted else'rejected']+=1
  return dict(proposal=proposal,request=request,admitted=accepted,certificate=certificate,error=error,executed=False,functional_goal_success=False,counts=dict(self.counts),observation_native_tick=measurement_native_tick,complete_stop_native=2200,training_updates=0)

 def propose_goal_profile(self,setup,packet,source,blocks,measurement_native_tick,nominal_requests,goal_xy,prefix_native=5):
  """A learned prefix may replace nominal input only with a full goal certificate."""
  obs=assemble(blocks,self.policy.base,packet['native_tick'],measurement_native_tick);proposal=self.policy.predict(obs);rr=np.asarray(nominal_requests,float);assert rr.ndim==2 and rr.shape[1]==3 and len(rr)>=prefix_native+2200,'COMPLETE_GOAL_PROFILE_REQUIRED';assert np.array_equal(rr[-2200:],np.zeros((2200,3))),'UNCHANGED_COMPLETE_STOP_REQUIRED'
  n=proposal['combined_normalized_action'];candidate=rr.copy()
  for i in range(prefix_native):
   v,w,stale=rr[i];assert not stale and v>=0,'FORWARD_NOMINAL_REQUIRED';target=0. if abs(v)<.005 else math.atan(.6*w/v);target=float(np.clip(target+.054*n[0],-CAP,CAP));speed=float(np.clip(v*(1+.08*n[1]),0.,.08));candidate[i]=[speed,speed*math.tan(target)/.6,False]
  folder=R/'experiments/v1067_causal_replan_brake_reserve';sys.path.insert(0,str(folder));spec=importlib.util.spec_from_file_location('v1070_goal_retaining_original_gate',folder/'fresh.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  self.counts['proposed']+=1
  try:
   certificate=module.finite_plan(setup,packet,source,candidate,'SAC_PREFIX_RETAINED_COMPLETE_GOAL_REFERENCE');upper=float(np.linalg.norm(np.asarray(certificate['state_path'][-1])[:2]-goal_xy))+.08;accepted=bool(certificate['passed']and upper<=.45);error=None
  except AssertionError as e:certificate=None;upper=None;accepted=False;error=repr(e)
  self.counts['admitted'if accepted else'rejected']+=1
  return dict(proposal=proposal,admitted=accepted,certificate=certificate,error=error,goal_upper_m=upper,executed=False,functional_goal_success=False,complete_goal_source=accepted,actual_vehicle_goal_success=False,counts=dict(self.counts),training_updates=0)
