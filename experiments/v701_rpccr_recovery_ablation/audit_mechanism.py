"""Offline audit that a complete-tail ablation never weakens a safety contract."""
import argparse,json
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('pair');args=parser.parse_args()
pair=Path(args.pair);cell=pair/'geometry_memory';read=lambda p:json.loads(p.read_text())
lines=lambda p:[json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
mode=read(pair/'ABLATION_PROTOCOL.json')['mode'];ad=lines(cell/'model_admission.jsonl')
suppressed=lines(cell/'ablation_suppressed_returns.jsonl');handovers=lines(cell/'handover_attempts.jsonl')
executed={x['step']:x for x in ad}
checks={'registered_mode':mode in ('FULL','COMPLETE_TAIL'),'declared_unchanged_safety':read(pair/'ABLATION_PROTOCOL.json')['same_safety_gates'] is True}
if mode=='COMPLETE_TAIL':
    checks.update(no_early_handover=not any(x.get('certified_backup_handover') for x in ad) and not list(cell.glob('handover_certificates/*.json.gz')) and not handovers,
                  suppressed_calls_contract_exact=bool(suppressed) and all(x['status']=='COMPLETE_EXISTING_TAIL_NO_EARLY_RETURN' and x['cache_modified'] is False and max(x['old_qpos_error'],x['old_qvel_error'])<=1e-8 and x['hidden_world_geometry_used'] is False for x in suppressed),
                  suppressed_actions_execute_existing_tail=all(x['step'] in executed and executed[x['step']]['status']=='RETAINED_REVERSE_BRAKE_CONTRACT' and executed[x['step']]['retained_from_step']==x['old_created_step'] and executed[x['step']]['contract_native_cursor']==x['old_native_cursor'] for x in suppressed),
                  completes_at_least_one_original_tail=any(x['status']=='RETAINED_REVERSE_BRAKE_CONTRACT' and x.get('finite_contract_complete_after_public') for x in ad))
else:
    checks.update(no_suppression=not suppressed,certified_return_actually_used=any(x.get('certified_backup_handover') for x in ad),handover_goal_progress_gate=all(x['predicted_goal_progress_m']>=.02 for x in handovers if x['status']=='CERTIFIED_RETURN'))
out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'mode':mode,'suppressed_attempts':len(suppressed),'certified_returns':sum(x['status']=='CERTIFIED_RETURN' for x in handovers),'new_integrations':0}
(pair/'MECHANISM_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['status']=='PASS'
