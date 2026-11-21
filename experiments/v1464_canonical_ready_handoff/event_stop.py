"""Stop on a real completed current event, never on a saved native tick."""
import copy
class FirstEventStop:
 def __init__(self,canonical,pump):
  self.owner=canonical;self.pump=pump;self.observed_event=None;self.completion=None
 def before_iteration(self):
  assert self.completion is None and not self.pump.stopped
  transaction=self.owner.transaction
  # The original transaction increments last_event only after a bound notice;
  # this narrow owner cannot start a second event or reset the first one.
  assert transaction.last_event<=0,'FIRST_EVENT_SCOPE_SECOND_EVENT_FORBIDDEN'
 def after_iteration(self):
  bridge=self.owner.bridge
  if bridge is None:return False
  assert self.owner.transaction.last_event==0,'FIRST_EVENT_SCOPE_FOREIGN_EVENT'
  identity=bridge.request.current['input_sha256']
  if self.observed_event is None:self.observed_event=identity
  assert self.observed_event==identity,'FIRST_EVENT_SCOPE_CURRENT_INPUT_CHANGED'
  if not bridge.complete:return False
  native=self.owner.native
  assert native.bridge_started and native.applied==native.vehicle.count and not native.in_step
  assert native.mode_memory.snapshot(native.applied)['covered_native']==native.applied
  # complete is set by original BridgeExecution only after its full response
  # reference membership and terminal method gates. No goal test is weakened.
  self.completion=dict(event_index=0,current_input_sha256=identity,complete_actual_bridge=True,completed_native=native.applied,whole_route_goal_not_claimed=True,component_scope_only=True,mode_history=copy.deepcopy(native.mode_memory.snapshot(native.applied)))
  self.pump.stopped=True
  return True
 def require_complete(self):
  assert self.completion is not None,'LIVE_FIRST_EVENT_NOT_COMPLETED'
  return copy.deepcopy(self.completion)
