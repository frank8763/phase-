"""One-shot freeze; fix only the new pilot deadline, never a previous clock."""
import ast,fcntl,json,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from evidence_rules import dump,read,sha
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v842_staged_long_navigation';ROOT=R/'runs/staged_90_then12_20261106';A=R/'RPCCR_STAGED_90_THEN12_AUTHORIZATION_20261106.json';auth=read(A)
assert auth['stage1_absolute_deadline_unix']is None and not(W/'CANDIDATE_FREEZE.json').exists()and not(ROOT/'ROUND_WINDOW.json').exists()
assert read(ROOT/'ZERO_MODEL_QUALIFICATION.json')['passed']and read(ROOT/'OPERATIONS_CHECK.json')['passed']and(R/'REVIEW_PENDING').exists()
with(R/'runs/v648_static_unknown/execution.lock').open('rb')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert __import__('shutil').disk_usage(ROOT).free>=80*1024**3,'INSUFFICIENT_INITIAL_EVIDENCE_DISK'
old=read(R/'experiments/v841_early_joint/CANDIDATE_FREEZE.json')['files'];files={n:h for n,h in old.items()if not n.startswith('runs/')};assert all(sha(R/n)==h for n,h in files.items())
for directory in[C,W,ROOT/'qualification']:
 for p in directory.rglob('*'):
  if p.is_file()and not p.is_symlink()and p.suffix not in['.lock','.pyc']and '__pycache__'not in p.parts:
   if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
   files[str(p.relative_to(R))]=sha(p)
for relative in ['runs/v690_visible_eight_meter/training_8m/proposer.json','runs/v841_early_joint/main_slot01/paired/geometry_memory/dynamic_native.jsonl.gz','runs/v841_early_joint/main_slot01/paired/geometry_memory/result.json','runs/v830_ranked_return_development/main_slot01/paired/geometry_memory/dynamic_native.jsonl.gz','runs/v828_goal_dynamic_confirmation/main_slot08/paired/geometry_memory/dynamic_native.jsonl.gz','evidence/rpccr_early_joint_v841_20261106/MANIFEST.json','evidence/rpccr_early_joint_v841_20261106/RAW_INVENTORY.json.gz','runs/staged_90_then12_20261106/DECISION_PRESERVATION_REGISTRATION.json','runs/staged_90_then12_20261106/ZERO_MODEL_QUALIFICATION.json','runs/staged_90_then12_20261106/OPERATIONS_CHECK.json','runs/staged_90_then12_20261106/qualify.console','runs/staged_90_then12_20261106/operations_check.console','runs/staged_90_then12_20261106/HANDOFF.md','docs/RPCCR_STAGED_90_THEN12_20261106_PLAN.md']:
 files[relative]=sha(R/relative)
start=time.time();deadline=start+5400;auth.update(stage1_started_unix=start,stage1_absolute_deadline_unix=deadline,stage1_hard_stop_beijing=datetime.fromtimestamp(deadline,timezone(timedelta(hours=8))).isoformat());dump(A,auth);files[str(A.relative_to(R))]=sha(A)
manifest=dict(status='FROZEN_BEFORE_FIRST_NEW_MODEL',scientific_algorithm='V841_UNCHANGED',scientific_revisions=0,stage1_absolute_deadline_unix=deadline,stage2_duration_if_all_pilot_gates_pass_s=43200,files=files);dump(W/'CANDIDATE_FREEZE.json',manifest);dump(ROOT/'PREPARED.json',dict(status='FROZEN_AND_ZERO_MODEL_QUALIFIED',freeze_sha256=sha(W/'CANDIDATE_FREEZE.json'),files=len(files),models=0,integrations=0,stage1_deadline_unix=deadline));print(json.dumps(dict(status='FROZEN',files=len(files),pilot_hard_stop=auth['stage1_hard_stop_beijing'],stage2_not_started=True)))
