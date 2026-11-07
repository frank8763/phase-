"""Persisted raw packet, braking and replanning chain; zero integrations."""
import argparse,os,json,gzip,hashlib
from pathlib import Path
from types import SimpleNamespace
import sys
sys.path.insert(1,str(Path(__file__).resolve().parents[2]/'experiments/v697_rpccr_dynamic_initialization'))
from ray_packet_contract import saved_rays_equal
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'runs/v771_audit_dependencies/site'))
from independent_domain import IndependentDomain
import risk_domain
risk_domain.RiskDomain=IndependentDomain
from motion_tracker import Tracker
from motion_evaluator import check_forecast
from union_belief import clearance as union_clearance
from exact_footprint import pose_values
p=argparse.ArgumentParser();p.add_argument('paired');p.add_argument('--preflight',action='store_true');p.add_argument('--output-dir',required=True);a=p.parse_args();root=Path(a.paired);cell=root/'geometry_memory'
output_dir=Path(a.output_dir).resolve();repo=Path(__file__).resolve().parents[2];assert output_dir.is_relative_to(repo/'runs'),'OUTPUT_MUST_BE_RUNS';output_dir.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
protocol=read(root/'STATIC_PROTOCOL.json');config=read(root/'DYNAMIC_PROTOCOL.json');initial=read(root/'INITIAL_UNSEEN.json')
def rays(packet):
 rows=[]
 for name,b,sigma in [('lidar',.06,.02),('depth',.09,.03)]:
  z=np.clip(np.asarray(packet[name],float),0,1)*packet[name+'_max_range'];R=packet[name+'_max_range'];angles=(np.arange(len(z))*2*np.pi/len(z)if name=='lidar'else np.linspace(-np.deg2rad(35),np.deg2rad(35),len(z)))+packet['yaw'];keep=(z>.05)&(z<R-b-1e-5)
  rows.extend([[*packet['xy'],np.cos(angle),np.sin(angle),v,b,sigma]for angle,v in zip(angles[keep],z[keep])])
 return np.asarray(rows).reshape(-1,7)
