"""One archived t0 causal origin; never a current live vehicle measurement."""
from common import R,C,S,read,put,sha,digest,load
import math,os,types
def main():
 os.sched_setaffinity(0,{7});assert not(S/'PREPARE_ONCE.json').exists();put(S/'PREPARE_ONCE.json',dict(models=0,CPU=7));P=R/'runs/v2052_svg_registered_causal_solver';saved=read(P/'INPUT.json');packet=saved['origin']['origin_packet'];request=saved['causal_request'];assert packet==read(R/saved['source_packet_path'])and sha(R/saved['source_packet_path'])==saved['source_packet_sha256']and packet['native_tick']==0 and packet['sim_time']==0.
 import numpy as np
 statepath=R/'runs/v2027_mppi_journal_snapshot_consistency/actual/INITIAL_FULL_STATE.npz'
 with np.load(statepath,allow_pickle=False)as z:full={k:z[k].tolist()for k in z.files}
 assert full['time']==0.;boundary=load('PRIEST_original_causal_boundary',R/'experiments/v1485_priest_current_polynomial_seam/causal_boundary.py');kin=boundary.rear_kinematics(full);b=packet['body'];assert abs(kin['position'][0]-(b[0]-.3*math.cos(b[2])))<=1e-8 and abs(kin['position'][1]-(b[1]-.3*math.sin(b[2])))<=1e-8
 hint=boundary.initial_hint(full,None,native_tick=0);assert hint['kind']=='CANONICAL_REST_DECLARED_ZERO_POLYNOMIAL_ACCELERATION_TARGET'
 public=read(R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json');port=load('original_PRIEST_body_exact_CPU_port',R/'experiments/v1487_priest_optimizer_contract/cpu_source.py').prepare_cpu_source();port={k:v for k,v in port.items()if k!='source'}
 identity=dict(author_members=[dict(path='runs/v1484_baseline_disposition_priest/upstream/priest/src/mpc_non_dy.py',sha256=port['author_sha256'])],scope='ARCHIVED_T0_PRIEST_PROPOSAL_COMPONENT_NOT_FACTORY_IDENTITY',canonical_packet_path=saved['source_packet_path'],canonical_packet_file_sha256=saved['source_packet_sha256'],canonical_initial_fullstate_path=str(statepath.relative_to(R)),canonical_initial_fullstate_file_sha256=sha(statepath),author_port=port,public_map_sha256=digest(public),current_wire_request_sha256=digest(request))
 core=digest(identity);manifest=digest(dict(source_identity=identity,preparation_source_sha256=sha(C/'prepare.py')));snapshot=dict(periodic=None,online_actor_truth=False,last_observed_time=None);gear=1
 current=dict(kind='PHASE_ARCHIVED_CAUSAL_PRIEST_T0_INPUT',schema=1,input_role='SAVED_ORIGINAL_ACTUAL_T0_NOT_FRESH_WIRE',run_id=C.name,core_identity_sha256=core,core_identity=identity,source_manifest_sha256=manifest,origin=packet,fullstate=full,fullstate_sha256=digest(full),fixed_origin_native=0,fixed_origin_sim_time=0.,rear_pose_world=[*kin['position'],kin['yaw']],rear_velocity_world=kin['velocity'],author_initial_boundary_hint=hint,next_segment=dict(gear=gear,poses=saved['path']),causal_snapshot=snapshot,causal_snapshot_sha256=digest(snapshot),causal_forecast=None,observation_stage='NO_DYNAMIC_RETURN_YET_NO_MEASURED_FUTURE',public_map_sha256=digest(public),proposal_only=True,physical_admission=False)
 # This pre-discovery origin must really have no causal dynamic observation;
 # the planner receives public geometry only, never actor phase/truth.
 assert not packet['dynamic_discovered'];current['input_sha256']=digest(current)
 prepared=types.SimpleNamespace(hot_identity=lambda:core,source_manifest_sha256=manifest,public_map_sha256=digest(public),public_map=public)
 reqmod=load('original_PRIEST_request_array_builder',R/'experiments/v1487_priest_optimizer_contract/optimizer_request.py');req=reqmod.build(current,prepared=prepared,boundary_state=boundary.boundary_state(current),port_identity=port)
 assert req['constructor_kwargs']['num_batch']==110 and req['constructor_kwargs']['maxiter_cem']==12 and req['dynamic_points_world']==[]
 put(S/'CURRENT_INPUT.json',current);put(S/'OPTIMIZER_REQUEST.json',req);put(S/'PREPARATION.json',dict(passed=True,models=0,optimizer_queries=0,physics=0,scope='NEW_ARCHIVED_T0_CAUSAL_PROPOSAL_INPUT_NOT_OLD6005_REPEAT',request_sha256=req['request_sha256'],input_sha256=current['input_sha256'],zero_acceleration_explicit_canonical_rest_planner_hint=True,actual_current_wire_or_plant=False,all_original_50static110batch12CEM13projection_parameters_retained=True,author_optimizer_internal_kinematic_work=None))
 print(__import__('json').dumps(read(S/'PREPARATION.json')))
if __name__=='__main__':main()
