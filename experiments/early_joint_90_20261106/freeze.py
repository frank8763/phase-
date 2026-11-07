"""One-shot source freeze and fresh 5400-second hard window, before any new model."""
import ast,fcntl,json,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;own=repo/'experiments/v841_early_joint';root=repo/'runs/early_joint_90_20261106';ap=repo/'RPCCR_EARLY_JOINT_90_AUTHORIZATION_20261106.json';auth=read(ap)
assert auth['absolute_deadline_unix']is None and not(root/'ROUND_WINDOW.json').exists()and not(own/'CANDIDATE_FREEZE.json').exists()
for n in ['ZERO_MODEL_QUALIFICATION.json','qualification/REFERENCE_ARRAY_QUALIFICATION.json','qualification/EARLY_JOINT_SEAM_QUALIFICATION.json']:assert read(root/n)['passed']
assert(repo/'REVIEW_PENDING').exists()
with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=dict(read(repo/'experiments/v838_reference_differential_qualification/INPUT_FREEZE.json')['files']);assert all(sha(repo/n)==h for n,h in files.items())
# Include the exact newly derived295 inputs and the full old actual/calibration evidence.
for d in [common,own,root/'qualification',repo/'runs/v830_ranked_return_development/main_slot01/paired']:
 for p in d.rglob('*'):
  if p.is_file()and not p.is_symlink()and p.suffix not in['.pyc','.lock']and '__pycache__'not in p.parts:
   if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
   files[str(p.relative_to(repo))]=sha(p)
started=time.time();deadline=started+5400;auth.update(model_window_started_unix=started,absolute_deadline_unix=deadline,hard_stop_beijing=datetime.fromtimestamp(deadline,timezone(timedelta(hours=8))).isoformat());dump(ap,auth)
config=read(own/'BATCH.json');config['absolute_deadline_unix']=deadline;dump(own/'BATCH.json',config)
for p in [ap,own/'BATCH.json',repo/'docs/RPCCR_EARLY_JOINT_90_20261106_PLAN.md',root/'ZERO_MODEL_QUALIFICATION.json']:
 files[str(p.relative_to(repo))]=sha(p)
manifest=dict(status='FROZEN_BEFORE_ANY_NEW_MODEL',algorithm='EARLY_JOINT_COMPLETE_TAIL_SELECTION',scientific_candidates=1,absolute_deadline_unix=deadline,files=files)
dump(own/'INPUT_FREEZE.json',manifest);dump(own/'CANDIDATE_FREEZE.json',manifest)
dump(root/'PREPARED.json',dict(status='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED',source_freezes={own.name:sha(own/'CANDIDATE_FREEZE.json')},qualification_freeze=sha(own/'INPUT_FREEZE.json'),frozen_files=len(files),models=0,integrations=0,absolute_deadline_unix=deadline))
print(json.dumps(dict(status='FROZEN',files=len(files),hard_stop_beijing=auth['hard_stop_beijing'],models=0)))
