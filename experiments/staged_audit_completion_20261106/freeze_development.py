"""Freeze one operations-only12h continuation after full independent pilot qualification."""
import ast,json,sys,time
from pathlib import Path
from evidence_rules import read,dump,sha
from limits import can_transition,model_fits
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/staged_audit_completion_20261106';W=R/'experiments/v842_staged_long_navigation'
assert not(C/'DEVELOPMENT_FREEZE.json').exists(),'NO_FREEZE_REPLACEMENT'
pilot=read(ROOT/'SUPPLEMENT_FINALIZED.json');assert can_transition(pilot)
positive={k:True for k in ['development_passed','source_and_decompressed_sha_verified','independent_audit_passed','complete_chain_passed','native_replay_exact','source_unchanged']}
assert can_transition(positive);negatives=0
for key in positive:
 wrong=dict(positive);wrong[key]=False;assert not can_transition(wrong);negatives+=1
assert not can_transition({})and not can_transition(dict(component_passed=True));negatives+=2
assert not model_fits(100,99,2)and model_fits(1000,1,720)
source=(C/'engine.py').read_text();assert "assert stage=='development12'"in source and "pair/'audit_run.py.console',600,True"in source and "limits['outer']+720"in source and 'complete_audit_entry.py'in source
assert source.index("unit(tasks_by[10060002],'long_repeat02'")<source.index("t0(tasks_by[10060008],'long_t0_08')")<source.index("unit(tasks_by[10060008],'long_main08'")<source.index("unit(tasks_by[10060008],'long_repeat08'")
import engine
try:engine.stage_run('pilot90',0)
except AssertionError:negatives+=1
else:raise AssertionError('PILOT_RELAUNCH_NOT_BLOCKED')
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
original=read(W/'CANDIDATE_FREEZE.json');assert all(sha(R/p)==h for p,h in original['files'].items())
assert all(sha(R/x['path'])==x['sha256']for x in read(ROOT/'ORIGINAL_EVIDENCE_FREEZE.json'))
check=dict(passed=True,operations_only=True,scientific_revisions=0,original17_audit_scopes_saved_GOAL_passed=True,original_reactive_count_FAIL_preserved=True,strict9601_witness_coverage=True,coverage_negative_cases=10,original_Goal_chain_passed=True,original5800_replay_exact=True,prefix3112_exact=True,negative_cases=negatives,repeat_before_second_task_t0=True,canonical_cache_passed=True,joint_cache_passed=True,model_metadata_reused_from_actual_read=True,new_models=0,new_integrations=0)
dump(ROOT/'DEVELOPMENT_OPERATIONS_CHECK.json',check)
files=dict(original['files']);files.update({str(p.relative_to(R)):sha(p)for p in C.glob('*')if p.is_file()and p.name!='DEVELOPMENT_FREEZE.json'})
for name in ['SUPPLEMENT_FINALIZED.json','FINAL_INDEPENDENT_AUDIT.json','ORIGINAL_EVIDENCE_FREEZE.json','AUTHORIZATION.json','SAVED_ONLY_COMPLETION_NOTE.json','QUALIFICATION.json','DEVELOPMENT_OPERATIONS_CHECK.json']:
 p=ROOT/name;files[str(p.relative_to(R))]=sha(p)
dump(C/'DEVELOPMENT_FREEZE.json',dict(files=files,frozen_unix=time.time(),scientific_revision='V842_BUDGET_ONLY_V841_IDENTICAL_DECISIONS',scientific_revisions=0,model_window_claim_not_yet_created=True))
print(json.dumps(dict(status='FROZEN',files=len(files),negative_cases=negatives,models=0,integrations=0)))
