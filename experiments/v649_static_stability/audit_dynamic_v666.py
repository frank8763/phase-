"""Independent persisted-evidence checks; no controller/simulator import or steps."""
import gzip,hashlib,json,math,argparse
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s)for s in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
window=repo/'runs/v666_dynamic_dense_navigation/development01'
assert (window/'COMPLETION.json').exists(),'Do not audit unfinished candidate'
outcomes=read(window/'RESULTS.json',) if (window/'RESULTS.json').exists() else []
roots=[window.parent/x['name']/'paired'for x in outcomes]
records=[]
for root in roots:
 cell=root/'geometry_memory'
 if not (cell/'result.json').exists() or not (root/'NATIVE_REPLAY_AUDIT.json').exists():
  records.append({'run':str(root.relative_to(repo)),'passed':False,'outcome':'INTERRUPTED_OR_NATIVE_REPLAY_MISSING','interrupted':read(cell/'interrupted.json')if(cell/'interrupted.json').exists()else None,'scope':'no completed full physical audit claimed'});continue
 r=read(cell/'result.json');model=read(root/'STATIC_PROTOCOL.json');motion=read(root/'DYNAMIC_PROTOCOL.json')
 replay=read(root/'NATIVE_REPLAY_AUDIT.json');execution=lines(cell/'v648_execution.jsonl');admissions=lines(cell/'model_admission.jsonl')
 with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:native=[json.loads(s)for s in f]
 c=motion;xy=np.asarray([s['actor_xy']for s in native]);t=np.asarray([s['time']for s in native]);a=np.asarray(c['anchor_xy']);axis=np.asarray(c['axis_xy'])
 expected=a+np.sin(t*c['omega_rad_s']+c['phase_rad'])[:,None]*c['amplitude_m']*axis
 displacement=np.linalg.norm(np.diff(xy,axis=0),axis=1)
 h=hashlib.sha256();contact_count=0;unknown_count=0;obstacle_count=0
 with gzip.open(cell/'contacts.jsonl.gz','rb')as f:
  for b in f:
   h.update(b);row=json.loads(b);kind=row['contact_type'];contact_count+=1
   unknown_count+=kind=='unknown_contact';obstacle_count+=kind in ['robot_obstacle_contact','robot_obstacle_penetration']
 source=read(root.parent/'source_snapshot/SHA256.json')
 source_match=all(sha(root.parent/'source_snapshot'/name)==digest for name,digest in source.items())
 certificate=c['swept_envelope_reference']
 checks={'all_public_and_native_records':len(execution)==r['public_steps']==len(admissions)and len(native)==r['physics_steps']==8*len(execution),
         'source_snapshot':source_match,'saved_model':sha(root/'scene_model.mjb')==model['full_model_sha256']==replay['scene_model_sha256'],
         'causal_admission':all(s['hidden_world_geometry_used']is False and s['dynamic_time_gate']is True for s in admissions),
         'actor_motion_formula':float(np.max(abs(expected-xy)))<=1e-12,
         'actor_mocap_at_all_native_ticks':all(np.max(abs(np.asarray(s['mocap_pos'])[c['mocap_id'],:2]-s['actor_xy']))<=1e-12 for s in native),
         'native_time_steps':np.max(abs(np.diff(t)-.01))<=1e-10,
         'motion_bounds':np.max(np.linalg.norm(xy-a,axis=1))<=.25+1e-10 and np.max(displacement)<=.08*.01+1e-10,
         'smaller_actor':c['radius_m']==.10,'not_at_junction':c['protected_junction_clearance_of_sweep_m']>=.05,
         'swept_known_geometry_clearance':c['known_obstacle_clearance_of_swept_envelope_m']>=.55,
         'full_sweep_bypass':certificate['eligible']and certificate['continuous_polygonal_pose_clearance_lower_bound_m']>=.15 and certificate['search']['minimum_clearance_m']>=.155,
         'online_native_clearance':min(s['actual_clearance_m']for s in native)>=.15 and abs(min(s['actual_clearance_m']for s in native)-r['minimum_dynamic_native_clearance_m'])<=1e-12,
         'full_replay':replay['status']=='MATCHED_RECORDED_PUBLIC_STATES'and replay['replay_integration_steps']==len(native)and max(replay['maximum_full_public_qpos_error'],replay['maximum_full_public_qvel_error'],replay['maximum_public_mocap_error'])<=1e-8,
         'replay_safety':replay['minimum_reconstructed_native_actual_axis_AABB_clearance_m']>=.15 and replay['reconstructed_native_states_below_015']==0 and replay['minimum_reconstructed_self_domain_margin_m']>=0,
         'zero_contact':obstacle_count==unknown_count==replay['replay_obstacle_contact_records']==replay['replay_unknown_contact_records']==0,
         'raw_contact_digest':h.hexdigest()==r['contacts']['contact_log_content_sha256']and contact_count==r['contacts']['all_contact_records'],
         'self_coverage':r['self_geometry_checked_native_ticks']==len(native)and r['minimum_actual_self_domain_margin_m']>=0,
         'native_root_only':r['root_mutations_outside_mjstep']==0,
         'strict_outcome_consistent':r['strict_safe_arrival']==bool(r['outcome']=='GOAL'and r['goal_distance_m']<=.45 and obstacle_count==unknown_count==0)}
 records.append({'run':str(root.relative_to(repo)),'passed':all(checks.values()),'checks':checks,'outcome':r['outcome'],'strict_arrival':r['strict_safe_arrival'],
     'public_steps':len(execution),'native_steps':len(native),'minimum_native_clearance_m':min(s['actual_clearance_m']for s in native),
     'actor_displacement_span_m':float(np.linalg.norm(xy.max(axis=0)-xy.min(axis=0))),
     'actor_max_native_displacement_m':float(np.max(displacement)),'raw_contact_records':contact_count})
