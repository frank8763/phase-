"""Independent accounting and raw contact hashes for interrupted V670 prefix."""
from pathlib import Path
import json,gzip,hashlib
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v670_dynamic_empty_samples';pair=root/'dev38_95000011_empty/paired';cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text())
r=read(cell/'interrupted.json');replay=read(pair/'PARTIAL_NATIVE_REPLAY_AUDIT.json');full=read(root/'INDEPENDENT_DYNAMIC_AUDIT.json');window=root/'development01';ledger=read(root/'ROUND_WINDOW.json')
rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];trace=read(cell/'trace.json');admissions=[json.loads(s)for s in(cell/'model_admission.jsonl').read_text().splitlines()]
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:native=[json.loads(s)for s in f]
h=hashlib.sha256();counts={};total=0
with gzip.open(cell/'contacts.jsonl.gz','rb')as f:
 for b in f:h.update(b);k=json.loads(b)['contact_type'];counts[k]=counts.get(k,0)+1;total+=1
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=read(window/'SOURCE_FREEZE.json');docs=read(window/'DOCUMENT_FREEZE.json');src=repo/'experiments/v670_dynamic_empty_samples'
old=repo/'runs/v669_dynamic_reserved_recovery/dev37_95000011_reserve/paired'
checks={'original_non_success_preserved':r['strict_safe_arrival']is False and not(cell/'result.json').exists()and read(pair/'completion.json')['status']=='FAILED',
'counts_complete_for_executed_prefix':len(rows)==len(trace)==len(admissions)==r['public_steps']==843 and len(native)==r['physics_steps']==replay['replay_integration_steps']==6744,
'zero_obstacle_unknown_records':sum(counts.get(k,0)for k in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact'])==0 and r['contacts']['robot_obstacle_contact_records']==r['contacts']['robot_obstacle_penetration_records']==r['contacts']['unknown_contact_records']==0,
'raw_contact_count_and_digest':total==r['contacts']['all_contact_records']and h.hexdigest()==r['contacts']['contact_log_content_sha256'],
'full_public_state_replay':replay['status']=='MATCHED_RECORDED_PUBLIC_STATES'and max(replay['maximum_full_public_qpos_error'],replay['maximum_full_public_qvel_error'],replay['maximum_public_mocap_error'])<=1e-8,
'native_clearance_and_self_domain':min(s['actual_clearance_m']for s in native)>=.15 and abs(min(s['actual_clearance_m']for s in native)-replay['minimum_reconstructed_native_actual_axis_AABB_clearance_m'])<=1e-12 and replay['minimum_reconstructed_self_domain_margin_m']>=0,
'saved_model_and_initial_state':sha(pair/'scene_model.mjb')==replay['scene_model_sha256']==read(old/'STATIC_PROTOCOL.json')['full_model_sha256']and read(cell/'state_hash_normalization.json')['normalized_hash']==read(old/'geometry_memory/result.json')['normalized_initial_state_hash'],
'frozen_source_and_protocol':all(sha(src/name)==h for name,h in {**source,**docs}.items()),
'finite_forecast_and_first_state':full['checks']['finite_prediction_coverage']and full['checks']['first_public_predicted_pose_matches']and full['checks']['retained_recovery_certificates'],
'reconstructed_causal_estimates':read(root/'ACTUAL_PACKET_ESTIMATOR_ABLATION.json')['maximum_reconstructed_online_state_error']<=1e-10,
'one_navigation_no_repeat':ledger['navigation_attempts']==1 and ledger['round_closed']and not ledger['completion']['conditional_repeat_attempted'],
'original_900s_stop':read(pair/'completion.json')['error']['message']=='STATIC_PILOT_900S_HARD_BUDGET'and read(pair/'completion.json')['elapsed_s']<=901,
'no_nav_deadline_extension':read(window/'COMPLETION.json')['absolute_deadline_unix']==ledger['absolute_deadline_unix']}
result={'status':'INTERRUPTED_EXECUTED_PREFIX_EVIDENCE_PASS'if all(checks.values())else'FAIL','checks':checks,'public_steps':len(rows),'native_steps':len(native),'native_control_replay_steps':replay['replay_integration_steps'],'maximum_public_qpos_qvel_error':max(replay['maximum_full_public_qpos_error'],replay['maximum_full_public_qvel_error']),'minimum_actual_native_clearance_m':min(s['actual_clearance_m']for s in native),'raw_contact_records':total,'contact_type_counts':counts,'strict_arrivals':0,'navigation_attempts':1,'independent_confirmation_tasks':0,'dynamic_stability_acceptance_passed':False,'verification_integrations':0,'scope':'all recorded executed prefix verified, original interrupted navigation remains non-success; full acceptance audit remains FAIL'}
(root/'INTERRUPTED_PREFIX_EVIDENCE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert all(checks.values())
