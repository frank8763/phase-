"""New private-snapshot/noise-profile software seam on saved data, no audit or models."""
from union_features import R,blocks
from private_snapshot import world_from_arrays
from pathlib import Path
import os,json,copy,hashlib
import numpy as np
S=R/'runs'/Path(__file__).resolve().parent.name;OLD=R/'runs/v2144_sccr_depth_resource_units/components/SCCR/actual'
assert os.sched_getaffinity(0)=={0}and not(S/'RAY_PROFILE_SOFTWARE_PROOF.json').exists()
def read(p):return json.loads(Path(p).read_bytes())
setup=read(OLD/'physics/SETUP.json');known=setup['known'];rows=[];inputs={}
with np.load(OLD/'FULL_STATE_NPLUS1.npz')as z:pos=z['mocap_pos'][[0,5,10]].copy();quat=z['mocap_quat'][[0,5,10]].copy()
for index,k in enumerate([0,5,10]):
 receipt=read(OLD/f'cycle_{index:06d}_origin.json')['receipt'];p=receipt['packet'];m=dict(native=k,sim_time=p['sim_time'],body=p['body']);arrays=dict(mocap_pos=pos[index],mocap_quat=quat[index],geom_size=np.array([[.1,.2,0.]]),geom_type=np.array([123]),geom_bodyid=np.array([0]),body_mocapid=np.array([0]),geom_pos=np.array([[0.,0.,.22]]));ids=dict(mocap_id=0,geom_id=0,radius_m=.1,cylinder_type=123)
 before={n:v.copy()for n,v in arrays.items()};world=world_from_arrays(np,m,known,arrays,ids);v,proof=blocks(np,m,world,receipt['scan'],setup['seed'],setup['noise'])
 assert all(np.array_equal(arrays[n],b)for n,b in before.items())and proof['primary32_measured_meters_byte_exact']
 assert not np.array_equal(np.asarray(v['phase6_lidar32']),np.asarray(v['phase17_lidar32'])),'FUSION_NOISE_INCORRECTLY_DROPPED'
 rows.append(dict(native=k,primary_meter_ranges_byte_exact=True,noise_indices=[proof['lidar_noise_index'],proof['depth_noise_index']],feature_lengths={n:len(x)for n,x in v.items()},input_arrays_unmodified=True,private_geometry_fixture_not_a_live_model=True))
 for file in [OLD/f'cycle_{index:06d}_origin.json',OLD/'FULL_STATE_NPLUS1.npz',OLD/'physics/SETUP.json']:inputs[str(file.relative_to(R))]=hashlib.sha256(file.read_bytes()).hexdigest()
negative=[]
def reject(label,fn):
 try:fn()
 except(AssertionError,KeyError,ValueError):negative.append(label)
 else:raise AssertionError('UNION_SENSOR_NEGATIVE_ACCEPTED:'+label)
bad=dict(ids,radius_m=.2);reject('wrong_actor_radius',lambda:world_from_arrays(np,m,known,arrays,bad))
bad=dict(ids,actor_phase=1.);reject('future_actor_metadata',lambda:world_from_arrays(np,m,known,arrays,bad))
bad=dict(world,native=5);reject('stale_private_world',lambda:blocks(np,m,bad,receipt['scan'],setup['seed'],setup['noise']))
bad=copy.deepcopy(receipt['scan']);bad['ranges'][0]=bad['ranges'][0]-.01 if bad['ranges'][0]>.01 else bad['ranges'][0]+.01;reject('primary_range_mismatch',lambda:blocks(np,m,world,bad,setup['seed'],setup['noise']))
bad=dict(setup['noise'],lidar_call=setup['noise']['lidar_call']+1);reject('wrong_noise_counter',lambda:blocks(np,m,world,receipt['scan'],setup['seed'],bad))
for file in [Path(__file__),Path(__file__).with_name('union_features.py'),Path(__file__).with_name('private_snapshot.py')]:inputs[str(file.relative_to(R))]=hashlib.sha256(file.read_bytes()).hexdigest()
result=dict(passed=True,closed=True,saved_measured_cases=rows,negative_cases=negative,models=0,renderer_constructors=0,neural_inference=0,physics=0,replay=0,physical_audit=0,source_once_claimed=False,private_current_snapshot_and_original_noise_profile_software_passed=True,all_live_union_or_policy_not_yet_qualified=True,source_SHA256=inputs)
(S/'RAY_PROFILE_SOFTWARE_PROOF.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['saved_measured_cases','source_SHA256']}))
