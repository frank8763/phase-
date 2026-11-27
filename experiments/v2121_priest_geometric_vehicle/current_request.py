"""Fresh measured t0 whitelist; actor/fullstate truth is never sent to solver."""
import math,types
from context import R,C,read,load,digest,sha
OLD=R/'experiments/v1485_priest_current_polynomial_seam'
def build(np,receipt,fullstate,selected,source,*,run_id):
 observation=load('PRIEST_original_current_receipt',C/'observation.py');p=observation.verify(receipt,0,0.)
 assert p['native_tick']==0 and not p['dynamic_discovered']and not p['steering_motion_active']and p.get('parked_target')is None
 boundary=load('PRIEST_original_rear_boundary',OLD/'causal_boundary.py');kin=boundary.rear_kinematics(fullstate);hint=boundary.initial_hint(fullstate,None,native_tick=0)
 assert hint['kind']=='CANONICAL_REST_DECLARED_ZERO_POLYNOMIAL_ACCELERATION_TARGET'and selected['gear']==1
 assert max(abs(a-b)for a,b in zip(kin['position'],[p['body'][0]-.3*math.cos(p['body'][2]),p['body'][1]-.3*math.sin(p['body'][2])]))<=1e-8
 public=read(R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json');port=load('PRIEST_body_exact_CPU_source',R/'experiments/v1487_priest_optimizer_contract/cpu_source.py').prepare_cpu_source();port={k:v for k,v in port.items()if k!='source'}
 identity=dict(author_members=[dict(path='runs/v1484_baseline_disposition_priest/upstream/priest/src/mpc_non_dy.py',sha256=port['author_sha256'])],scope='FRESH_CURRENT_PRIEST_ORIGINAL_VEHICLE_COMPONENT',author_port=port,public_map_sha256=digest(public),current_receipt_sha256=digest(receipt))
 core=digest(identity);manifest=digest(dict(builder_sha256=sha(C/'current_request.py'),core_identity=identity));snapshot=dict(periodic=None,online_actor_truth=False,last_observed_time=None)
 current=dict(kind='PHASE_PRIEST_CURRENT_POLYNOMIAL_INPUT',schema=1,run_id=run_id,core_identity_sha256=core,core_identity=identity,source_manifest_sha256=manifest,origin=p,fullstate_sha256=digest(fullstate),fixed_origin_native=0,fixed_origin_sim_time=0.,rear_pose_world=[*kin['position'],kin['yaw']],rear_velocity_world=kin['velocity'],author_initial_boundary_hint=hint,next_segment=selected,causal_snapshot=snapshot,causal_snapshot_sha256=digest(snapshot),causal_forecast=None,observation_stage='NO_DYNAMIC_RETURN_YET_NO_MEASURED_FUTURE',public_map_sha256=digest(public),proposal_only=True,physical_admission=False,source_receipt_sha256=digest(receipt),fullstate_or_actor_truth_transmitted=False)
 current['input_sha256']=digest(current)
 prepared=types.SimpleNamespace(hot_identity=lambda:core,source_manifest_sha256=manifest,public_map_sha256=digest(public),public_map=public)
 request=load('PRIEST_exact_original_request_arrays',R/'experiments/v1487_priest_optimizer_contract/optimizer_request.py').build(current,prepared=prepared,boundary_state=boundary.boundary_state(current),port_identity=port)
 assert request['constructor_kwargs']['num_batch']==110 and request['constructor_kwargs']['maxiter_cem']==12 and not request['dynamic_points_world']
 assert 'fullstate'not in current and 'mocap_pos'not in current and 'mocap_pos'not in request
 return dict(current=current,request=request)
