"""Zero-integration final ledger, source/model and all-task consistency verification."""
from pathlib import Path
import json,hashlib
repo=Path(__file__).resolve().parents[2];src=repo/'experiments/v689_dynamic_route_commitment';root=repo/'runs/v689_dynamic_route_commitment';window=root/'curriculum01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ledger=read(root/'ROUND_WINDOW.json');assert ledger['round_closed'];results=read(window/'RESULTS.json');tasks=[]
for row in results:
 pair=repo/row['run'];checks={'recorded_result_matches':row['result']==(read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None)}
 if row['result']is None:
  partial=read(pair/'geometry_memory/interrupted.json');completion=read(pair/'completion.json');checks['original_zero_step_failure_retained']=completion['status']=='FAILED'and partial['public_steps']==partial['physics_steps']==0 and row['runner_exit']!=0
  checks['zero_step_failure_not_counted_arrival']=partial['strict_safe_arrival']is False
 if row['result']is not None:
  r=row['result'];replay=read(pair/'NATIVE_REPLAY_AUDIT.json');audit=read(pair/'INDEPENDENT_CANONICAL_AUDIT.json');proposal=read(pair/'PROJECTION_LEARNING_AUDIT.json');route=read(pair/'ROUTE_COMMITMENT_AUDIT.json');tail=read(pair/'SAVED_TAIL_GEOMETRY_AUDIT.json')
  checks.update(full_physical_audit=audit['status']=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS',causal_projection_and_learning=proposal['status']=='PASS',route_triggers=route['status']=='PASS',full_tail_geometry=tail['status']=='ALL_SAVED_TAIL_GEOMETRY_DIRECTION_SCHEDULE_PASS',full_replay=replay['replay_integration_steps']==r['physics_steps']and max(replay[k]for k in ['maximum_full_public_qpos_error','maximum_full_public_qvel_error','maximum_public_mocap_error'])<=1e-8,unchanged_sources=all(sha(src/n)==v for n,v in read(window/'SOURCE_FREEZE.json').items()),unchanged_documents=all(sha(src/n)==v for n,v in read(window/'DOCUMENT_FREEZE.json').items()),raw_snapshot_sources=read(pair.parent/'source_snapshot/SHA256.json')==read(window/'SOURCE_FREEZE.json'))
 if 'repeat'in row['name']:
  checks['exact_repeat_pass']=read(pair/'EXACT_REPEAT_AUDIT.json')['passed']
 tasks.append({'name':row['name'],'checks':checks,'passed':all(checks.values())})
six=[x for x in results if x['distance_m']==6]
expected_six=bool(len(six)==3 and all(x.get('evidence_audits_pass')and x['result']['strict_safe_arrival']for x in six)and read(repo/six[-1]['run']/'EXACT_REPEAT_AUDIT.json')['passed'])
trained=list(root.glob('training_*/TRAINING.json'));updates=sum(read(p)['gradient_updates']for p in trained)
checks={'source_and_result_audits':all(x['passed']for x in tasks),'attempt_cap':ledger['navigation_attempts']<=6,'registered_update_cap':updates==ledger['supervised_gradient_updates']<=512,'six_meter_gate_matches_actual':expected_six==ledger['six_meter_gate_passed'],'eight_meter_requires_actual_six_gate':not ledger['eight_meter_started']or expected_six,'original_seven_thousand_two_hundred_deadline':abs(ledger['absolute_deadline_unix']-ledger['started_unix']-7200)<1e-6,'actual_elapsed_within_deadline':ledger['elapsed_s']<=7200,'old_six_meter_checkpoint_unchanged':sha(repo/'runs/v688_dynamic_distance_curriculum/training_6m/proposer.json')=='c77b5f833fe77d3cadbab9fb41835426a058249728eee94a0cf8e92aa88796c0','sac_updates_zero':ledger['sac_gradient_updates']==0}
out={'status':'ALL_FINAL_ACCOUNT_CHECKS_PASS'if all(checks.values())else'FAIL','checks':checks,'tasks':tasks,'verification_integrations':0,'verification_gradient_updates':0,'scope':'finite two-phase development gate and repeats, not original-field or statistical dynamic acceptance'}
(root/'FINAL_ACCOUNT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'checks':checks,'tasks':len(tasks)},indent=2));assert out['status']!='FAIL'
