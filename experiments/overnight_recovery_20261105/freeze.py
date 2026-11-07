"""Freeze science, tasks, operations and saved qualification before any new model."""
import ast
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/overnight_recovery_20261105';own=repo/'experiments/v830_ranked_return_development'
assert not(root/'ROUND_WINDOW.json').exists()and not(own/'CANDIDATE_FREEZE.json').exists()
assert read(root/'ZERO_MODEL_QUALIFICATION.json')['passed']and read(root/'OPERATIONS_GATE_TESTS.json')['passed']
old=read(repo/'experiments/v828_goal_dynamic_confirmation/CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in old['files'].items()),'OLD_FROZEN_SOURCES_CHANGED'
files=dict(old['files'])
for directory in [own,common,repo/'experiments/v829_return_saved_diagnosis']:
 for p in directory.iterdir():
  if p.is_file()and p.suffix in['.py','.md','.json']:
   if p.suffix=='.py':ast.parse(p.read_text())
   files[str(p.relative_to(repo))]=sha(p)
for p in [repo/'RPCCR_OVERNIGHT_RECOVERY_AUTHORIZATION_20261105.json',repo/'docs/RPCCR_OVERNIGHT_RECOVERY_20261105_PLAN.md',root/'ZERO_MODEL_QUALIFICATION.json',root/'OPERATIONS_GATE_TESTS.json',repo/'experiments/global_day_20261104_analysis/transport_archive.py']:
 files[str(p.relative_to(repo))]=sha(p)
for directory in [root/'qualification',repo/'runs/v829_return_saved_diagnosis']:
 for p in directory.rglob('*'):
  if p.is_file()and not p.is_symlink()and p.suffix not in['.lock','.pyc']:files[str(p.relative_to(repo))]=sha(p)
manifest=dict(status='FROZEN_BEFORE_ANY_NEW_MODEL',algorithm='V830_COMPLETE_RETURN_SEARCH_ORIGINAL_CANDIDATES',scientific_revisions=1,absolute_deadline_unix=1793923200,files=files)
dump(own/'CANDIDATE_FREEZE.json',manifest)
dump(root/'PREPARED.json',dict(status='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED',source_freezes={own.name:sha(own/'CANDIDATE_FREEZE.json')},frozen_files=len(files),models=0,integrations=0,absolute_deadline_unix=1793923200,new_confirmation=0))
print('ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED',len(files))
