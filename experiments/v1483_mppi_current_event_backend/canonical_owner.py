"""Concrete actual CUSP event installation on one canonical native owner.

The outer registered CLI owns the vehicle/process lifetime and replay. This
module never creates a vehicle or obtains launch permission by importing it.
"""
import copy
import importlib.util
import math
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
native_module=exact('v1423_exact_native_owner',C/'native_step.py')
reserve_module=exact('v1420_current_reserve',C/'reserve.py')
guard_module=exact('v1420_current_guard',C/'physical_guard.py')
sink_module=exact('v1420_current_sink',C/'evidence_sink.py')
bridge_module=exact('v1420_live_feedback_bridge',C/'bridge_execution.py')
transaction_module=exact('v1423_current_transaction',C/'transaction.py')

controller=exact('v1483_canonical_plugin_identity',C/'controller_identity.py')
context=exact('v1483_exact_MPPI_task',C/'route_context.py')

def unavailable(*args,**kwargs):raise RuntimeError('CURRENT_EVENT_EXECUTION_NOT_INSTALLED')

class CanonicalOwner:
 def __init__(self,vehicle,*,task,output,setup,authority,lock,budget,limits,reserve_accounting,reserve_limits,atomic,np,peer_command,peer_replies,check_budget,quota,append):
  context.task_check(task);self.controller_identity_sha256=controller.verify(task['controller_binding'])
  assert callable(append);self.append=append
  self.quota=quota;self.task=copy.deepcopy(task);self.output=Path(output).resolve();self.setup=copy.deepcopy(setup);self.authority=copy.deepcopy(authority);self.lock=lock;self.atomic=atomic;self.np=np
  self.native=native_module.NativeStep(vehicle,run_id=task['run_id'],controller_identity_sha256=self.controller_identity_sha256,reserve=unavailable,physical_guard=unavailable,evidence_sink=None)
  self.native.before_native_budget=check_budget
  self.reserve_accounting=reserve_accounting;self.reserve_limits=copy.deepcopy(reserve_limits);self.bridge=None;self.sink=None;self.closed=False;self.last_published_native=None
  self.transaction=transaction_module.CuspTransaction(native=self.native,output=self.output,setup=setup,authority=authority,lock=lock,budget=budget,limits=limits,atomic=atomic,np=np,peer_command=peer_command,peer_replies=peer_replies,quota=quota)

 def observe_original_prefix(self,row,*,control_owner):
  assert not self.closed and not self.native.bridge_started
  self.native.observe_original_prefix(row,control_owner=control_owner)

 def envelope(self):
  assert not self.closed
  n=self.native;wire,packet=n.current();gear=dict(gear=n.gear.gear,brake_start=n.gear.brake_start,last_tick=n.gear.last_tick)
  feedback=dict(native_tick=wire['native_tick'],sim_time=wire['sim_time'],body=wire['body'],encoders=[*packet['steering']['position'],*packet['steering']['velocity']],last_ctrl=packet['controller_memory']['last_ctrl'],integral=packet['controller_memory']['integral'],parked_target=packet['parked_target'],steering_motion_active=packet['steering_motion_active'],gear_memory=gear)
  self.last_published_native=n.vehicle.count
  return dict(kind='ROUTE_ACTUAL_FRAME',wire=wire,feedback=feedback,evidence_state_sha256=native_module.state_digest(n.vehicle))

 def on_cusp(self,notice):
  assert not self.closed and (self.bridge is None or self.bridge.complete)
  if self.sink is not None:self.sink.close(self.native.exact_accounting())
  request,ready,states=self.transaction.run(notice)
  # Every potentially slow full-source check is done before a fresh live wire.
  # The canonical plant stays fixed throughout; none of its state/time is set.
  folder=self.output/'bridge_events'/('event%04d'%notice['event_index'])
  sink=sink_module.EvidenceSink(folder/'actual',identity=request.current['input_sha256'],np=self.np,atomic=self.atomic,maximum_branches=self.reserve_limits['maximum_branches_per_event'],quota=self.quota)
  self.sink=sink
  a=dict(self.authority,scope='CURRENT_MEASURED_PACKET_RESERVE',current_input_sha256=request.current['input_sha256'],causal_snapshot_sha256=request.current['causal_snapshot_sha256'],maximum_analytical_native=self.reserve_limits['maximum_analytical_native'],maximum_predictor_constructions=self.reserve_limits['maximum_predictor_constructions'])
  reserve=reserve_module.CurrentReserve(setup=self.setup,current=request.current,authority=a,lock=self.lock,accounting=self.reserve_accounting,save_complete=sink.reserve_complete,save_partial=sink.reserve_partial)
  guard=guard_module.PhysicalGuard.at_event(self.native.vehicle,setup=self.setup,current=request.current,canonical_owner=self.native)
  self.native.reserve=reserve;self.native.physical_guard=guard;self.native.sink=sink;self.sink=sink
  assert request.current['controller_identity_sha256']==self.controller_identity_sha256,'CURRENT_CERTIFICATE_WRONG_ACTUAL_PLUGIN'
  self.bridge=bridge_module.BridgeExecution(request,self.native,self.np.asarray(states,dtype=float).tolist(),retirement_sink=lambda proof:self.append(dict(kind='RETIRED_ACTUAL_BRIDGE',event_index=notice['event_index'],retirement=proof)))
  self.last_published_native=None
  return ready

 def advance_bridge(self,*,mppi_packet=None,action_done=None):
  assert not self.closed and self.bridge is not None and not self.bridge.complete
  n=self.native;tick=n.vehicle.count;origin=self.bridge.start
  # Outer pump publishes this real envelope before requesting any new command.
  assert self.last_published_native is not None and 0<=tick-self.last_published_native<5,'FRESH_ACTUAL_WIRE_REQUIRED_AFTER_CERTIFICATE'
  if (tick-origin)%5==0:assert self.last_published_native==tick,'ORIGINAL5_NATIVE_SAMPLE_CADENCE'
  result=self.bridge.advance(mppi_packet=mppi_packet,action_done=action_done)
  if result['kind']=='BRIDGE_COMPLETE':
   body=list(n.vehicle.body());result.update(whole_goal_center_distance_m=math.dist(body[:2],self.task['goal_xy']),whole_forward_progress_m=sum((body[i]-self.task['start_xy'][i])*[math.cos(self.task['start_yaw']),math.sin(self.task['start_yaw'])][i]for i in range(2)))
  return result

 def after_bridge_zero(self,command):
  assert not self.closed and self.bridge is not None and self.bridge.complete
  assert command['v']==command['w']==0.,'POST_BRIDGE_NONZERO_REQUIRES_NEW_CURRENT_EVENT'
  assert command['delivery']['command_source']in {'CAUSAL_BRAKE_HOLD','CAUSAL_BRAKE_TIMER','EXPIRED_SOURCE_ZERO'}
  n=self.native;tick=n.vehicle.count
  assert self.last_published_native is not None and 0<=tick-self.last_published_native<5
  return n.apply(0.,0.,phase='ORIGINAL_ROUTE_ZERO_WAIT',control_owner='DISCLOSED_SHARED_EXECUTION_BRIDGE',delivery=command['delivery'])

 def ordinary_nonzero_after_bridge(self,*args,**kwargs):
  raise RuntimeError('POST_BRIDGE_NONZERO_ROUTE_REQUIRES_NEXT_CURRENT_EVENT_WITNESS')

 def close(self):
  self.closed=True
  if self.sink is not None:self.sink.close(self.native.exact_accounting())
  self.atomic(self.output/'CANONICAL_OWNER_CLOSED.json',dict(closed=True,actual=self.native.exact_accounting(),reserve=copy.deepcopy(self.reserve_accounting),transaction=copy.deepcopy(self.transaction.budget),physical_admission=False))
