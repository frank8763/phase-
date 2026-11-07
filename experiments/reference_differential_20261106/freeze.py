"""Freeze the complete one-candidate conditional schedule before model startup."""
import ast
import json
import math
from pathlib import Path
import time
from evidence_rules import dump,read,sha,main_gate
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent
root=repo/'runs/reference_differential_20261106'
workers=[repo/'experiments'/x for x in ['v838_reference_differential_qualification','v839_reference_differential_development','v840_reference_differential_confirmation']]
auth=read(repo/'RPCCR_REFERENCE_DIFFERENTIAL_AUTHORIZATION_20261106.json')
assert not(root/'ROUND_WINDOW.json').exists()
assert all(not(w/'INPUT_FREEZE.json').exists()and not(w/'CANDIDATE_FREEZE.json').exists()for w in workers)
assert read(root/'ZERO_MODEL_QUALIFICATION.json')['passed']
assert read(root/'qualification/REFERENCE_ARRAY_QUALIFICATION.json')['passed']
assert read(root/'qualification/VEHICLE_REAR_DIFFERENTIAL.json')['gain']==8.0
tasks=read(workers[2]/'TASK_LIST.json')
rows=[dict(role='MAIN',task=t,physical_passed=True,functional_passed=True)for t in tasks]
assert main_gate(tasks,rows,True)['passed']
assert main_gate(tasks,rows[:-1],True)['success_rate']is None
bad=[dict(x)for x in rows];bad[0]['functional_passed']=False
assert main_gate(tasks,bad,True)['passed']
bad[8]['functional_passed']=False;assert not main_gate(tasks,bad,True)['passed']
assert not main_gate(tasks,rows[::-1],True)['passed']
for t in tasks:
 assert (math.cos(t['phase'])>0)==(t['initial_axis_motion_direction']=='POSITIVE_AXIS')
assert time.time()+36000<auth['absolute_deadline_unix']
assert (repo/'REVIEW_PENDING').exists()
files=dict(read(repo/'experiments/v833_timed_escape_qualification/INPUT_FREEZE.json')['files'])
assert all(sha(repo/n)==h for n,h in files.items()),'OLD_FROZEN_SOURCES_CHANGED'
for directory in [common,*workers]:
 for p in directory.iterdir():
  if p.is_file()and p.suffix in['.py','.md','.json']:
   if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
   files[str(p.relative_to(repo))]=sha(p)
for directory in [root/'qualification']:
 for p in directory.rglob('*'):
  if p.is_file()and not p.is_symlink()and p.suffix not in['.pyc','.lock']and p.name!='VERIFICATION.json':
   files[str(p.relative_to(repo))]=sha(p)
for name in ['RPCCR_REFERENCE_DIFFERENTIAL_AUTHORIZATION_20261106.json','docs/RPCCR_REFERENCE_DIFFERENTIAL_20261106_PLAN.md','runs/reference_differential_20261106/HANDOFF.md','runs/reference_differential_20261106/ZERO_MODEL_QUALIFICATION.json','runs/reference_differential_20261106/qualify_reference.console','runs/reference_differential_20261106/qualify_reference_ready02.console']:
 files[name]=sha(repo/name)
operations=dict(passed=True,positive_confirmation_gate=True,first_failure_tolerated=True,second_failure_stops=True,incomplete_denominator_rate_null=True,reordered_tasks_rejected=True,
 original_deadlines_closed=True,root_absolute_deadline=auth['absolute_deadline_unix'],first_model_not_started=True,models=0,integrations=0)
dump(root/'OPERATIONS_GATE_TESTS.json',operations);files[str((root/'OPERATIONS_GATE_TESTS.json').relative_to(repo))]=sha(root/'OPERATIONS_GATE_TESTS.json')
manifest=dict(status='FROZEN_BEFORE_ANY_NEW_MODEL',algorithm='CAUSAL_REFERENCE_FOLLOWING_WITH_FINITE_SUCCESSOR',scientific_candidates=1,candidate_index_in_user_round=2,no_more_scientific_revisions=True,absolute_deadline_unix=auth['absolute_deadline_unix'],files=files)
source_freezes={}
for worker in workers:
 p=worker/('INPUT_FREEZE.json'if worker==workers[0]else'CANDIDATE_FREEZE.json')
 dump(p,manifest);source_freezes[worker.name]=sha(p)
dump(root/'PREPARED.json',dict(status='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED',source_freezes=source_freezes,frozen_files=len(files),models=0,integrations=0,absolute_deadline_unix=auth['absolute_deadline_unix'],conditional_new_confirmation_tasks=24))
print(json.dumps(dict(status='ALL_THREE_STAGES_FROZEN',files=len(files),deadline=auth['hard_stop_beijing'],models=0,integrations=0)))
