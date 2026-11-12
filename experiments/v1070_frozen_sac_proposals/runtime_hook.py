"""Hook for the next qualified owner; no model creation or control ownership."""
import numpy as np
from integration import ShieldedSAC
class RuntimeHook:
 def __init__(self,measurement_provider):self.measurements=measurement_provider;self.shield=ShieldedSAC()
 def propose(self,vehicle,setup,packet,source,nominal_requests,goal_xy):
  # The sensor backend supplies the actual legacy feature blocks. It may
  # perform sensing, but cannot integrate or alter physical/controller state.
  before={k:np.asarray(getattr(vehicle.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};tick=vehicle.count;clock=float(vehicle.d.time);memory=np.r_[vehicle.adapter.last,vehicle.adapter.integral]
  frame=self.measurements.read(vehicle)
  assert frame['native_tick']==tick==packet['native_tick']and float(vehicle.d.time)==clock and vehicle.count==tick,'SENSING_ADVANCED_OR_STALE_STATE'
  assert all(np.array_equal(v,np.asarray(getattr(vehicle.d,k)))for k,v in before.items()),'SENSING_CHANGED_PHYSICAL_STATE'
  assert np.array_equal(memory,np.r_[vehicle.adapter.last,vehicle.adapter.integral]),'SENSING_CHANGED_CONTROLLER_MEMORY'
  return self.shield.propose_goal_profile(setup,packet,source,frame['blocks'],frame['native_tick'],nominal_requests,goal_xy)
