"""Fresh scalar response audit, independent of the producer's step loop."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1497_audit_model_binding',C/'model_bridge.py');bridge=importlib.util.module_from_spec(s);s.loader.exec_module(bridge)

def audit(current,proposal,setup,evidence,*,branch_count,read_branch,authority,lock,save_origin):
 assert authority['mode']=='PRIEST_RESPONSE_INDEPENDENT_AUDIT'
 binding=bridge.authorize(current,proposal,authority,lock)
 # Numerical audits occur only after a fully completed producer succeeded.
 assert evidence['generation']['passed']and evidence['generation']['closed']and not evidence['generation']['analytical_inflight_unknown']
 Predictor,initial,kernel,Adapter,Gear,Policy,feedback,Geometry,causal=bridge.binding()
 import numpy as np
 known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text());assert setup['known']==known
 forecast=causal(current['causal_snapshot'],current_native=current['fixed_origin_native'],current_sim_time=current['fixed_origin_sim_time']);assert forecast==current['causal_forecast']
 geometry=Geometry(known,[*forecast['center'],forecast['radius_m']]);origin=current['origin'];origin_tick=current['fixed_origin_native']
 nominal=np.asarray(evidence['states'],dtype=float);ctrl=np.asarray(evidence['ctrl'],dtype=float);memory=np.asarray(evidence['memory'],dtype=float);journal=evidence['journal'];modes=evidence['modes'];n=len(journal)
 assert 200<=n<=authority['maximum_nominal_native']and branch_count==n
 assert nominal.shape==(n+1,8)and ctrl.shape==(n,4)and memory.shape==(n,5)and len(modes)==n
 assert all(np.isfinite(v).all()for v in [nominal,ctrl,memory])
 assert evidence['generation']['nominal_native']==n and evidence['generation']['complete_stop_branches']==n and evidence['generation']['analytical_native']==n*201
 result=dict(passed=False,closed=False,binding=binding,audit_analytical_native=0,audit_inflight_unknown=False,explicit_predictor_constructions=0,branch_copies=0,maximum_state_ctrl_memory_error=0.,models_physical=0,replay_native=0,actual_admission=False)
 end=min(authority['hard_stop_monotonic'],time.monotonic()+1800);minimum=math.inf
 def compare(a,b):
  a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);assert a.shape==b.shape and np.isfinite(a).all()and np.isfinite(b).all()
  err=float(np.max(abs(a-b)))if a.size else 0.;result['maximum_state_ctrl_memory_error']=max(result['maximum_state_ctrl_memory_error'],err)
  assert err<=1e-8,'PRIEST_RESPONSE_FRESH_STATE_CTRL_MEMORY_DIVERGED'
 def step(p,v,w):
  assert time.monotonic()<end and time.time()<min(authority['absolute_deadline_unix'],1795395600)
  assert result['audit_analytical_native']<authority['maximum_analytical_native']
  before=p.adapter.last.copy();result['audit_inflight_unknown']=True;state,u=p.step(v,w,False);result['audit_analytical_native']+=1;result['audit_inflight_unknown']=False
  assert p.adapter.commands.legal(u),'PRIEST_AUDIT_CONTROL_LIMIT'
  rate=np.asarray(p.adapter.commands.rate)*p.adapter.dt/.08
  assert np.max(abs(u-before)-rate)<=1e-8,'PRIEST_AUDIT_CONTROL_SLEW'
  return state,u
 def packet(p,tick):return bridge.current_packet(p,current=current,native_tick=tick,feedback=feedback)
 try:
  result['explicit_predictor_constructions']=None;p=Predictor(setup,initial(origin),kernel.PARAMETERS);result['explicit_predictor_constructions']=1
  assert p.adapter.__class__ is Adapter
  p.adapter.encoders=lambda owner=p:feedback.current(owner);p.adapter.parked_target=origin['parked_target'];p.adapter._steering_motion_active=origin['steering_motion_active']
  compare(p.state,nominal[0]);first=packet(p,origin_tick)
  origin_proof=bridge.origin_comparison(first,current,p.state);save_origin(origin_proof)
  assert origin_proof['passed'],'PRIEST_AUDIT_CURRENT_ORIGIN_CHANGED'
  gate=Gear()
  for k,v in current['gear_memory'].items():setattr(gate,k,v)
  method=Policy(current,proposal)
  for i,row in enumerate(journal):
   tick=origin_tick+i;assert row['before_native']==tick
   before=packet(p,tick);compare(memory[i],[*p.adapter.last,float(p.adapter.integral)])
   assert modes[i]==dict(coupled_episode=p.coupled_episode,parked_target=p.adapter.parked_target,steering_motion_active=bool(p.adapter._steering_motion_active))
   proof,ss,uu=read_branch(i);ss=np.asarray(ss,dtype=float);uu=np.asarray(uu,dtype=float)
   assert ss.shape==(201,8)and uu.shape==(200,4)and np.isfinite(ss).all()and np.isfinite(uu).all()
   assert proof['before_native']==tick and proof['complete_native']==200 and proof['current_input_sha256']==current['input_sha256']and proof['proposal_sha256']==proposal['proposal_sha256']
   assert proof['geometry_kind']=='FULL_PERIOD_DISK'and proof['causal_snapshot_sha256']==current['causal_snapshot_sha256']
   compare(p.state,ss[0]);branch=copy.deepcopy(p);branch.adapter.encoders=lambda owner=branch:feedback.current(owner);branch.adapter.parked_target=None;result['branch_copies']+=1
   for j in range(200):state,u=step(branch,0.,0.);compare(state,ss[j+1]);compare(u,uu[j])
   stop=packet(branch,tick+200);lower=float(geometry.tube(ss));minimum=min(minimum,lower)
   assert lower>=.22-1e-8 and abs(lower-proof['causal_tube_lower_m'])<=1e-8 and proof['rest']and proof['body_caps']
   assert abs(stop['body_lateral'])<=.003 and max(abs(x)for x in stop['body'][3:])<=.003 and max(abs(x)for x in stop['steering']['velocity'])<=.03 and max(abs(x)for x in stop['controller_memory']['last_ctrl'][2:])<=1e-10
   assert (abs(ss[:,3:6])<=np.array([.13,.03,.16])+1e-8).all()
   selected=method.select(before,source_kind='PRIVATE_CURRENT_RESPONSE_PACKET');assert selected==row['selection']and selected['raw_request']==row['requested']and selected['contribution_owner']==row['control_owner']
   vr,wr,gear=gate.select(*selected['raw_request'][:2],native_tick=tick,body=before['body'],last_ctrl=before['controller_memory']['last_ctrl'],encoders=[*before['steering']['position'],*before['steering']['velocity']])
   gear_memory=dict(gear=gate.gear,brake_start=gate.brake_start,last_tick=gate.last_tick)
   assert [vr,wr,False]==row['admitted']==selected['expected_request_after_original_gear']and gear==row['gear']==selected['expected_gear_handoff']and gear_memory==row['gear_memory_after']
   state,u=step(p,vr,wr);compare(state,nominal[i+1]);compare(u,ctrl[i]);method.observe_applied(before_native=tick,gear_handoff=gear,gear_memory_after=gear_memory,after_packet=packet(p,tick+1))
   assert method.complete==(i==n-1),'PRIEST_AUDIT_EARLY_OR_MISSING_COMPLETE'
  last=packet(p,origin_tick+n);goal=current['next_segment']['poses'][-1];body=last['body'];rear=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2])];whole=float(geometry.tube(nominal))
  checks=dict(fresh_state_ctrl_memory_error=result['maximum_state_ctrl_memory_error']<=1e-8,all200_branches=branch_count==n,all_201_steps=n*201==result['audit_analytical_native'],complete_zero200=len(journal[-200:])==200 and all(r['requested']==r['admitted']==[0.,0.,False]for r in journal[-200:]),whole_tube=whole>=.22-1e-8,endpoint_position=math.dist(rear,goal[:2])<=.12,endpoint_heading=abs(math.atan2(math.sin(body[2]-goal[2]),math.cos(body[2]-goal[2])))<=.20,body_rest=max(abs(x)for x in body[3:])<=.003 and abs(last['body_lateral'])<=.003,steering_rest=max(abs(x)for x in last['steering']['velocity'])<=.03,rear_zero=max(abs(x)for x in last['controller_memory']['last_ctrl'][2:])<=1e-10,nominal_caps=bool((abs(nominal[:,3:6])<=np.array([.13,.03,.16])+1e-8).all()))
  result.update(passed=all(checks.values()),checks=checks,minimum_stop_tube_m=minimum,whole_tube_m=whole,nominal_native=n)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  result.update(closed=True,source_unchanged=all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in authority['tested_source_hashes'].items()))
  result['passed']=result['passed']and result['source_unchanged']
 return result
