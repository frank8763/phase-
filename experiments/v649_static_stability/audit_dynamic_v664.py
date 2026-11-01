"""Independent persisted-evidence checks; no controller/simulator import or steps."""
import gzip,hashlib,json,math,argparse
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s)for s in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
roots=[repo/'runs/v664_dynamic_causal_proposals'/name/'paired' for name in ['dev34_95000011_proposal','dev34_95000011_proposal_repeat'] if (repo/'runs/v664_dynamic_causal_proposals'/name/'paired').exists()]
window=repo/'runs/v664_dynamic_causal_proposals/development01'
assert (window/'COMPLETION.json').exists()
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
origin=read(repo/'runs/v662_dynamic_sensor_diagnosis/diagnosis01/WINDOW.json');final=read(window/'COMPLETION.json');w=read(window/'WINDOW.json')
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
source=read(window/'SOURCE_FREEZE.json');documents=read(window/'DOCUMENT_FREEZE.json');src=repo/'experiments/v664_dynamic_causal_proposals'
checks={'all_native_records':all(r['passed']for r in records),'prediction_coverage_finite_grid':all(r['passed']for r in coverage),
 'frozen_source_and_protocol':all(sha(src/n)==h for n,h in {**source,**documents}.items()),
 'same_model':len({read(r/'STATIC_PROTOCOL.json')['full_model_sha256']for r in roots})==1,
 'same_normalized_initial_state':len({read(r/'geometry_memory/result.json')['normalized_initial_state_hash']for r in roots})==1,
 'original_deadline_unchanged':w['absolute_deadline_unix']==origin['absolute_deadline_unix']==final['absolute_deadline_unix'],
 'completed_within_original_deadline':w['started_unix']+final['elapsed_s']<=origin['absolute_deadline_unix'],
 'v662_diagnosis_pass':read(repo/'runs/v662_dynamic_sensor_diagnosis/diagnosis01/DIAGNOSTIC_AUDIT.json')['passed'],
 'same_v663_model_and_initial':all(read(r/'STATIC_PROTOCOL.json')['full_model_sha256']==read(repo/'runs/v663_dynamic_interval_tracking/dev33_95000011_observe0/paired/STATIC_PROTOCOL.json')['full_model_sha256'] and read(r/'geometry_memory/result.json')['normalized_initial_state_hash']==read(repo/'runs/v663_dynamic_interval_tracking/dev33_95000011_observe0/paired/geometry_memory/result.json')['normalized_initial_state_hash']for r in roots),
 'repeat_if_executed':len(roots)<2 or read(roots[1]/'EXACT_REPEAT_AUDIT.json')['matched']}
output={'status':'EVIDENCE_AND_EXECUTED_NATIVE_CHECKS_PASS'if all(checks.values())else'FAIL','checks':checks,'branches':records,'coverage':coverage,'distinct_development_tasks':1,'new_navigation_branches':min(1,len(roots)),'independent_confirmation_tasks':0,'strict_arrivals':sum(r['strict_arrival']for r in records),'conditional_repeat_attempted':len(roots)>1,'verification_simulation_steps':0,'dynamic_stability_acceptance_passed':False,'scope':'finite one-scene causal-proposal development and success-dependent repeat; non-arrivals preserved; sampled future coverage is not a calibrated probability or continuous-time proof'}
out=window.parent/'INDEPENDENT_DYNAMIC_AUDIT.json';out.write_text(json.dumps(output,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(output,indent=2,default=lambda x:x.item()))
