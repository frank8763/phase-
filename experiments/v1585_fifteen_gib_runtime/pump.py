"""Actual prefix pump and disclosed goal-bound policy; no modeled ROS peer."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import socket
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def owner_state_digest(v):
 value={k:getattr(v.d,k).tolist()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};value['time']=float(v.d.time)
 return __import__('hashlib').sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
wire_grants=exact('v1479_before_wire_grant',R/'experiments/v1479_retirement_scope_binding/wire_grant.py')
commands_module=exact('v1421_actual_route_commands',R/'experiments/v1479_retirement_scope_binding/route_command.py')
stamped=exact('v1421_actual_expiry',R/'experiments/v1396_rpp_rpc_retirement/stamped_contract.py')
transport=exact('v1421_actual_latest_transport',R/'experiments/v1370_overnight_controller_matrix/transport.py')

class Pump:
 def __init__(self,owner,*,check_budget,append):
  self.owner=owner;self.check=check_budget;self.append=append;self.armed=False;self.stopped=False;self.ros_pass=False;self.prefix_inflight=False;self.closed=False;self.transport_drops=0;self.freshness_start=None
  self.command_gate=commands_module.Commands(owner.native.run_id,retirement_sink=lambda proof:self.append(dict(kind='RETIRED_ACTUAL_ROUTE',retirement=proof)));self.socket=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
  self.address=str((owner.output/'native.sock').relative_to(R));self.peer=str((owner.output/'ros.sock').relative_to(R));assert max(len(self.address.encode()),len(self.peer.encode()))<108
  try:self.socket.bind(self.address);self.socket.settimeout(.02)
  except BaseException:self.socket.close();raise

 def publish(self):
  quota=self.owner.quota;wire_grants.before_wire(quota,native_tick=self.owner.native.vehicle.count)
  envelope=self.owner.envelope();sent=transport.send_latest(self.socket,json.dumps(envelope,allow_nan=False).encode(),self.peer)
  self.transport_drops+=not sent
  self.append(dict(kind='PUBLISHED_ACTUAL_ENVELOPE',envelope=envelope,transport_sent=sent))
  return envelope

 def receive(self):
  try:raw,sender=self.socket.recvfrom(1024*1024)
  except socket.timeout:return None
  assert sender==self.peer,'FOREIGN_ACTUAL_ROUTE_SOCKET'
  value=json.loads(raw);assert value['run_id']==self.owner.native.run_id,'FOREIGN_ACTUAL_ROUTE_RUN'
  self.append(dict(kind='RECEIVED_ACTUAL_ROUTE',before_native=self.owner.native.vehicle.count,packet=value,received_monotonic=time.monotonic()))
  return value

 def send_notice(self,value):
  assert value['run_id']==self.owner.native.run_id
  assert transport.send_latest(self.socket,json.dumps(value,allow_nan=False).encode(),self.peer),'CURRENT_BRIDGE_NOTICE_TRANSPORT_FAILED'

 def prefix_step(self,command,*,stop_tail=False):
  n=self.owner.native;v=n.vehicle;assert not n.bridge_started and not self.prefix_inflight and v.count==n.applied
  self.check('ACTUAL_STOP_TAIL'if stop_tail else'ACTUAL_NATIVE',1)
  if stop_tail:
   vr=wr=0.;delivery=None;control_owner='APPLIED_STOP_TAIL';expiry=None;upstream=[0.,0.,False]
  else:
   delivery=command['delivery'];assert delivery['source_kind']=='ACTUAL_FRAME'
   commands_module.frames.validate_binding(delivery,n.sent)
   assert 0<=v.count-delivery['observation_native_tick']<5
   vr,wr,expiry=stamped.before_step(command['v'],command['w'],delivery,time.monotonic());assert expiry['fresh'],'PREFIX_COMMAND_EXPIRED'
   upstream=[vr,wr,False];control_owner=command['control_owner']
  body=list(v.body());enc=v.steering_sample().tolist();last=v.adapter.last.tolist();candidate=copy.deepcopy(n.gear)
  vr,wr,gear=candidate.select(vr,wr,native_tick=v.count,body=body,last_ctrl=last,encoders=enc)
  row=dict(before_native=v.count,control_owner=control_owner,source_full_state_sha256=owner_state_digest(v),phase='COMPLETE_STOP_TAIL'if stop_tail else'ORIGINAL_RPP_ROUTE_PREFIX',upstream_request=upstream,request=[vr,wr,False],gear_handoff=gear,last_ctrl=last,integral=float(v.adapter.integral),encoders=enc,body=body,parked_target=None,delivery=delivery,expiry_gate=expiry,applied=False)
  self.append(dict(kind='BEFORE_ORIGINAL_PREFIX_NATIVE',row=copy.deepcopy(row)))
  v.adapter.parked_target=None;self.prefix_inflight=True;v.step(vr,wr,False);self.prefix_inflight=False;row['applied']=True
  self.owner.observe_original_prefix(row,control_owner=control_owner)
  b=list(v.body());lateral=-float(v.d.qvel[0])*math.sin(b[2])+float(v.d.qvel[1])*math.cos(b[2]);assert abs(b[3])<=.13 and abs(b[4])<=.16 and abs(lateral)<=.03,'PREFIX_BODY_CAP'
  self.append(dict(kind='AFTER_ORIGINAL_PREFIX_NATIVE',row=row))

 def iteration(self):
  assert not self.stopped and not self.closed;self.check('PUMP',0);n=self.owner.native
  if self.owner.bridge is not None:
   self.bridge_iteration();return
  assert not n.bridge_started
  last=self.owner.last_published_native
  if last is None or n.vehicle.count-last>=5 or (n.vehicle.count==last and n.sent and time.monotonic()-max(n.sent.values(),key=lambda p:p['sequence'])['sampled_at']>=.04):self.publish()
  packet=self.receive()
  if packet is None:
   if self.freshness_start is not None and time.monotonic()-self.freshness_start>=2.:raise TimeoutError('NO_FRESH_ROUTE_COMMAND_FOR_2S')
   return
  kind=packet['kind'];now=time.monotonic()
  if kind=='arm':
   assert not self.armed and n.vehicle.count==0 and 0<=now-packet['issued_at']<=.2,'ACTUAL_ARM_ORDER_OR_AGE';self.armed=True;return
  assert self.armed,'ACTUAL_COMMAND_BEFORE_ARM'
  if kind=='stop':
   assert 0<=now-packet['issued_at']<=.2,'ACTUAL_STOP_EXPIRED';self.ros_pass=packet['passed']is True;self.stopped=True;return
  if kind=='BRIDGE_CERTIFICATE_REQUEST_FILE':
   # Actual event stops at source capture. No modeled ROS or old certificate
   # is constructed, and no BRIDGE_*_READY notice is fabricated.
   self.owner.on_cusp(packet)
   assert self.owner.bridge is not None,'CURRENT_GOAL_BOUND_INSTALLATION_MISSING'
   return
  assert kind=='command','UNKNOWN_ACTUAL_ROUTE_PACKET'
  command=self.command_gate.accept(packet,n.sent,current_native=n.vehicle.count,now=now)
  if command is None:
   if self.freshness_start is None:self.freshness_start=now
   assert now-self.freshness_start<2.,'NO_FRESH_ROUTE_COMMAND_FOR_2S'
   return
  self.freshness_start=None
  for _ in range(5):
   self.prefix_step(command)

 def bridge_iteration(self):
  n=self.owner.native;bridge=self.owner.bridge
  assert n.bridge_started and not bridge.failed and not bridge.inflight
  wire_grants.before_wire(self.owner.quota,native_tick=n.applied)
  envelope=self.owner.envelope();wire=envelope['wire'];now=time.monotonic()
  # A disclosed local policy command is not a fabricated NAV2 stamp or RPP
  # reply. Original NativeStep still applies binding/hold/postcertificate200ms.
  delivery=dict(source_kind='ACTUAL_FRAME',run_id=n.run_id,
   observation_sequence=wire['sequence'],observation_native_tick=wire['native_tick'],
   observation_sampled_at=wire['sampled_at'],issued_at=now,
   origin=dict(kind='DISCLOSED_SHARED_SEGMENT_POLICY',generated_monotonic=now),
   response_method_sha256=bridge.method['response_method_sha256'],
   policy_definition='experiments/v1585_fifteen_gib_runtime/tracker.py')
  self.append(dict(kind='CURRENT_SHARED_POLICY_DELIVERY',delivery=delivery,envelope=envelope))
  result=bridge.block(delivery)
  if result['complete']:
   self.publish()
   self.owner.atomic(self.owner.output/'GOAL_BOUND_ACTUAL_COMPLETE.json',result)
   self.stopped=True

 def close(self):
  if self.closed:return
  self.owner.atomic(self.owner.output/'PEER_STOP_REQUEST.json',dict(run_id=self.owner.native.run_id,requested_monotonic=time.monotonic(),no_native_action=True))
  self.closed=True;self.socket.close();Path(self.address).unlink(missing_ok=True)
