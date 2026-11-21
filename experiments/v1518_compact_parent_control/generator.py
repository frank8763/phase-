"""One exact current origin, all200braking alternatives before every request."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time
import traceback
C=Path(__file__).resolve().parent;R=C.parents[1]
s=importlib.util.spec_from_file_location('v1497_response_model_bridge',C/'model_bridge.py');bridge=importlib.util.module_from_spec(s);s.loader.exec_module(bridge)

def generate(current,proposal,setup,*,authority,lock,save_branch,save_origin):
 # No executable owner/admission is supplied by this draft.
 identity=bridge.authorize(current,proposal,authority,lock)
 Predictor,initial,kernel,Adapter,Gear,Policy,feedback,Geometry,causal=bridge.binding()
 import numpy as np
 known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text());assert setup['known']==known
 forecast=causal(current['causal_snapshot'],current_native=current['fixed_origin_native'],current_sim_time=current['fixed_origin_sim_time']);assert forecast==current['causal_forecast']
 geometry=Geometry(known,[*forecast['center'],forecast['radius_m']]);origin=current['origin'];origin_tick=current['fixed_origin_native']
 end=min(authority['hard_stop_monotonic'],time.monotonic()+1800)
 result=dict(passed=False,closed=False,binding=identity,models_physical=0,analytical_native=0,analytical_inflight_unknown=False,explicit_predictor_constructions=0,branch_copies=0,nominal_native=0,complete_stop_branches=0,first_error=None,actual_control_admitted=False)
 arrays=dict(states=[],ctrl=[],journal=[],memory=[],modes=[]);partial=None;minimum_nominal=math.inf;minimum_stop=math.inf
 def advance(p,v,w):
  assert time.monotonic()<end and time.time()<min(authority['absolute_deadline_unix'],1795395600),'PRIEST_RESPONSE_DUAL_CLOCK_EXPIRED'
  assert result['analytical_native']<authority['maximum_analytical_native'],'PRIEST_RESPONSE_ANALYTICAL_CAP'
  result['analytical_inflight_unknown']=True;state,ctrl=p.step(v,w,False);result['analytical_native']+=1;result['analytical_inflight_unknown']=False;return state,ctrl
 def packet(p,tick):return bridge.current_packet(p,current=current,native_tick=tick,feedback=feedback)
 try:
  result['explicit_predictor_constructions']=None
  p=Predictor(setup,initial(origin),kernel.PARAMETERS);result['explicit_predictor_constructions']=1
  assert p.adapter.__class__ is Adapter;p.adapter.encoders=lambda owner=p:feedback.current(owner)
  p.adapter.parked_target=origin['parked_target'];p.adapter._steering_motion_active=origin['steering_motion_active']
  measured=packet(p,origin_tick)
  bridge.validate_origin(measured,current,p.state,save_origin=save_origin)
  method=Policy(current,proposal);gate=Gear()
  for key,value in current['gear_memory'].items():setattr(gate,key,value)
  arrays['states'].append(p.state.copy())
  for index in range(authority['maximum_nominal_native']):
   tick=origin_tick+index;before=packet(p,tick)
   # Actual current stop evidence is saved even if the next policy refuses.
   branch=copy.deepcopy(p);branch.adapter.encoders=lambda owner=branch:feedback.current(owner);branch.adapter.parked_target=None;result['branch_copies']+=1
   bs=[branch.state.copy()];bu=[]
   for j in range(200):
    state,ctrl=advance(branch,0.,0.);bs.append(state.copy());bu.append(ctrl.copy())
   stop_state=np.asarray(bs);stop_ctrl=np.asarray(bu);lower=float(geometry.tube(stop_state));minimum_stop=min(minimum_stop,lower)
   stop=packet(branch,tick+200)
   rest=bool(abs(stop['body_lateral'])<=.003 and max(abs(x)for x in stop['body'][3:])<=.003 and max(abs(x)for x in stop['steering']['velocity'])<=.03 and max(abs(x)for x in stop['controller_memory']['last_ctrl'][2:])<=1e-10)
   caps=bool((abs(stop_state[:,3:6])<=np.array([.13,.03,.16])+1e-8).all())
   proof=dict(before_native=tick,complete_native=200,causal_tube_lower_m=lower,rest=rest,body_caps=caps,current_input_sha256=current['input_sha256'],proposal_sha256=proposal['proposal_sha256'],geometry_kind='FULL_PERIOD_DISK',causal_snapshot_sha256=current['causal_snapshot_sha256'])
   save_branch(proof,stop_state,stop_ctrl);result['complete_stop_branches']+=1
   assert lower>=.22-1e-8 and rest and caps,'PRIEST_CURRENT_COMPLETE_STOP_REFUSED'
   selection=method.select(before,source_kind='PRIVATE_CURRENT_RESPONSE_PACKET');raw=selection['raw_request'];assert raw[2]is False
   vr,wr,gear=gate.select(*raw[:2],native_tick=tick,body=before['body'],last_ctrl=before['controller_memory']['last_ctrl'],encoders=[*before['steering']['position'],*before['steering']['velocity']])
   gear_memory=dict(gear=gate.gear,brake_start=gate.brake_start,last_tick=gate.last_tick)
   assert gear==selection['expected_gear_handoff']and [vr,wr,False]==selection['expected_request_after_original_gear']
   arrays['memory'].append([*p.adapter.last.tolist(),float(p.adapter.integral)]);arrays['modes'].append(dict(coupled_episode=p.coupled_episode,parked_target=p.adapter.parked_target,steering_motion_active=bool(p.adapter._steering_motion_active)))
   state,ctrl=advance(p,vr,wr);arrays['states'].append(state.copy());arrays['ctrl'].append(ctrl.copy());result['nominal_native']+=1
   # Record an applied action before post-state checks can refuse.
   arrays['journal'].append(dict(before_native=tick,selection=selection,requested=raw,admitted=[vr,wr,False],gear=gear,gear_memory_after=gear_memory,control_owner=selection['contribution_owner']))
   after=packet(p,tick+1);method.observe_applied(before_native=tick,gear_handoff=gear,gear_memory_after=gear_memory,after_packet=after)
   assert (abs(p.state[3:6])<=np.array([.13,.03,.16])+1e-8).all(),'PRIEST_NOMINAL_BODY_CAP'
   lower=float(geometry.tube(arrays['states'][-2:]));minimum_nominal=min(minimum_nominal,lower);assert lower>=.22-1e-8,'PRIEST_NOMINAL_TUBE_REFUSED'
   if method.complete:
    whole=float(geometry.tube(arrays['states']));last=arrays['journal'][-200:]
    checks=dict(full_Nplus1=len(arrays['states'])==len(arrays['ctrl'])+1,complete_current_stop_branches=result['complete_stop_branches']==len(arrays['ctrl']),whole_tube=whole>=.22-1e-8,full200_applied_tail=len(last)==200 and all(r['requested']==r['admitted']==[0.,0.,False]for r in last),policy_endpoint_and_rest=True,lateral_rest=abs(after['body_lateral'])<=.003)
    result.update(passed=all(checks.values()),checks=checks,whole_tube_m=whole,stop_reason='COMPLETE_FINITE_PRIEST_RESPONSE');break
  else:result['stop_reason']='FINITE_PRIEST_RESPONSE_NOMINAL_LIMIT'
 except BaseException as e:
  result.update(first_error=repr(e),traceback=traceback.format_exc(),stop_reason='CURRENT_PRIEST_RESPONSE_REFUSED_OR_EXCEPTION')
  if result['branch_copies']>result['complete_stop_branches']and 'bs'in locals():
   partial=dict(before_native=tick,states=bs,ctrl=bu,complete=False,inflight_unknown=result['analytical_inflight_unknown'],first_error=result['first_error'])
 finally:
  result.update(closed=True,source_unchanged=all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in authority['tested_source_hashes'].items()),minimum_nominal_tube_m=None if minimum_nominal==math.inf else minimum_nominal,minimum_stop_tube_m=None if minimum_stop==math.inf else minimum_stop)
  result['passed']=result['passed']and result['source_unchanged'];arrays['partial_branch']=partial
 return result,arrays
