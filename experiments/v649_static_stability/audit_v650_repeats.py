"""Offline compare V650 repetitions with the preserved V649 full-state traces."""
import gzip,json
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v650_static_acceptance';baseline=repo/'evidence/static_stability_20261031/selected'
rows=[]
for seed,scene,original in [(91000002,'single_event','dev27b_seed91000002_single_event'),(92000003,'single_event','dev27_seed92000003_single_event'),(92000005,'legacy_two','dev27b_seed92000005_legacy_two')]:
    name=f'repeat_{seed}_{scene}';pair=root/name/'paired';branch=pair/'geometry_memory';base=baseline/original/'geometry_memory'
    if not (branch/'result.json').exists():rows.append({'name':name,'passed':False,'status':'NOT_COMPLETED'});continue
    def archived(p):return json.loads(gzip.decompress(p.read_bytes()))
    r=json.loads((branch/'result.json').read_text());old=archived(base/'result.json.gz');trace=json.loads((branch/'trace.json').read_text());prior=archived(base/'trace.json.gz')
    execution=[json.loads(x)for x in(branch/'v648_execution.jsonl').read_text().splitlines()];old_execution=[json.loads(x)for x in gzip.decompress((base/'v648_execution.jsonl.gz').read_bytes()).decode().splitlines()]
    errors={}
    for key in ['qpos_full','qvel_full','ctrl']:
        errors[key]=float(np.max(abs(np.array([x[key]for x in execution])-np.array([x[key]for x in old_execution]))))if len(execution)==len(old_execution)else None
    state_same=r['normalized_initial_state_hash']==old['normalized_initial_state_hash'];contact_same=r['contacts']['contact_log_content_sha256']==old['contacts']['contact_log_content_sha256'];outcome_same=r['outcome']==old['outcome']and r['strict_safe_arrival']==old['strict_safe_arrival']
    passed=state_same and contact_same and outcome_same and all(x is not None and x<=1e-8 for x in errors.values())
    rows.append({'name':name,'baseline':original,'passed':passed,'normalized_initial_state_same':state_same,'contact_content_same':contact_same,'outcome_same':outcome_same,'maximum_recorded_state_error':errors,'public_steps':r['public_steps']})
result={'three_scene_repeat_gate_met':len(rows)==3 and all(x['passed']for x in rows),'rows':rows,'independent_new_trial_count':0,'simulation_steps':0};(root/'REPEAT_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
