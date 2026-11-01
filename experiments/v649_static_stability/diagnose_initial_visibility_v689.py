"""Zero-integration reconstruction of the registered 8m initialization failure."""
from pathlib import Path
import json,gzip,math,hashlib,sys
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v689_dynamic_route_commitment';pair=root/'teacher8m/paired';cell=pair/'geometry_memory';src=repo/'experiments/v689_dynamic_route_commitment';sys.path.insert(0,str(src))
from motion_tracker import capsule_constraints
read=lambda p:json.loads(p.read_text())
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
assert len(packets)==1;packet=packets[0];config=read(pair/'DYNAMIC_PROTOCOL.json');protocol=read(pair/'STATIC_PROTOCOL.json');interrupted=read(cell/'interrupted.json');completion=read(pair/'completion.json');state=json.loads((cell/'motion_estimate.jsonl').read_text());coverage=json.loads((cell/'forecast_coverage.jsonl').read_text())
origin=np.asarray(packet['xy']);center=np.asarray(config['anchor_xy'])+np.asarray(config['axis_xy'])*config['amplitude_m']*np.sin(config['phase_rad']);distance=float(np.linalg.norm(center-origin));entry=distance-config['radius_m'];sample=float(math.ceil(entry/.08-1e-7)*.08)
sensor=[];recreated=[]
for name,b,sigma in [('lidar',.06,.02),('depth',.09,.03)]:
 R=packet[name+'_max_range'];values=np.asarray(packet[name]);ranges=np.clip(values,0,1)*R;angles=(np.arange(len(values))*2*np.pi/len(values)if name=='lidar'else np.linspace(-np.deg2rad(35),np.deg2rad(35),len(values)))+packet['yaw'];keep=(ranges>.05)&(ranges<R-b-1e-5)
 bearing=math.atan2(*(center-origin)[::-1]);difference=np.abs((angles-bearing+np.pi)%(2*np.pi)-np.pi);i=int(np.argmin(difference));sensor.append({'sensor':name,'center_bearing_beam_index':i,'measured_range_m':float(ranges[i]),'accepted_hit_upper_bound_m':R-b-1e-5,'center_beam_kept':bool(keep[i]),'ideal_first_sample_kept_with_zero_noise':bool(sample<R-b-1e-5),'noise_bound_m':b})
 for angle,z in zip(angles[keep],ranges[keep]):recreated.append([*origin,np.cos(angle),np.sin(angle),z,b,sigma])
rays=np.asarray(recreated).reshape(-1,7);A,b,used=capsule_constraints(rays,protocol['known_rectangles'],protocol['known_circles'])
checks={'exact_packet_filter_reproduced':np.array_equal(rays,np.asarray(packet['rays'])),'no_certified_unknown_returns':used==state['certified_unknown_rays']==0,'failure_is_initial_no_observation':coverage['reason']=='NO_INITIAL_ACTOR_OBSERVATION'and state['center']is None,'zero_actual_navigation':interrupted['public_steps']==interrupted['physics_steps']==0,'original_completion_failed_preserved':completion['status']=='FAILED'and completion['error']['message']=='EVALUATOR_FORECAST_COVERAGE_BREACH'}
out={'status':'INITIAL_VISIBILITY_FAILURE_RECONSTRUCTED'if all(checks.values())else'FAIL','checks':checks,'start_xy':origin.tolist(),'actor_t0_xy_evaluator_only':center.tolist(),'center_distance_m':distance,'physical_circle_entry_distance_m':entry,'ideal_008m_first_hit_sample_m':sample,'sensor_checks':sensor,'retained_all_sensor_rays':len(rays),'certified_unknown_rays':used,'gradient_updates':0,'robot_integrations':0,'new_navigation':0,'interpretation':'6m to8m moved start from-3to-4 while actor anchor stayed-1. This also changed initial visibility from2mto3m, so it is not a distance-only control challenge. No-noise ideal sample also fails registered hit censor; do not bypass coverage or secretly widen sensors.','next_task_design_unexecuted':'Separately preregister a distance course with comparable initial encounter/visibility and declared geometry; do not overwrite/retry original failed8m or call it passed.'}
(root/'INITIAL_VISIBILITY_DIAGNOSIS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert out['status']!='FAIL'
