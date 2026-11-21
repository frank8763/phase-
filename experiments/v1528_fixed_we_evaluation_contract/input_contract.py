"""Source-envelope contract. No model factory, FFI, optimizer or actual permission."""
import copy,hashlib,json,math
SCHEMA=1
CASE=('WEST_EAST',10060001,1.5107128341898335)
ROLES={'SAVED_ACTUAL_MODEL_ONLY','FRESH_ACTUAL_CURRENT'}
MODEL_VARIANTS={'V1159_BOUNDED_STEERING_LOAD_OVER_V1114','V1114_COUPLED_SCALAR_FEEDBACK'}
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def finite(x):return type(x)in(int,float)and math.isfinite(x)
def vector(x,n):return isinstance(x,list)and len(x)==n and all(finite(v)for v in x)
def safe(value,ancestors=None,depth=0):
 # Invalid/cyclic software inputs remain diagnosable without pretending finite state.
 if value is None or type(value)in(bool,int,str):return value
 if type(value)is float:return value if math.isfinite(value)else {'invalid_numeric_repr':repr(value)}
 if depth>32:return {'invalid_nesting_depth':depth}
 if not isinstance(value,(list,dict)):return {'invalid_type_repr':repr(value)[:1024]}
 ancestors=set()if ancestors is None else ancestors
 if id(value)in ancestors:return {'invalid_cyclic_container':type(value).__name__}
 ancestors=ancestors|{id(value)}
 if isinstance(value,list):return [safe(x,ancestors,depth+1)for x in value]
 return {str(k):safe(v,ancestors,depth+1)for k,v in value.items()}
class SourceRefusal(AssertionError):
 def __init__(self,message,proof,save_error=None):super().__init__(message);self.proof=proof;self.save_error=save_error

