"""Zero-model independent recovery of the already-saved actual NS preflight."""
import os,sys,json,gzip,copy,hashlib,math
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1065_preflight_metadata_continuation_20261111';sys.path.insert(0,str(R/'experiments/v1064_cpu_backend_entry'))
from resource_policy import apply
apply();sys.path.insert(0,str(C))
from initial_contract import check_setup
import numpy as np
out=R/'runs/v858_nav2_verified/v1064/t0_dev_north_south';result=json.loads((out/'RESULT.json').read_text());setup=json.loads((out/'physics/SETUP.json').read_text());meta=json.loads((R/'runs/v1061_three_route_readiness/NORTH_SOUTH_T0_METADATA.json').read_text());task=json.loads((R/'experiments/v1064_cpu_backend_entry/TASK_t0_dev_north_south.json').read_text());assert result['passed']is False and result['error']=="KeyError('actuator_ids')";assert check_setup(setup,meta);physical=result['physical'];assert result['model_initializations']==1 and physical['actual_native']==physical['fully_recorded_native']==physical['root_guard_native_count']==result['navigation_native']==result['own_replay_native']==result['private_mujoco_native']==0;assert physical['minimum_actual_clearance_m']>=.15 and physical['minimum_self_margin_m']>=0 and physical['bad_contacts']==0 and physical['first_actor_detection']is None;assert abs(np.array(physical['final_body'])-meta['packet']['body']).max()<=1e-8
with gzip.open(out/'physics/SENSORS.json.gz','rt')as f:scans=json.load(f)
assert len(scans)==3 and scans[0]==scans[1]==scans[2]and scans[-1]['native_tick']==0 and scans[-1]['time']==0.;assert json.loads((out/'physics/BODY_COMMANDS.json').read_text())==[]
with np.load(out/'physics/INITIAL_STATE.npz')as data:assert np.isfinite(data['state']).all()
provenance=json.loads((out/'physics/paired/INITIALIZATION_PROVENANCE.json').read_text());assert provenance['gpu_rendering_disabled']and provenance['cpu_render_backend']['actual_context_module']=='mujoco.osmesa'and provenance['cpu_render_backend']['actual_OpenGL_dispatch_module']=='OpenGL.platform.osmesa'
assert setup['actor']['phase_rad']==task['phase']and setup['actor']['radius_m']==.1 and setup['actor']['amplitude_m']==.25 and setup['actor']['maximum_speed_m_s']==.08
negative=[]
for label in ['changed_dt','duplicate_actuators','changed_limits','changed_known_map','changed_slew']:
 candidate=copy.deepcopy(setup)
 if label=='changed_dt':candidate['dt']=.02
 elif label=='duplicate_actuators':candidate['actuator_ids'][1]=candidate['actuator_ids'][0]
 elif label=='changed_limits':candidate['limits'][0][0]-=.1
 elif label=='changed_known_map':candidate['known']['known_circles'][0][0]+=.1
 else:candidate['slew_per_second'][0]+=.1
 try:check_setup(candidate,meta)
 except AssertionError:negative.append(label)
 else:raise AssertionError('CONTRACT_MUTATION_ACCEPTED '+label)
reference=dict(passed=True,status='INDEPENDENT_SAVED_T0_METADATA_AUDIT_PASS',original_result_passed=False,original_failure_retained=True,output=str(out),setup=setup,summary=physical,scan=scans[-1],body=physical['final_body'],task=task,model_initializations=1,navigation_native=0,own_replay_native=0,private_mujoco_native=0,source_receipts={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [out/'RESULT.json',out/'physics/SETUP.json',out/'physics/INITIAL_STATE.npz',out/'physics/SENSORS.json.gz',out/'physics/paired/INITIALIZATION_PROVENANCE.json']});(O/'REUSED_PREFLIGHTS.json').write_text(json.dumps(dict(t0_dev_north_south=reference),indent=2)+'\n');audit=dict(passed=True,models=0,integrations=0,actual_existing_vehicle_initializations=1,reused_native_zero_only=True,original_failed_result_unchanged=True,public_schema_exact=True,independent_private_actuator_schema_valid=True,actual_CPU_backend_verified_from_saved_initialization=True,negative_cases=negative,preflight_reinitialization_required=False,physical_navigation_not_authorized=True);(O/'QUALIFICATION.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))
