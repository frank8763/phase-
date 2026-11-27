"""Strict packet-only offline filter request; no factory or controller imports."""
import copy,hashlib,json,math
from common import R,load
ALLOWED_KNOWN={'source','source_sha256','bootstrap_seed','known_rectangles','known_circles','scope'}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def build(receipt,known,nominal,gear,causal=None):
 assert set(known)<=ALLOWED_KNOWN and {'known_rectangles','known_circles'}<=set(known),'PUBLIC_FIELD_WHITELIST'
 original=load('original_causal_receipt_verifier',R/'experiments/v1938_current_causal_solver_wire/wire.py')

 source={str(q.relative_to(R)):original.sha(q)for q in[original.CONTRACT,original.DWA_OBSERVATION,original.TWIST]}
 wire=original.CurrentWire(source,run_id='offline_filter_component',method='PSF')
 p=wire.dwa(receipt,receipt['packet']['native_tick'],receipt['packet']['sim_time'])
 assert set(p)<={'body','body_lateral','native_tick','sim_time','body_measured_at','sent_at','dynamic_discovered','steering','controller_memory','coupled_episode','steering_motion_active','parked_target'},'PACKET_WHITELIST'
 assert gear in[-1,1]and len(nominal)==2 and all(math.isfinite(x)for x in nominal)
 if p['dynamic_discovered']:assert causal is not None,'MISSING_CURRENT_CAUSAL_SOURCE'
 if causal is not None:
  assert set(causal)=={'source_native_tick','source_sim_time','periodic'},'CAUSAL_WHITELIST'
  assert causal['source_native_tick']<=p['native_tick']and 0<=p['sim_time']-causal['source_sim_time']<=.05000001,'CAUSAL_SOURCE_STALE_OR_FUTURE'
  assert abs(causal['source_sim_time']-.01*causal['source_native_tick'])<=1e-8,'CAUSAL_SOURCE_CLOCK'
  assert set(causal['periodic'])=={'omega','amplitude','last','source_tick','vertices'},'PERIODIC_SOURCE_WHITELIST'
  from geometry import support_at
  support_at(causal['periodic'],p['sim_time'],True)
  assert causal['periodic']['source_tick']<=causal['source_native_tick']and causal['periodic']['last']<=causal['source_sim_time']
 return dict(schema='OFFLINE_PSF_PCBF_CAUSAL_BODY_INPUT',pose=p['body'][:3],native=p['native_tick'],sim_time=p['sim_time'],receipt_sha256=digest(receipt),public_known=copy.deepcopy(known),public_known_sha256=digest(known),nominal_twist=list(nominal),gear=gear,causal=copy.deepcopy(causal),model_identity='EXPLICIT_IDEAL_KINEMATIC_ONLY',actuator_model=None,uncertainty_bound=None,physical_authority=False)
