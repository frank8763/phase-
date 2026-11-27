"""Saved current-geometry/feature audit; never render or reevaluate a neural actor."""
from context import R,C,read,load,sha,digest
import copy,math
METHODS=['RP-CCR','DWA','TEB','RPP','MPPI','SVG-MPPI','SCCR','PRIEST','PSF','PCBF']
def verify_record(np,task,k,record,private,receipt,depth_packet,setup,mocap_pos,mocap_quat,route,previous_wp):
 assert record['receipt']==private['receipt']==receipt
 assert k==receipt['packet']['native_tick']and abs(receipt['packet']['sim_time']-.01*k)<=1e-8
 packet=record['sensor_packet'];assembly=load('SCCR_union_audit_assembly',C/'assemble.py');assert set(packet)==assembly.FIELDS
 assert record['sensor_packet_sha256']==digest(packet)and packet['body']==receipt['packet']['body']and packet['native']==k and packet['sim_time']==receipt['packet']['sim_time']
 assert packet['goal_xy']==task['goal_xy']and packet['previous_body_command']==[0.,0.]
 assert packet['rendered_depth24']==depth_packet['depth24']and depth_packet['own_body']==packet['body']and depth_packet['native']==k
 assert record['actor_outputs_not_executed']and record['actual_state_qpos_qvel_ctrl_mocap_time_byte_exact']
 assert record['all_ten_consumer_methods']==METHODS and record['all_ten_equal_sensor_availability']and not record['full_SCCR_control_or_navigation_qualified']
 p=packet['producer_proof'];assert p['actual_fresh_sensor']and p['all_sensor_sources_qualified']and p['no_hidden_actor_truth']and p['native']==k and p['equal_availability_all_ten_methods']and p['previous_action_zero_from_entire_zero_request_journal']
 assert p['registered_profile']=='V2168_PRIMARY_MATCHED_NOISE_UNION'and p['previous_action_units']=='virtual_steer_rad_and_wheel_rad_s'and not p['full_historical_wrapper_cadence_identity']
 # Geometry is reconstructed independently from the actual full-state capture,
 # not trusted from the producer's private circle or risk/phase metadata.
 ids=private['ids'];actor=setup['actor'];assert set(ids)=={'mocap_id','geom_id','radius_m','cylinder_type'}and ids['mocap_id']==actor['mocap_id']and ids['geom_id']==actor['actor_geom_id']and ids['radius_m']==actor['radius_m']==.1
 mid=ids['mocap_id'];quat=np.asarray(mocap_quat[mid]);assert abs(float(quat[0]))==1. and np.array_equal(quat[1:],np.zeros(3))
 xy=np.asarray(mocap_pos[mid,:2],float);assert np.isfinite(xy).all()
 world=dict(native=k,sim_time=receipt['packet']['sim_time'],bounds=[-5.,5.],rectangles=[list(a)for a in setup['known']['known_rectangles']],circles=[list(a)for a in setup['known']['known_circles']]+[[float(xy[0]),float(xy[1]),.1]])
 assert private['world']==world and private['current_only']and private['not_a_consumer_packet']and private['source_sha256']==sha(C/'private_snapshot.py')
 feature_module=load('SCCR_union_audit_rays',C/'union_features.py');features,profile=feature_module.blocks(np,dict(native=k,sim_time=receipt['packet']['sim_time'],body=packet['body']),world,receipt['scan'],task['seed'],setup['noise'])
 assert all(np.array_equal(np.asarray(packet[n],np.float32),np.asarray(v,np.float32))for n,v in features.items())and record['profile']==private['profile']==profile
 original=np.asarray(route['original_virtual_rear_path'],float);converted=original[:,:2]+.3*np.column_stack([np.cos(original[:,2]),np.sin(original[:,2])])
 path=converted.astype(np.float32).tolist();assert path==route['body_center_polyline']==packet['path_world']
 assert np.linalg.norm(converted[0]-task['start_xy'])<=1e-8 and route['public_static_only']and route['no_actor_truth']
 f=assembly.builders(np);v=f['room']();v.robot_xy=np.asarray(packet['body'][:2],np.float32);v.path_world=np.asarray(path,np.float32);v.wp_index=previous_wp;v.goal_xy=np.asarray(task['goal_xy'],np.float32);v._update_waypoint();assert packet['wp_index']==v.wp_index
 # Use the SAVED base action as an arithmetic input only. Backend equivalence
 # is inherited by exact actor body/weights identity, with no extra inference.
 saved_base=np.asarray(record['assembly']['base_action_2'],np.float32);assert saved_base.shape==(2,)and np.isfinite(saved_base).all()and(abs(saved_base)<=1).all()
 obs,parts=assembly.build(np,packet,lambda x:saved_base.copy())
 assert parts==record['assembly']and np.array_equal(obs,np.asarray(record['observation186'],np.float32))
 residual=np.asarray(record['residual_action'],np.float32);assert residual.shape==(2,)and np.isfinite(residual).all()and(abs(residual)<=1).all()
 counts=record['model_counts'];index=[0,5,10].index(k)
 assert counts['actor_constructor_attempts']==counts['actor_constructor_returns']==counts['weight_deserializations_completed']==2
 assert counts['explicit_renderer_constructor_attempts']==counts['explicit_renderer_constructor_returns']==1
 assert counts['forward_attempts']==counts['forward_returns']==2*(index+1)and counts['inflight']is None
 assert counts['internal_factory_policy_and_renderer_counts']is None and counts['internal_torch_work']is None
 return dict(native=k,passed=True,fullstate_current_mocap_geometry_bound=True,primary_noise_profile_byte_exact=True,complete186_arithmetic_byte_exact=True,NN_forward_reexecuted=0,renderer_reexecuted=0),v.wp_index
def audit_saved(np,out,task,source):
 setup=read(out/'physics/SETUP.json');route=read(out/'SCCR_UNION_PUBLIC_ROUTE.json');rows=[];previous_wp=0
 depth=load('SCCR_union_original_depth_audit',C/'depth.py')
 with np.load(out/'FULL_STATE_NPLUS1.npz')as full:
  for i,k in enumerate([0,5,10]):
   path=out/f'SCCR_UNION_{k:06d}.json'
   if not path.exists():continue
   assert len(rows)==i,'SCCR_UNION_NONPREFIX_FRAME_SEQUENCE'
   depth.audit_saved(np,out,k,source)
   row,previous_wp=verify_record(np,task,k,read(path),read(out/f'SCCR_UNION_PRIVATE_{k:06d}.json'),read(out/f'cycle_{i:06d}_origin.json')['receipt'],read(out/f'SCCR_DEPTH_{k:06d}.json')['packet'],setup,full['mocap_pos'][k],full['mocap_quat'][k],route,previous_wp)
   rows.append(row)
 return rows
