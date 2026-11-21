"""One declared raw request law for private and actual future owners.

No step, Allocator.compute, scan or physical permission is supplied. The caller
must apply the original gear gate exactly once, then the unchanged Allocator.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
poly=exact('v1485_fixed_polynomial_proposal',C/'polynomial.py')
gear_source=exact('v1485_original_gear_request_guard',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py')
contract=exact('v1485_original_signed_twist_limits',R/'experiments/v1288_baseline_interface/contract.py')
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def wrap(a):return math.atan2(math.sin(a),math.cos(a))
def stopped(packet):
 return max(abs(x)for x in packet['body'][3:])<=.003 and max(abs(x)for x in packet['steering']['velocity'])<=.03 and max(abs(x)for x in packet['controller_memory']['last_ctrl'][2:])<=1e-10

def errors(packet,goal):
 b=packet['body'];rear=[b[0]-.3*math.cos(b[2]),b[1]-.3*math.sin(b[2])]
 return math.dist(rear,goal[:2]),abs(wrap(b[2]-goal[2]))

class Policy:
 def __init__(self,current,proposal):
  value=dict(current);identity=value.pop('input_sha256');assert digest(value)==identity
  clean=dict(proposal);p_sha=clean.pop('proposal_sha256');assert digest(clean)==p_sha and proposal['input_sha256']==identity
  assert proposal['core_identity_sha256']==current['core_identity_sha256']
  assert not current['origin']['steering_motion_active']and current['origin']['parked_target']is None,'PRIEST_POLICY_ACTIVE_STEERING_MODE_NOT_QUALIFIED'
  self.current=copy.deepcopy(current);self.proposal=copy.deepcopy(proposal);self.input_sha=identity;self.proposal_sha=p_sha
  self.origin=current['fixed_origin_native'];self.origin_time=current['fixed_origin_sim_time'];self.last=self.origin-1
  self.pending=None;self.cached=None;self.tail_start=None;self.complete=False
  self.gear=copy.deepcopy(current['gear_memory'])
  self.source_kind=None

 def select(self,packet,*,source_kind):
  assert source_kind in {'ACTUAL_MEASURED_PACKET','PRIVATE_CURRENT_RESPONSE_PACKET'}
  assert self.source_kind in (None,source_kind),'PRIEST_POLICY_OWNER_KIND_CHANGED'
  self.source_kind=source_kind
  tick=packet['native_tick'];assert not self.complete and self.pending is None and type(tick)is int and tick==self.last+1
  assert abs(packet['sim_time']-(self.origin_time+.01*(tick-self.origin)))<=1e-8,'PRIEST_POLICY_FIXED_CLOCK'
  b=packet['body'];ctrl=packet['controller_memory']['last_ctrl'];enc=[*packet['steering']['position'],*packet['steering']['velocity']]
  assert len(b)==5 and len(ctrl)==len(enc)==4 and all(type(x)in(int,float)and math.isfinite(x)for x in [*b,*ctrl,*enc,packet['controller_memory']['integral']])
  assert packet['parked_target']is None and not packet['steering_motion_active'],'PRIEST_POLICY_UNREGISTERED_MODE_SWITCH'
  goal=self.current['next_segment']['poses'][-1];pos,yaw=errors(packet,goal)
  if self.tail_start is None and (tick-self.origin>=1000 or(pos<=.12 and yaw<=.20 and stopped(packet))):self.tail_start=tick
  if self.tail_start is not None:raw=[0.,0.];phase='FINAL_TAIL'
  else:
   phase='PRIEST_POLYNOMIAL_TRACK'
   if self.cached is None or(tick-self.origin)%5==0:
    reply=self.proposal['reply'];elapsed=.01*(tick-self.origin)
    samples=[poly.sample(reply['coefficients_x'],reply['coefficients_y'],time_s=min(10.,elapsed+i*10./99.),gear=reply['gear'])for i in range(6)]
    vx=sum(x['velocity'][0]for x in samples)/6;vy=sum(x['velocity'][1]for x in samples)/6;speed=math.hypot(vx,vy)
    assert speed>1e-12,'PRIEST_UNRESOLVED_ZERO_SPEED_DIRECTION'
    desired=math.atan2(reply['gear']*vy,reply['gear']*vx);error=wrap(desired-b[2])
    vr=reply['gear']*speed*math.cos(error);wr=error/(6*10.*.01)
    assert abs(vr)<.005 or vr*reply['gear']>0,'PRIEST_REQUEST_OPPOSES_DECLARED_SEGMENT_GEAR'
    contract.twist(vr,wr) # Reject in-place/curvature/speed violations; never clip.
    self.cached=[vr,wr]
   raw=self.cached.copy()
  gate=gear_source.GearHandoff()
  for k,v in self.gear.items():setattr(gate,k,v)
  assert gate.last_tick==tick-1,'PRIEST_POLICY_GEAR_HISTORY_GAP'
  vr,wr,proof=gate.select(*raw,native_tick=tick,body=b,last_ctrl=ctrl,encoders=enc)
  after=dict(gear=gate.gear,brake_start=gate.brake_start,last_tick=gate.last_tick)
  row=dict(before_native=tick,raw_request=[*raw,False],expected_request_after_original_gear=[vr,wr,False],expected_gear_handoff=proof,expected_gear_memory_after=after,source_feedback_sha256=digest(packet),phase=phase,parked_target=None,input_sha256=self.input_sha,proposal_sha256=self.proposal_sha,
   contribution_owner='APPLIED_STOP_TAIL'if phase=='FINAL_TAIL'else'ENGINEERING_PRIEST_POLYNOMIAL_FEEDBACK',control_emitted=False,execution_permitted=False)
  self.pending=copy.deepcopy(row);self.last=tick
  return row

 def observe_applied(self,*,before_native,gear_handoff,gear_memory_after,after_packet):
  row=self.pending;assert row is not None and before_native==row['before_native']
  assert gear_handoff==row['expected_gear_handoff']and gear_memory_after==row['expected_gear_memory_after'],'PRIEST_ORIGINAL_GEAR_NOT_APPLIED_EXACTLY_ONCE'
  assert after_packet['native_tick']==before_native+1 and abs(after_packet['sim_time']-(self.origin_time+.01*(before_native+1-self.origin)))<=1e-8
  self.gear=copy.deepcopy(gear_memory_after);self.pending=None
  if self.tail_start is not None and after_packet['native_tick']-self.tail_start==200:
   pos,yaw=errors(after_packet,self.current['next_segment']['poses'][-1]);assert pos<=.12 and yaw<=.20 and stopped(after_packet),'PRIEST_FINITE_POLYNOMIAL_ENDPOINT_OR_STOP_REFUSED'
   self.complete=True
  return dict(complete=self.complete,source_kind=self.source_kind,input_sha256=self.input_sha,proposal_sha256=self.proposal_sha,physical_permission=False)
