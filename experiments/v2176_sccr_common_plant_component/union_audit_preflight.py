"""Finite pure audit checks with explicitly constructed nonphysical records."""
from context import R,C,read,sha,digest,load
from pathlib import Path
import os,json,copy,time
import numpy as np
S=R/'runs'/C.name;OLD=R/'runs/v2144_sccr_depth_resource_units/components/SCCR/actual'
assert os.sched_getaffinity(0)=={0}and not(S/'UNION_AUDIT_PREFLIGHT.json').exists()
audit=load('new_union_audit_software',C/'union_audit.py');assembly=load('new_union_audit_assembly_fixture',C/'assemble.py');rays=load('new_union_audit_ray_fixture',C/'union_features.py')
task=read(S/'components/SCCR/PILOT_TASK.json');setup=read(OLD/'physics/SETUP.json');public=read(R/'runs/v2170_sccr_live_source_scope/components/SCCR/actual/SCCR_UNION_PUBLIC_ROUTE.json');public=dict(public,passed=True,original_virtual_rear_route=public['original_virtual_rear_path'])
route=dict(original_virtual_rear_path=public['original_virtual_rear_route'],body_center_polyline=public['body_center_polyline'],public_static_only=True,no_actor_truth=True)
assert public['passed'];rows=[];inputs=[];previous_wp=0
with np.load(OLD/'FULL_STATE_NPLUS1.npz')as z:full={n:z[n][[0,5,10]].copy()for n in ['mocap_pos','mocap_quat']}
start=time.monotonic()
try:
 for i,k in enumerate([0,5,10]):
  receipt=read(OLD/f'cycle_{i:06d}_origin.json')['receipt'];depth=read(OLD/f'SCCR_DEPTH_{k:06d}.json')['packet'];xy=full['mocap_pos'][i][0,:2]
  world=dict(native=k,sim_time=receipt['packet']['sim_time'],bounds=[-5.,5.],rectangles=setup['known']['known_rectangles'],circles=setup['known']['known_circles']+[[float(xy[0]),float(xy[1]),.1]])
  features,profile=rays.blocks(np,dict(native=k,sim_time=receipt['packet']['sim_time'],body=receipt['packet']['body']),world,receipt['scan'],task['seed'],setup['noise'])
  view=assembly.builders(np)['room']();view.robot_xy=np.asarray(receipt['packet']['body'][:2],np.float32);view.path_world=np.asarray(route['body_center_polyline'],np.float32);view.wp_index=previous_wp;view.goal_xy=np.asarray(task['goal_xy'],np.float32);view._update_waypoint()
  packet=dict(native=k,sim_time=receipt['packet']['sim_time'],body=receipt['packet']['body'],goal_xy=task['goal_xy'],path_world=route['body_center_polyline'],wp_index=view.wp_index,previous_body_command=[0.,0.]if k==0 else[.2,2.],rendered_depth24=depth['depth24'],**features,producer_proof=dict(actual_fresh_sensor=True,all_sensor_sources_qualified=True,no_hidden_actor_truth=True,native=k,equal_availability_all_ten_methods=True,registered_profile='V2168_PRIMARY_MATCHED_NOISE_UNION',previous_action_units='virtual_steer_rad_and_wheel_rad_s',previous_action_from_committed_same_episode_prefix=True,episode_id=task['run_id'],previous_action_commit=None if k==0 else dict(episode_id=task['run_id'],origin_native=k-5,end_native=k,applied_prefix_sha256='EXPLICIT_SOFTWARE_FIXTURE'),full_historical_wrapper_cadence_identity=False))
  obs,parts=assembly.build(np,packet,lambda x:np.array([.125,-.25],np.float32))
  record=dict(sensor_packet=packet,sensor_packet_sha256=digest(packet),receipt=receipt,profile=profile,assembly=parts,observation186=obs.tolist(),residual_action=[.25,-.125],actual_commands_not_implied_by_capture=True,actor_outputs_used_for_controller_proposal=(k in [0,5]),all_ten_consumer_methods=audit.METHODS,all_ten_equal_sensor_availability=True,actual_state_qpos_qvel_ctrl_mocap_time_byte_exact=True,model_counts=dict(actor_constructor_attempts=2,actor_constructor_returns=2,weight_deserializations_completed=2,forward_attempts=2*(i+1),forward_returns=2*(i+1),inflight=None,internal_factory_policy_and_renderer_counts=None,internal_torch_work=None,explicit_renderer_constructor_attempts=1,explicit_renderer_constructor_returns=1),full_SCCR_control_or_navigation_qualified=False)
  private=dict(world=world,ids=dict(mocap_id=0,geom_id=setup['actor']['actor_geom_id'],radius_m=.1,cylinder_type=123),receipt=receipt,profile=profile,current_only=True,not_a_consumer_packet=True,source_sha256=sha(C/'private_snapshot.py'))
  previous=dict(episode_id=task['run_id'],virtual_action=packet['previous_body_command'],commit=packet['producer_proof']['previous_action_commit'])
  args=[np,task,k,record,private,receipt,depth,setup,full['mocap_pos'][i],full['mocap_quat'][i],route,previous_wp,previous]
  row,previous_wp=audit.verify_record(*args);rows.append(row);inputs.append(args)
 negative=[]
 def reject(label,args):
  try:audit.verify_record(*args)
  except(AssertionError,ValueError,KeyError):negative.append(label)
  else:raise AssertionError('AUDIT_MUTATION_ACCEPTED:'+label)
 # Alter the captured mocap, then alter only the producer's private geometry.
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[8][0,0]+=.2;reject('captured_mocap_disagrees_with_sensor_world',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[4]['world']['circles'][-1][0]+=.2;reject('private_geometry_changed',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['sensor_packet']['body'][0]+=.1;a[3]['sensor_packet_sha256']=digest(a[3]['sensor_packet']);reject('receipt_body_mismatch',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['sensor_packet']['phase6_lidar32'][0]=.25;a[3]['sensor_packet_sha256']=digest(a[3]['sensor_packet']);reject('sensor_ray_mismatch',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['sensor_packet']['actor_phase']=1.;a[3]['sensor_packet_sha256']=digest(a[3]['sensor_packet']);reject('private_actor_field_in_consumer_packet',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['sensor_packet']['previous_body_command']=[.1,0.];a[3]['sensor_packet_sha256']=digest(a[3]['sensor_packet']);reject('unjustified_nonzero_previous_actuation',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['observation186'][0]+=.1;reject('full186_changed',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['assembly']['base_action_2']=[.5,.5];reject('saved_base_action_unbound_to186',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['residual_action']=[1.1,0.];reject('residual_outside_original_domain',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['model_counts']['forward_returns']=5;reject('forward_count_gap',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['model_counts']['inflight']=['forward',186,10];reject('unclosed_forward',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['all_ten_consumer_methods']=audit.METHODS[:-1];reject('unequal_sensor_availability',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['sensor_packet']['wp_index']=100;a[3]['sensor_packet_sha256']=digest(a[3]['sensor_packet']);reject('waypoint_not_from_measured_source',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['profile']['lidar_noise_index']+=1;reject('noise_counter_changed',a)
 a=[np]+[copy.deepcopy(value)for value in inputs[-1][1:]];a[3]['sensor_packet']['rendered_depth24'][0]+=.1;a[3]['sensor_packet_sha256']=digest(a[3]['sensor_packet']);reject('rendered_depth_unbound',a)
 v=dict(passed=True,closed=True,scope='INDEPENDENT_UNION_ARITHMETIC_SOFTWARE_ONLY_EXPLICIT_FAKE_POLICY_OUTPUTS',saved_measured_fixture_cases=rows,negative_cases=negative,models=0,NN_inference=0,render=0,physics=0,replay=0,source_once_claimed=False,synthetic_packets_in_memory_only_not_new_live_evidence=True,live_union_audit_not_executed=True,wall_s=time.monotonic()-start,source_SHA256={str(p.relative_to(R)):sha(p)for p in [Path(__file__),C/'union_audit.py',C/'assemble.py',C/'union_features.py',R/'runs/v2170_sccr_live_source_scope/components/SCCR/actual/SCCR_UNION_PUBLIC_ROUTE.json']})
 (S/'UNION_AUDIT_PREFLIGHT.json').write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');print(json.dumps({k:x for k,x in v.items()if k not in ['source_SHA256','negative_cases','saved_measured_fixture_cases']}))
except BaseException as e:
 import traceback
 p=next(S/f'UNION_AUDIT_PREFLIGHT_ATTEMPT{i:02d}.json'for i in range(1,10)if not(S/f'UNION_AUDIT_PREFLIGHT_ATTEMPT{i:02d}.json').exists());p.write_text(json.dumps(dict(passed=False,error=repr(e),traceback=traceback.format_exc(),models=0,physics=0,source_once_claimed=False),indent=2)+'\n');raise
