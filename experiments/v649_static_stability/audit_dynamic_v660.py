"""Independent persisted-evidence checks; no controller/simulator import or steps."""
import gzip,hashlib,json,math,argparse
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s)for s in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--v661',action='store_true');args=parser.parse_args()
roots=[repo/'runs/v659_dynamic_scene_repair/dev31_95000011_instant/paired',
       repo/'runs/v660_dynamic_audit_recovery/dev31_95000011_predictive/paired']
repeat=repo/'runs/v660_dynamic_audit_recovery/dev31_95000011_predictive_repeat/paired'
if repeat.exists():roots.append(repeat)
window=repo/'runs/v660_dynamic_audit_recovery/development03'
if args.v661:
 roots.append(repo/'runs/v661_dynamic_corridor_consistency/dev32_95000011_predictive/paired')
 repeat=repo/'runs/v661_dynamic_corridor_consistency/dev32_95000011_predictive_repeat/paired'
 if repeat.exists():roots.append(repeat)
 window=repo/'runs/v661_dynamic_corridor_consistency/development04'
assert (window/'COMPLETION.json').exists(),'Do not finalize a live window'
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
original=read(repo/'runs/v658_dynamic_unknown/development01/WINDOW.json');final=read(window/'COMPLETION.json');w=read(window/'WINDOW.json')
checks={'all_record_checks':all(x['passed']for x in records),'original_deadline_unchanged':w['absolute_deadline_unix']==original['absolute_deadline_unix']==final['original_absolute_deadline_unix'],
        'completed_within_original_budget':w['started_unix']+final['elapsed_s']<=original['absolute_deadline_unix'],
        'baseline_supplemental_audit':read(window/'BASELINE_SUPPLEMENTAL_AUDIT.json')['passed'],
        'same_model_and_initial_pair':read(window/'PAIRING_AUDIT.json')['passed']}
output={'status':'EVIDENCE_AND_EXECUTED_NATIVE_CHECKS_PASS'if all(checks.values())else'FAIL','checks':checks,'branches':records,'navigation_tasks':1,'independent_confirmation_tasks':0,
        'repeat_present':repeat.exists(),'dynamic_stability_acceptance_passed':False,'verification_simulation_steps':0,
        'scope':'Finite one-scene development; reference is pose interpolation, safety is native sampled; no calibrated/continuous/real-time claim'}
out=window.parent/'INDEPENDENT_DYNAMIC_AUDIT.json';out.write_text(json.dumps(output,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(output,indent=2,default=lambda x:x.item()))
