"""Pure-current bindings plus lazy CPU2 scalar response, no launch permission."""
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2]

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def bind_input(current,proposal):
 value=copy.deepcopy(current);identity=value.pop('input_sha256');assert digest(value)==identity
 result=copy.deepcopy(proposal);p_sha=result.pop('proposal_sha256');assert digest(result)==p_sha
 assert proposal['input_sha256']==identity and proposal['core_identity_sha256']==current['core_identity_sha256']
 assert proposal['fixed_origin_native']==current['fixed_origin_native']==current['origin']['native_tick']
 assert proposal['fixed_origin_sim_time']==current['fixed_origin_sim_time']==current['origin']['sim_time']
 assert current['causal_snapshot_sha256']==digest(current['causal_snapshot'])
 assert current['causal_snapshot']['periodic']is not None,'PRIEST_CURRENT_RESPONSE_REQUIRES_BOUND_CAUSAL_FORECAST'
 assert current.get('software_fixture_not_actual')is not True,'PRIEST_SOFTWARE_PROPOSAL_NOT_CURRENT_EVENT_INPUT'
 assert not current['origin']['steering_motion_active']and current['origin']['parked_target']is None
 return dict(kind='ENGINEERING_PRIEST_FIXED_POLYNOMIAL_CURRENT_RESPONSE',current_input_sha256=identity,proposal_sha256=p_sha,core_identity_sha256=current['core_identity_sha256'],geometry_kind='FULL_PERIOD_DISK',fixed_origin_native=current['fixed_origin_native'],fixed_origin_sim_time=current['fixed_origin_sim_time'],actual_admission=False)

def authorize(current,proposal,authority,lock):
 identity=bind_input(current,proposal);parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
 assert authority['models_authorized']is True and authority['round_id']==parent['active_round']and parent['models_now_authorized'],'PRIEST_RESPONSE_MODEL_NOT_ADMITTED'
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(R)and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 assert authority['current_input_sha256']==current['input_sha256']and authority['proposal_sha256']==proposal['proposal_sha256']
 assert authority['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert time.time()<authority['absolute_deadline_unix']<=1795395600 and time.monotonic()<authority['hard_stop_monotonic']<=parent['hard_stop_monotonic']
 assert 0<authority['maximum_nominal_native']<=1200 and 0<authority['maximum_analytical_native']<=241200
 assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock';fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert authority['tested_source_hashes']and all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in authority['tested_source_hashes'].items())
 return identity

def binding():
 original=exact('v1497_original_response_constructor',R/'experiments/v1415_unified_causal_witness/generator.py')
 Predictor,initial,kernel,Adapter,_,Gear,_=original.binding()
 policy=exact('v1497_same_frozen_feedback_policy',R/'experiments/v1485_priest_current_polynomial_seam/response_policy.py')
 feedback=exact('v1497_same_scalar_feedback',R/'experiments/v1409_scalar_steering_feedback/feedback.py')
 geometry=exact('v1497_same_full_footprint_geometry',R/'experiments/v1396_rpp_rpc_retirement/geometry_contract.py')
 causal=original.geometry_binding.all_future
 return Predictor,initial,kernel,Adapter,Gear,policy.Policy,feedback,geometry.Geometry,causal

def current_packet(p,*,current,native_tick,feedback):
 b=p.state;enc=feedback.current(p)
 return dict(native_tick=native_tick,sim_time=current['fixed_origin_sim_time']+.01*(native_tick-current['fixed_origin_native']),body=[float(b[0]),float(b[1]),float(b[2]),float(b[3]),float(b[5])],body_lateral=float(b[4]),steering=dict(position=[float(x)for x in enc[:2]],velocity=[float(x)for x in enc[2:]]),controller_memory=dict(last_ctrl=[float(x)for x in p.adapter.last],integral=float(p.adapter.integral)),coupled_episode=bool(p.coupled_episode),parked_target=p.adapter.parked_target,steering_motion_active=bool(getattr(p.adapter,'_steering_motion_active',False)))
