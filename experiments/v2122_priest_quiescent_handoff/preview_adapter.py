"""New tracker through the old one-use preview API; never physical authority."""
from pathlib import Path
import copy,hashlib,importlib.util,json
R=Path(__file__).resolve().parents[2]
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class OriginPreview:
 def __init__(self,current,proposal,source,*,saved_software_only=False):
  self.closed=False;self.used=False;self.poisoned=True;self.saved=saved_software_only
  assert current['kind']=='PHASE_PRIEST_CURRENT_POLYNOMIAL_INPUT'
  names=['experiments/v1485_priest_current_polynomial_seam/candidate_output.py','experiments/v2122_priest_quiescent_handoff/tracking.py','experiments/v1288_baseline_interface/contract.py']
  for n in names:assert source[n]==hashlib.sha256((R/n).read_bytes()).hexdigest(),'PRIEST_ADAPTER_SOURCE_CHANGED'
  self.boundary=load('PRIEST_source_bound_candidate',R/names[0]);assert self.boundary.bind(current,proposal['reply'])==proposal,'PRIEST_ADAPTER_CANDIDATE_CHANGED'
  self.tracker=load('PRIEST_geometric_tracker',R/names[1]);self.contract=load('PRIEST_original_command_contract',R/names[2]);self.current=copy.deepcopy(current);self.proposal=copy.deepcopy(proposal);self.poisoned=False
 def preview(self,packet):
  assert not self.closed and not self.used and not self.poisoned,'PRIEST_ADAPTER_CLOSED_USED_POISONED'
  self.poisoned=True;current=self.current;reply=self.proposal['reply']
  assert digest(packet)==digest(current['origin']),'PRIEST_ADAPTER_FOREIGN_ORIGIN'
  assert packet['native_tick']==current['fixed_origin_native']and packet['sim_time']==current['fixed_origin_sim_time'],'PRIEST_ADAPTER_CLOCK_CHANGED'
  assert not packet['steering_motion_active']and packet.get('parked_target')is None,'PRIEST_ADAPTER_STEERING_MODE'
  p=self.tracker.command(reply['coefficients_x'],reply['coefficients_y'],body=packet['body'],gear=reply['gear'],receipt_native=packet['native_tick'],proposal_native=reply['origin_native']);self.contract.twist(*p['request'][:2])
  self.used=True;self.poisoned=False
  return dict(raw_request=p['request'],input_sha256=current['input_sha256'],proposal_sha256=self.proposal['proposal_sha256'],origin_packet_sha256=digest(packet),origin_native=packet['native_tick'],original_gear_gate_still_required=True,full5_plus2200_response_still_required=True,actual_execution_permitted=False,full_vehicle_qualified=False,adaptation='PRIEST_POLYNOMIAL_GEOMETRIC_PP_0P6_SPEED_0P08',polynomial_timing_preserved=False,saved_software_only=self.saved,tracker_details=p)
 def close(self):self.closed=True