def inspect(raw,*,source_graph_sha256):
 """Accumulate every available check; never fabricate a sensor timestamp or state."""
 checks={};errors=[]
 def check(name,test):
  try:checks[name]=bool(test())
  except (KeyError,TypeError,ValueError,OverflowError,IndexError,AttributeError):checks[name]=False
  if not checks[name]:errors.append(name)
 check('mapping',lambda:isinstance(raw,dict))
 check('fixed_case_seed_phase',lambda:(raw['case_id'],raw['seed'],raw['phase'])==CASE)
 check('source_role',lambda:raw['source_role']in ROLES)
 check('explicit_model_variant',lambda:raw['model_variant']in MODEL_VARIANTS)
 check('source_graph_identity',lambda:raw['source_graph_sha256']==source_graph_sha256 and isinstance(source_graph_sha256,str)and len(source_graph_sha256)==64)
 check('schema',lambda:type(raw['schema'])is int and raw['schema']==SCHEMA)
 check('run_identity',lambda:isinstance(raw['run_id'],str)and 0<len(raw['run_id'])<=128)
 check('native_clock',lambda:type(raw['packet']['native_tick'])is int and raw['packet']['native_tick']>=0 and finite(raw['packet']['sim_time'])and abs(raw['packet']['sim_time']-.01*raw['packet']['native_tick'])<=1e-8)
 check('body_and_lateral',lambda:vector(raw['packet']['body'],5)and finite(raw['packet']['body_lateral']))
 check('measured_steering_schema',lambda:set(raw['packet']['steering'])=={'position','velocity','native_tick','measured_at'}and vector(raw['packet']['steering']['position'],2)and vector(raw['packet']['steering']['velocity'],2))
 check('measurement_origin',lambda:raw['packet']['steering']['native_tick']==raw['packet']['native_tick']and finite(raw['packet']['body_measured_at'])and raw['packet']['body_measured_at']==raw['packet']['steering']['measured_at'])
 check('control_memory',lambda:set(raw['packet']['controller_memory'])=={'last_ctrl','integral'}and vector(raw['packet']['controller_memory']['last_ctrl'],4)and finite(raw['packet']['controller_memory']['integral']))
 check('explicit_current_mode',lambda:all(type(raw['packet'][k])is bool for k in ['coupled_episode','steering_motion_active'])and (not raw['packet']['steering_motion_active']or raw['packet']['coupled_episode']))
 check('method_memory_not_measured_sensor',lambda:raw['method_memory']['actual_sensor_claim']is False and raw['method_memory']['kind']=='EXPLICIT_METHOD_STATE_SEPARATE_FROM_PHYSICAL_PACKET')
 check('explicit_load_epoch',lambda:raw['model_variant']!='V1159_BOUNDED_STEERING_LOAD_OVER_V1114'or type(raw['method_memory']['steering_load_episode'])is bool and type(raw['method_memory']['epoch_native'])is int and 0<=raw['method_memory']['epoch_native']<=raw['packet']['native_tick']and isinstance(raw['method_memory']['epoch_policy_id'],str)and len(raw['method_memory']['epoch_policy_id'])>0 and isinstance(raw['method_memory']['source_receipt_sha256'],str)and len(raw['method_memory']['source_receipt_sha256'])==64)
 check('plain_V1114_does_not_acquire_load_state',lambda:raw['model_variant']!='V1114_COUPLED_SCALAR_FEEDBACK'or raw['method_memory']['steering_load_episode']is None and raw['method_memory']['epoch_native']is None and raw['method_memory']['epoch_policy_id']=='NOT_APPLICABLE_TO_PLAIN_V1114')
 check('parked_target',lambda:raw['packet']['parked_target']is None or finite(raw['packet']['parked_target']))
 check('continuous_mode_envelope',lambda:raw['mode_history']['canonical_origin_native']==0 and raw['mode_history']['covered_native']==raw['packet']['native_tick']and all(raw['mode_history'][k]==raw['packet'][k]for k in ['coupled_episode','steering_motion_active','parked_target']))
 check('gear_clock',lambda:type(raw['gear_memory']['gear'])is int and raw['gear_memory']['gear']in[-1,0,1]and type(raw['gear_memory']['last_tick'])is int and raw['gear_memory']['last_tick']==raw['packet']['native_tick']-1 and (raw['gear_memory']['brake_start']is None or type(raw['gear_memory']['brake_start'])is int and 0<=raw['gear_memory']['brake_start']<raw['packet']['native_tick']))
 check('fullstate_schema',lambda:set(raw['fullstate'])=={'time','qpos','qvel','ctrl','mocap_pos','mocap_quat'}and vector(raw['fullstate']['qpos'],20)and vector(raw['fullstate']['qvel'],19)and vector(raw['fullstate']['ctrl'],11)and isinstance(raw['fullstate']['mocap_pos'],list)and len(raw['fullstate']['mocap_pos'])==1 and vector(raw['fullstate']['mocap_pos'][0],3)and len(raw['fullstate']['mocap_quat'])==1 and vector(raw['fullstate']['mocap_quat'][0],4))
 check('fullstate_clock',lambda:raw['fullstate']['time']==raw['packet']['sim_time'])
 check('fullstate_digest',lambda:digest(raw['fullstate'])==raw['fullstate_sha256'])
 check('causal_snapshot_digest',lambda:digest(raw['causal_snapshot'])==raw['causal_snapshot_sha256'])
 check('causal_source_only',lambda:raw['causal_snapshot']['online_actor_truth']is False and raw['causal_snapshot']['periodic']is not None and finite(raw['causal_snapshot']['last_observed_time'])and raw['causal_snapshot']['last_observed_time']<=raw['packet']['sim_time']+1e-8)
 check('canonical_coverage_descriptor',lambda:raw['provenance']['canonical_origin_native']==0 and raw['provenance']['applied_actions']==raw['packet']['native_tick']and raw['provenance']['state_rows']==raw['packet']['native_tick']+1 and raw['provenance']['contact_rows']==raw['packet']['native_tick']+1 and raw['provenance']['root_guard_native']==raw['packet']['native_tick']and raw['provenance']['unrecorded_actual_gap']==0)
 check('source_receipt_identities',lambda:all(isinstance(raw['provenance'][k],str)and len(raw['provenance'][k])==64 for k in ['state_packet_binding_proof_sha256','applied_journal_sha256','causal_source_receipt_sha256','model_setup_sha256','public_map_sha256']))
 check('saved_role_explicit_not_wire',lambda:raw['source_role']!='SAVED_ACTUAL_MODEL_ONLY'or raw['provenance']['not_fresh_wire']is True and raw['physical_permission']is False)
 # This draft deliberately cannot manufacture a successful actual-current capture.
 check('fresh_current_capture_qualified',lambda:raw['source_role']!='FRESH_ACTUAL_CURRENT')
 check('no_actual_or_model_permission',lambda:raw['physical_permission']is False and raw['models_authorized']is False)
 try:clean=copy.deepcopy(raw);identity=clean.pop('input_sha256');identity_ok=digest(clean)==identity
 except (TypeError,KeyError,ValueError,OverflowError,AttributeError):identity_ok=False
 check('complete_envelope_digest',lambda:identity_ok)
 return dict(source_envelope_checks_passed=bool(all(checks.values())),checks=checks,first_failed_check=errors[0]if errors else None,failed_checks=errors,source_graph_sha256=source_graph_sha256,original_envelope=safe(raw),model_projection_binding_verified=False,mode_history_numerical_recompute_verified=False,source_receipts_actual_content_verified=False,steering_load_state_qualified=False,method_state_receipt_content_verified=False,causal_support_geometry_qualified=False,physical_permission=False,models_authorized=False,actual_capture_qualified=False,navigation_qualified=False)

def validate(raw,*,source_graph_sha256,save_proof):
 proof=inspect(raw,source_graph_sha256=source_graph_sha256);first=None if proof['source_envelope_checks_passed']else 'CURRENT_WE_EVALUATION_SOURCE_REFUSED:'+str(proof['first_failed_check']);save_error=None
 try:save_proof(proof)
 except BaseException as error:save_error=repr(error)
 if first is not None or save_error is not None:raise SourceRefusal(first or 'CURRENT_WE_EVALUATION_PROOF_SAVE_FAILED',proof,save_error)
 return proof

def authorize_model(*_args,**_kwargs):
 # No fake complete gate or old source/worker success can activate this draft.
 raise SourceRefusal('CURRENT_WE_EVALUATION_BACKEND_NOT_IMPLEMENTED_OR_ADMITTED',dict(models_authorized=False,physical_permission=False))