origin=read(repo/'runs/v666_dynamic_dense_navigation/ROUND_WINDOW.json');final=read(window/'COMPLETION.json');w=read(window/'WINDOW.json')
coverage=[]
for root in roots:
 rows=lines(root/'geometry_memory/motion_estimate.jsonl');c=read(root/'DYNAMIC_PROTOCOL.json');saved=lines(root/'geometry_memory/forecast_coverage.jsonl')
 worst=-float('inf'); velocity_excess=-float('inf')
 for r in rows:
  times=np.linspace(0,2.4,121);lo=np.asarray(r['position_lower']);hi=np.asarray(r['position_upper']);vl=np.asarray(r['velocity_lower']);vu=np.asarray(r['velocity_upper']);tt=times[:,None]
  low=np.maximum(lo+tt*vl-.02*tt**2,lo-.12*tt);high=np.minimum(hi+tt*vu+.02*tt**2,hi+.12*tt)
  truth=np.asarray(c['anchor_xy'])+np.sin((r['time']+times)*c['omega_rad_s'])[:,None]*c['amplitude_m']*np.asarray(c['axis_xy'])
  v=np.cos(r['time']*c['omega_rad_s'])*c['maximum_speed_m_s']*np.asarray(c['axis_xy'])
  worst=max(worst,float(np.maximum(low-truth,truth-high).max()))
  velocity_excess=max(velocity_excess,float(np.maximum(vl-v,v-vu).max()))
 coverage.append({'run':str(root.relative_to(repo)),'frames':len(rows),'forecast_times_per_frame':121,'maximum_center_box_excess_m':worst,'maximum_velocity_box_excess_m_s':velocity_excess,'saved_rows_pass':len(saved)==len(rows) and all(x['passed']for x in saved),'passed':worst<=1e-7 and velocity_excess<=1e-7 and len(saved)==len(rows) and all(x['passed']for x in saved)})
source=read(window/'SOURCE_FREEZE.json');documents=read(window/'DOCUMENT_FREEZE.json');src=repo/'experiments/v666_dynamic_dense_navigation'
pose_errors=[]
for root in roots:
 trace=read(root/'geometry_memory/trace.json');admissions=lines(root/'geometry_memory/model_admission.jsonl')
 error=np.asarray([np.asarray(r['pose'])-a['predicted_next_pose']for r,a in zip(trace,admissions)]);error[:,2]=(error[:,2]+np.pi)%(2*np.pi)-np.pi
 pose_errors.append({'run':str(root.relative_to(repo)),'maximum_first_public_xy_yaw_error':np.max(abs(error),axis=0).tolist(),'public_steps':len(trace)})
old=repo/'runs/v664_dynamic_causal_proposals/dev34_95000011_proposal/paired'
checks={'all_native_records':bool(records)and all(r['passed']for r in records),'finite_prediction_coverage':bool(coverage)and all(r['passed']for r in coverage),
 'frozen_source_protocol':all(sha(src/n)==h for n,h in {**source,**documents}.items()),
 'deadline_unchanged':w['absolute_deadline_unix']==origin['absolute_deadline_unix']==final['absolute_deadline_unix'],
 'within_deadline':w['started_unix']+final['elapsed_s']<=origin['absolute_deadline_unix'],
 'within_registered_attempt_caps':origin['development_candidates']<=3 and origin['navigation_attempts']<=6 and origin['preflight_attempts']<=2,
 'old_task_model_initial_unchanged':all(read(r/'STATIC_PROTOCOL.json')['full_model_sha256']==read(old/'STATIC_PROTOCOL.json')['full_model_sha256'] and read(r/'geometry_memory/result.json')['normalized_initial_state_hash']==read(old/'geometry_memory/result.json')['normalized_initial_state_hash']for r in roots if read(r/'geometry_memory/result.json')['seed']==95000011),
 'first_public_predicted_pose_matches':all(max(r['maximum_first_public_xy_yaw_error'])<=1e-8 for r in pose_errors),
 'all_registered_repeats_match':all(read(r/'EXACT_REPEAT_AUDIT.json')['matched']for r in roots if 'repeat'in str(r))}
output={'status':'EVIDENCE_AND_EXECUTED_NATIVE_CHECKS_PASS'if all(checks.values())else'FAIL','checks':checks,'branches':records,'coverage':coverage,'prediction_first_public_pose_checks':pose_errors,
 'distinct_development_tasks':len(set(read(r/'geometry_memory/result.json')['seed']for r in roots)),'navigation_branches_including_repeats':len(roots),'independent_confirmation_tasks':0,'strict_arrivals_including_repeats':sum(r['strict_arrival']for r in records),'verification_simulation_steps':0,'dynamic_stability_acceptance_passed':False,'scope':'finite development, no population, continuous-time or real-time guarantee'}
out=window.parent/'INDEPENDENT_DYNAMIC_AUDIT.json';out.write_text(json.dumps(output,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(output,indent=2,default=lambda x:x.item()))
