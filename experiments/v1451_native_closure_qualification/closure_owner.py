"""Only the original pre-bridge owner seam, with no event/route authority."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
original=exact('v1451_original_native_owner',R/'experiments/v1423_integrated_route_audit/native_step.py')
def forbidden(*_,**__):raise RuntimeError('ZERO_TAIL_ONLY_NO_SCAN_EVENT_OR_PRIVATE_MODEL')
class ZeroTailOwner:
 def __init__(self,vehicle,*,output,run_id,atomic,check):
  self.output=Path(output);self.atomic=atomic;self.closed=False
  self.native=original.NativeStep(vehicle,run_id=run_id,reserve=forbidden,physical_guard=forbidden,evidence_sink=None)
  self.native.before_native_budget=check
 def observe_original_prefix(self,row,*,control_owner):
  assert not self.closed and control_owner=='APPLIED_STOP_TAIL'and row['request']==[0.,0.,False]
  self.native.observe_original_prefix(row,control_owner=control_owner)
 def close(self):
  self.closed=True;self.atomic(self.output/'CANONICAL_OWNER_CLOSED.json',dict(closed=True,actual=self.native.exact_accounting(),event_transaction_created=False,physical_route_admission=False))
 envelope=on_cusp=advance_bridge=forbidden
