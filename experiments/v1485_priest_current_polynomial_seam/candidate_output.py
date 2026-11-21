"""Bind author polynomial outputs to one current input; no command adapter."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v1485_pure_polynomial_math',C/'polynomial.py');polynomial=importlib.util.module_from_spec(spec);spec.loader.exec_module(polynomial)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def bind(current,reply):
 clean=dict(current);identity=clean.pop('input_sha256');assert digest(clean)==identity
 expected={'kind','schema','run_id','input_sha256','core_identity_sha256','origin_native','origin_sim_time','horizon_s','coordinate_frame','gear','coefficients_x','coefficients_y','optimizer_accounting'}
 assert set(reply)==expected and reply['kind']=='PRIEST_AUTHOR_POLYNOMIAL_PROPOSAL'and reply['schema']==1,'PRIEST_OUTPUT_SCHEMA'
 assert reply['run_id']==current['run_id']and reply['input_sha256']==identity and reply['core_identity_sha256']==current['core_identity_sha256'],'PRIEST_OUTPUT_WRONG_CURRENT_INPUT'
 assert type(reply['origin_native'])is int and reply['origin_native']==current['fixed_origin_native']and type(reply['origin_sim_time'])in(int,float)and reply['origin_sim_time']==current['fixed_origin_sim_time'],'PRIEST_OUTPUT_FIXED_CLOCK_CHANGED'
 assert reply['coordinate_frame']=='REAR_AXLE_WORLD_XY'and reply['horizon_s']==10. and reply['gear']==current['next_segment']['gear']
 polynomial.finite_vector(reply['coefficients_x'],11);polynomial.finite_vector(reply['coefficients_y'],11)
 first=polynomial.sample(reply['coefficients_x'],reply['coefficients_y'],time_s=0.,gear=reply['gear'])
 assert max(abs(a-b)for a,b in zip(first['position'],current['rear_pose_world'][:2]))<=1e-8,'PRIEST_POLYNOMIAL_WRONG_CURRENT_REAR_POSITION'
 assert max(abs(a-b)for a,b in zip(first['velocity'],current['rear_velocity_world']))<=1e-8,'PRIEST_POLYNOMIAL_WRONG_CURRENT_REAR_VELOCITY'
 accounting=reply['optimizer_accounting']
 assert set(accounting)=={'optimizer_calls','iterations_completed','mathematical_candidate_evaluations','inflight_unknown','author_core_source_sha256'}
 assert accounting['author_core_source_sha256']==current['core_identity']['author_members'][0]['sha256']
 for key in ['optimizer_calls','iterations_completed','mathematical_candidate_evaluations']:
  assert accounting[key]is None or(type(accounting[key])is int and accounting[key]>=0),'PRIEST_OPTIMIZER_ACCURATE_OR_UNKNOWN_REQUIRED'
 assert type(accounting['inflight_unknown'])is bool
 value=dict(kind='BOUND_PRIEST_POLYNOMIAL_PROPOSAL',schema=1,input_sha256=identity,core_identity_sha256=current['core_identity_sha256'],reply=copy.deepcopy(reply),initial_sample=first,
  fixed_origin_native=current['fixed_origin_native'],fixed_origin_sim_time=current['fixed_origin_sim_time'],initial_acceleration_source_qualified=False,complete_current_response_witness_passed=False,independent_audit_passed=False,actual_control_domain_qualified=False,polynomial_samples_are_not_physical_or_response_integrations=True,control_emitted=False,physical_admission=False)
 return dict(value,proposal_sha256=digest(value))

def reference_at(proposal,*,native_tick):
 clean=dict(proposal);identity=clean.pop('proposal_sha256');assert digest(clean)==identity
 assert type(native_tick)is int and proposal['fixed_origin_native']<=native_tick<=proposal['fixed_origin_native']+1000
 reply=proposal['reply'];sample=polynomial.sample(reply['coefficients_x'],reply['coefficients_y'],time_s=(native_tick-proposal['fixed_origin_native'])*.01,gear=reply['gear'])
 return dict(sample,native_tick=native_tick,sim_time=proposal['fixed_origin_sim_time']+(native_tick-proposal['fixed_origin_native'])*.01,fixed_origin_native=proposal['fixed_origin_native'])

def actual_command(*_args,**_kwargs):
 raise RuntimeError('PRIEST_POLYNOMIAL_IS_NOT_AN_ACTUATOR_POLICY_CURRENT_RESPONSE_AND_ACTUAL_SHARED_CONTROLLER_NOT_QUALIFIED')
