"""Freeze both already-prepared stages before any new model initialization."""
import ast
import json
from pathlib import Path
from evidence_rules import dump, read, sha

repo = Path(__file__).resolve().parents[2]
common = Path(__file__).parent
root = repo/'runs/dynamic_acceptance_20261105'
assert read(root/'ZERO_MODEL_QUALIFICATION.json')['passed']
assert not (root/'ROUND_WINDOW.json').exists()
auth = read(repo/'RPCCR_DYNAMIC_ACCEPTANCE_AUTHORIZATION_20261105.json')
old = repo/'experiments/v820_tracked_norm_global'
baseline = read(old/'CANDIDATE_FREEZE.json')
assert all(sha(repo/n)==h for n,h in baseline['files'].items())
files = dict(baseline['files'])
frozen_inputs = [repo/'RPCCR_DYNAMIC_ACCEPTANCE_AUTHORIZATION_20261105.json',
    repo/'docs/RPCCR_DYNAMIC_ACCEPTANCE_20261105_PLAN.md',
    root/'POOL_UNUSED_BEFORE_PREPARATION.json',root/'ALGORITHM_IDENTITY.json',
    root/'LOCKED_NEW_CONFIRMATION_TASKS.json',root/'ZERO_MODEL_QUALIFICATION.json',
    repo/'runs/v820_tracked_norm_global/FINALIZED.json',repo/'runs/v820_tracked_norm_global/FINAL_INDEPENDENT_AUDIT.json',
    repo/'runs/v820_tracked_norm_global/repeat_slot01/paired/EXACT_REPEAT_AUDIT.json',
    repo/'experiments/global_day_20261104_analysis/transport_archive.py']
for p in [*common.glob('*.py'),*frozen_inputs]: files[str(p.relative_to(repo))]=sha(p)
for namespace in ['v821_norm_route_development','v822_norm_dynamic_confirmation']:
    own = repo/'experiments'/namespace
    assert not (own/'CANDIDATE_FREEZE.json').exists()
    config = read(own/'BATCH.json')
    assert config['absolute_deadline_unix']==auth['absolute_deadline_unix']
    assert config['batch_cap_s']==auth['confirmation_cap_s' if config['confirmation'] else 'extension_cap_s']
    if config['confirmation']:
        assert read(own/'TASK_LIST.json')==read(root/'LOCKED_NEW_CONFIRMATION_TASKS.json')
    for p in own.iterdir():
        if p.is_file() and p.suffix in ['.py','.md','.json']:
            if p.suffix=='.py':ast.parse(p.read_text())
            files[str(p.relative_to(repo))]=sha(p)
    dump(own/'CANDIDATE_FREEZE.json',dict(status='FROZEN_BEFORE_ANY_NEW_MODEL',algorithm='V820_UNCHANGED',
        task_count=len(read(own/'TASK_LIST.json')),confirmation=config['confirmation'],
        absolute_deadline_unix=auth['absolute_deadline_unix'],files=dict(files)))
    files[str((own/'CANDIDATE_FREEZE.json').relative_to(repo))]=sha(own/'CANDIDATE_FREEZE.json')
dump(root/'PREPARED.json',dict(status='BOTH_STAGES_FROZEN_AND_ZERO_MODEL_QUALIFIED',new_models=0,new_integrations=0,
    extension='experiments/v821_norm_route_development/CANDIDATE_FREEZE.json',confirmation='experiments/v822_norm_dynamic_confirmation/CANDIDATE_FREEZE.json',
    absolute_deadline_unix=auth['absolute_deadline_unix']))
print(json.dumps(read(root/'PREPARED.json')))
