"""Persisted sensor/state reconstruction and an analytical certificate bound."""
import gzip,hashlib,json,math,os,sys,time
from pathlib import Path
import numpy as np
REPO=Path(__file__).resolve().parents[2];SOURCE=REPO/'experiments/v712_joint_field_continuation'
sys.path.insert(0,str(SOURCE));os.environ['PHASE_REPO']=str(REPO)
from motion_tracker import Tracker
from unseen_prior import set_public_origin
from motion_evaluator import check_forecast
from future_guide import route_world
from ray_packet_contract import saved_rays_equal
root=REPO/'runs/v713_unseen_frontier_diagnosis';root.mkdir(exist_ok=False)
pair=REPO/'runs/v712_joint_field_continuation/main01/paired';cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
states=lines(cell/'motion_estimate.jsonl');execution=lines(cell/'v648_execution.jsonl');admissions=lines(cell/'model_admission.jsonl');decisions=lines(cell/'control_decisions.jsonl')
protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');result=read(cell/'result.json')
set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();reconstructed=[];raw_matches=[];coverage=[];actual_actor_ranges=[]
for packet in packets:
 rr=[]
 for tag,b,sigma in [('lidar',.06,.02),('depth',.09,.03)]:
  values=np.clip(np.asarray(packet[tag],float),0,1)*packet[tag+'_max_range'];R=packet[tag+'_max_range'];angles=(np.arange(len(values))*2*np.pi/len(values) if tag=='lidar'else np.linspace(-np.deg2rad(35),np.deg2rad(35),len(values)))+packet['yaw'];keep=(values>.05)&(values<R-b-1e-5)
  rr.extend([[*packet['xy'],np.cos(angle),np.sin(angle),v,b,sigma]for angle,v in zip(angles[keep],values[keep])])
 rr=np.asarray(rr).reshape(-1,7);raw_matches.append(saved_rays_equal(rr,packet['rays']));_,state=tracker.update_rays(rr,protocol['known_rectangles'],protocol['known_circles'],packet['time']);reconstructed.append({'step':packet['step'],**state});coverage.append(check_forecast(config,state)['passed'])
 actor=np.array(config['anchor_xy'])+np.array(config['axis_xy'])*config['amplitude_m']*math.sin(config['omega_rad_s']*packet['time']+config['phase_rad'])
 actual_actor_ranges.append(float(np.linalg.norm(actor-packet['xy']))-config['radius_m'])
state_by_step={s['step']:s for s in reconstructed};plan_matches=[]
for p in sorted(cell.glob('planning_*.json')):
 x=read(p);w,metadata=route_world(x['causal_input'],state_by_step[x['step']]);plan_matches.append(dict(step=x['step'],same_world=w==x['causal_route_input'],same_metadata=metadata==x['route_projection_metadata'],status=x['stats']['status']))
bounds=np.array(protocol['footprint_bounds']);half=(bounds[2:]-bounds[:2])/2;rho=float(np.linalg.norm(half));speed=states[0]['radial_speed_bound_m_s'];H=3.28;floor=.155;radius=.10
critical=(3.-rho-radius-floor)/speed-H;last_time=states[-1]['time'];best_terminal_bound=max(0.,3.-speed*(last_time+H))-rho-radius
last_nominal=[x for x in decisions if x['stage']=='NOMINAL'][-1]
reasons={}
for x in last_nominal['candidates']:
 key=str(x.get('reason'));reasons[key]=reasons.get(key,0)+1
out=dict(status='SAVED_UNSEEN_FRONTIER_DIAGNOSIS_COMPLETE',checks=dict(raw_rays_exact=all(raw_matches),all_causal_states_exact=states==reconstructed,all329_finite_forecasts_cover=all(coverage),all_saved_plan_metadata_exact=all(x['same_world']and x['same_metadata']for x in plan_matches),all_states_unseen=all(s['information_mode']=='UNSEEN_PRIOR'and s['center']is None for s in states),original_nonarrival=result['strict_safe_arrival']is False),
  packets=len(packets),states=len(states),all_states_no_actor_detection=all(s['center']is None for s in states),minimum_actual_actor_surface_range_m=min(actual_actor_ranges),maximum_displacement_from_start_m=float(np.max(np.linalg.norm(np.asarray([e['qpos_full'][:2]for e in execution])-protocol['start_qpos'][:2],axis=1))),
  planning_records=plan_matches,tracked_projection_records=0,original_projection_audit_not_rewritten=True,
  terminal_certificate_bound=dict(initial_exclusion_radius_m=3.,footprint_half_diagonal_m=rho,actor_radius_m=radius,public_radial_speed_bound_m_s=speed,new_contract_horizon_s=H,required_clearance_m=floor,critical_current_time_s=critical,actual_last_decision_time_s=last_time,maximum_possible_new_contract_terminal_clearance_m=best_terminal_bound,
   formula='max(0, 3-v*(t+3.28)) - rho - 0.10; every rectangle pose has a corner at least rho from the fixed public origin.',scope='Necessary upper bound under the saved shrinking disk, independent of steering or search. Does not prove actual scene impossibility.'),
  last_nominal_step=last_nominal['step'],last_nominal_summary=last_nominal['summary'],last_nominal_candidate_reasons=reasons,
  navigation_native_steps=result['physics_steps'],replay_native_steps=read(pair/'NATIVE_REPLAY_AUDIT.json')['replay_integration_steps'],private_integrations=result['prediction_steps'],new_initializations=0,new_integrations=0,training_updates=0,
  next_unimplemented_research='Causal renewal of certified observed-free space before first actor detection, respecting clipped noise, dropout, occlusion, finite rays and motion bounds; no truth/recentering shortcut. Then separate frozen candidate validation and prospective acceptance.')
(root/'DIAGNOSIS.json').write_text(json.dumps(out,indent=2)+'\n')
assert all(out['checks'].values())
for filename,target_literal in [('audit_all_tail_geometry.py',"(root/'SAVED_TAIL_GEOMETRY_AUDIT.json')"),('audit_shadow_mode.py',"(pair/'SHADOW_MODE_AUDIT.json')")]:
 source=(SOURCE/filename).read_text();target='SAVED_TAIL_GEOMETRY_AUDIT.json'if filename.startswith('audit_all')else'SHADOW_MODE_AUDIT.json'
 assert source.count(target_literal)==1
 redirected=source.replace(target_literal,repr(str(root/target)) if False else "Path("+repr(str(root/target))+")")
 record=dict(original_source=str((SOURCE/filename).relative_to(REPO)),original_sha256=hashlib.sha256(source.encode()).hexdigest(),redirected_source_sha256=hashlib.sha256(redirected.encode()).hexdigest(),only_change='One persisted output path; original evidence not modified.',integrations=0)
 (root/(filename+'.OUTPUT_REDIRECT.json')).write_text(json.dumps(record,indent=2)+'\n')
 sys.argv=[str(SOURCE/filename),str(pair)]
 exec(compile(redirected,str(SOURCE/filename),'exec'),{'__name__':'__main__','__file__':str(SOURCE/filename)})
print(json.dumps({k:out[k]for k in ['status','checks','minimum_actual_actor_surface_range_m','maximum_displacement_from_start_m','terminal_certificate_bound','last_nominal_candidate_reasons']}))