from unseen_prior import set_public_origin
set_public_origin(protocol['start_qpos'][:2])
_,s=Tracker().update_packet(initial['packet'],protocol['known_rectangles'],protocol['known_circles'])
checks={'initial_raw_sensor_filter_exact':saved_rays_equal(rays(initial['packet']),initial['packet']['rays']),'initial_prior_reconstructed':s==initial['causal_state'],'initial_unobserved_real_actor':initial['passed']and initial['checks']['genuinely_outside_initial_range'],'registered_geometry':config['new_course_id']=='V706_ORIGINAL_FIELD_RANGE_ENTRY' and config['initial_encounter_distance_m']>=3.6 and config['public_initial_origin_xy']==protocol['start_qpos'][:2] and len(protocol['known_rectangles'])==10 and len(protocol['known_circles'])==9}
cases={x['id']:x for x in read(Path(__file__).parent/'SCENE_CASES.json')};case=cases[config['case_id']];known=read(Path(__file__).parent/'KNOWN_FIELD.json')
checks.update(registered_original_known_field=protocol['known_rectangles']==known['known_rectangles'] and protocol['known_circles']==known['known_circles'],registered_public_start=np.array_equal(protocol['start_qpos'][:2],case['start_xy']),registered_public_goal=np.array_equal(np.asarray(protocol['goal_xy'],np.float32),np.asarray(case['goal_xy'],np.float32)))
details={}
if not a.preflight:
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
 states=lines(cell/'motion_estimate.jsonl');execution=lines(cell/'v648_execution.jsonl');ad=lines(cell/'model_admission.jsonl');tracker=Tracker();reconstructed=[];filter_errors=[];coverage=[]
 for packet in packets:
  rr=rays(packet);filter_errors.append(not saved_rays_equal(rr,packet['rays']));_,state=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);reconstructed.append({'step':packet['step'],**state});coverage.append(check_forecast(config,state)['passed'])
 if not (cell/'FIRST_DISCOVERY.json').exists():
  checks.update(all_raw_packets_reconstructed=not any(filter_errors),all_causal_states_reconstructed=states==reconstructed,all329_future_coverage=all(coverage),moving_before_discovery=False,new_causal_route_after_stop=False,actually_continued_after_replanning=False,strict_arrival=False)
  details={'functional_stop':'NO_ACTOR_DISCOVERY','complete_discovery_brake_unexecuted':True}
 else:
  detected=[s['step']for s in reconstructed if s['center']is not None];d=read(cell/'FIRST_DISCOVERY.json');done=read(cell/'DISCOVERY_BRAKE_COMPLETION.json');first=d['step'];previous=execution[first-1]
  with gzip.open(cell/'discovery_stop_certificate.json.gz','rt')as f:c=json.load(f)
  bounds=np.asarray(protocol['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  q=np.asarray(c['qpos']);v=np.asarray(c['qvel']);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));poses=np.c_[q[:,:2],yaw];minimum=float(np.min(np.minimum(pose_values(field,poses),union_clearance(field,poses,c['forecast_state']['outer_state_cells'],np.arange(1,329)*.01))))
  contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');ids=contract['ids'];limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate']);command=np.asarray(c['prefix_command']);expected=[]
  for tick in range(0,328,8):command=np.clip(np.clip(c['target'],limits[:,0],limits[:,1]),command-rate,command+rate);expected.extend([command.copy()for _ in range(8)])
  errors=[];brakes=[x for x in ad if x['status']=='DISCOVERY_BRAKE_CONTRACT']
  for row in brakes:
   i=row['contract_native_cursor'];e=execution[row['step']];errors.append(max(float(np.max(abs(np.asarray(e['qpos_full'])-q[i+7]))),float(np.max(abs(np.asarray(e['qvel_full'])-v[i+7]))),float(np.max(abs(np.asarray(e['ctrl'])[ids]-np.asarray(c['controls'])[i])))))
  post=[read(p)for p in sorted(cell.glob('planning_*.json'))if read(p)['step']>done['finished_step']];new_reference=bool(post and post[0]['path']is not None and not np.array_equal(np.asarray(post[0]['path']),np.asarray(d['old_path'])))
  route_clearance=None
  if new_reference:
   path=np.asarray(post[0]['path']);state=reconstructed[post[0]['step']];route_clearance=float(np.min(np.minimum(pose_values(field,path[:,:3]),union_clearance(field,path[:,:3],state['outer_state_cells'],np.zeros(len(path))))))
  prior_moving=[np.linalg.norm(np.asarray(e['qvel_full'])[:2])for e in execution[max(0,first-10):first]];result=read(cell/'result.json');continued=float(np.linalg.norm(np.asarray(execution[-1]['qpos_full'])[:2]-np.asarray(execution[done['finished_step']]['qpos_full'])[:2]))
  checks.update(all_raw_packets_reconstructed=not any(filter_errors),all_causal_states_reconstructed=states==reconstructed,all329_future_coverage=all(coverage),first_detection_from_actual_sensor=bool(detected and min(detected)==first and all(s['center']is None for s in reconstructed[:first])),moving_before_discovery=first>=10 and len(prior_moving)==10 and min(prior_moving)>=.10 and d['speed_before_m_s']>=.15 and d['forward_progress_before_m']>=.30,discovery_state_exact=max(np.max(abs(np.asarray(d['qpos'])-previous['qpos_full'])),np.max(abs(np.asarray(d['qvel'])-previous['qvel_full'])))<=1e-8,no_initial_stationary_observation=result['initial_observation_steps']==0,complete328_stop=len(q)==len(v)==len(c['controls'])==328 and len(brakes)==41 and done['finished_step']==first+40,stop_canonical_commands=np.max(abs(np.asarray(expected)-c['controls']))<=1e-12 and c['target'][:2]==c['prefix_command'][:2]and c['target'][2:]==[0.,0.],stop_geometry_recomputed=minimum>=.155 and abs(minimum-c['minimum_causal_predicted_clearance_m'])<=1e-8,stop_full_state_ctrl=max(errors,default=1.)<=1e-8,actual_deceleration=done['actual_terminal_speed_m_s']<=.025 and np.linalg.norm(v[-1,:2])<=.025 and done['actual_terminal_speed_m_s']<d['speed_before_m_s'],new_causal_route_after_stop=new_reference and route_clearance is not None and route_clearance>=.155-1e-8,actually_continued_after_replanning=continued>=1.,strict_arrival=result['strict_safe_arrival'])
  checks['actual_discovery_progress_from_public_origin']=abs(float(np.linalg.norm(np.asarray(d['qpos'])[:2]-np.asarray(protocol['start_qpos'])[:2]))-d['forward_progress_before_m'])<=1e-10
  details={'first_detection_step':first,'first_detection_sim_time_s':d['time'],'speed_before_discovery_m_s':d['speed_before_m_s'],'forward_progress_before_discovery_m':d['forward_progress_before_m'],'minimum_last10_speed_m_s':min(prior_moving),'terminal_stop_speed_m_s':done['actual_terminal_speed_m_s'],'stop_public_steps':len(brakes),'stop_minimum_causal_clearance_m':minimum,'maximum_stop_state_control_error':max(errors,default=None),'first_post_stop_replan_step':post[0]['step']if post else None,'new_reference_current_causal_clearance_m':route_clearance,'post_stop_actual_displacement_m':continued,'preserves_task_assumption':'startup3m exclusion is a declared prior, not inferred from nondetections'}
out={'status':'PASS'if all(checks.values())else'FAIL','checks':{k:bool(v)for k,v in checks.items()},'details':details,'verification_integrations':0,'gradient_updates':0,'scope':'finite range-entry moving discovery under registered startup clearing, not arbitrary occlusion/spawning'}
target=output_dir/('INITIAL_UNSEEN_AUDIT_V699.json' if a.preflight else 'DISCOVERY_CHAIN_AUDIT_V699.json')
with target.open('x') as stream:stream.write(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'checks':out['checks']},indent=2));assert out['status']=='PASS'
