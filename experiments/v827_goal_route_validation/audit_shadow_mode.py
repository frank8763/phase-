"""Audit shadow-only evaluation against the retained and actually executed contract."""
import argparse,gzip,json
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('pair');args=p.parse_args();pair=Path(args.pair);cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []
mode=read(pair/'ABLATION_PROTOCOL.json')['mode'];ad=lines(cell/'model_admission.jsonl');execution=lines(cell/'v648_execution.jsonl');compute=lines(cell/'return_compute.jsonl');shadow=lines(cell/'shadow_return_attempts.jsonl');hands=lines(cell/'handover_attempts.jsonl');actual={x['step']:x for x in ad}
checks={'registered_mode':mode in ('FULL','SHADOW_COMPLETE_TAIL'),'declared_safety':read(pair/'ABLATION_PROTOCOL.json')['same_safety_gates'] is True,'compute_counts_valid':all(x['mode']==mode and x['prediction_after']-x['prediction_before']==x['prediction_delta'] and x['prediction_delta']>=0 and x['real_state_unchanged'] is True and x['hidden_world_geometry_used'] is False for x in compute)}
details=[]
if mode=='FULL':
    checks.update(no_shadow_certificates=not shadow and not list(cell.glob('shadow_handover_certificates/*.gz')),
                  actual_returns_match_compute={x['step'] for x in compute if x['returned']}=={x['step'] for x in ad if x.get('certified_backup_handover')},
                  progress_gate=all(x['predicted_goal_progress_m']>=.02 for x in hands if x['status']=='CERTIFIED_RETURN'))
else:
    checks.update(no_actual_shadow_commit=not list(cell.glob('handover_certificates/*.gz')) and not any(x.get('certified_backup_handover') for x in ad) and not any(x['returned'] for x in compute),
                  feasible_shadow_records={x['step'] for x in shadow}=={x['step'] for x in compute if x['shadow_feasible']})
    old={}
    for file in cell.glob('recovery_contracts/*.gz'):
        with gzip.open(file,'rt') as stream:value=json.load(stream)
        old[value['created_step']]=value
    files=sorted(cell.glob('shadow_handover_certificates/*.gz'));checks['one_saved_certificate_per_shadow']=len(files)==len(shadow)
    for file in files:
        with gzip.open(file,'rt') as stream:c=json.load(stream)
        step=c['handover_step'];cursor=c['old_native_cursor'];contract=old[c['old_created_step']];previous=execution[step-1]
        q=contract['initial_qpos'] if cursor==0 else contract['qpos'][cursor-1];v=contract['initial_qvel'] if cursor==0 else contract['qvel'][cursor-1]
        error=max(float(np.max(abs(np.asarray(previous['qpos_full'])-c['real_entry_qpos']))),float(np.max(abs(np.asarray(previous['qvel_full'])-c['real_entry_qvel']))),float(np.max(abs(np.asarray(q)-c['real_entry_qpos']))),float(np.max(abs(np.asarray(v)-c['real_entry_qvel']))))
        local={'old_actual_state_exact':error<=1e-8,'old_time_exact':abs(c['real_entry_time']-contract['start_time']-cursor*.01)<=1e-8,'explicitly_not_executed':c['shadow_only'] is True and c['executed'] is False,'actual_still_old_contract':actual[step]['status']=='RETAINED_REVERSE_BRAKE_CONTRACT' and actual[step]['retained_from_step']==c['old_created_step'] and actual[step]['contract_native_cursor']==cursor,'goal_gate_and_causal':c['metadata']['predicted_goal_progress_m']>=.02 and c['hidden_world_geometry_used'] is False,'full_candidate_saved':len(c['qpos'])==len(c['qvel'])==len(c['controls'])==320 and len(c['prefix_poses'])==8,'candidate_gates':c['minimum_causal_predicted_clearance_m']>=.155 and c['minimum_predicted_self_domain_margin_m']>=.002 and c['terminal_speed_m_s']<=.025}
        details.append({'step':step,'file':file.name,'checks':local,'passed':all(local.values())})
    checks['all_shadow_entries_retain_actual_old_contract']=all(x['passed'] for x in details)
reentry_private={int(p.stem[4:]):read(p)['private_integrations']for p in(cell/'retained_reentry').glob('step????.json')}
checks['logged_count_matches_actual_admission']=all(x['step']in actual and actual[x['step']]['prediction_steps_total']==x['prediction_after']+reentry_private.get(x['step'],0)for x in compute)
out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'mode':mode,'return_calls':len(compute),'actual_certified_returns':sum(x.get('certified_backup_handover',False) for x in ad),'shadow_feasible_returns':len(shadow),'shadow_details':details,'new_integrations':0,'scope':'Shadow candidate is evaluated but never committed or counted as actual recovery.'}
(pair/'SHADOW_MODE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='shadow_details'}));assert out['status']=='PASS'
