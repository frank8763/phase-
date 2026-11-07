"""Freeze this independent joint candidate and complete offline schedule before any model."""
import ast
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/timed_escape_night_20261105';science=repo/'experiments/v834_timed_escape_development';probe=repo/'experiments/v833_timed_escape_qualification'
assert not(root/'ROUND_WINDOW.json').exists()and not(science/'CANDIDATE_FREEZE.json').exists()and not(probe/'INPUT_FREEZE.json').exists()
assert read(root/'ZERO_MODEL_QUALIFICATION.json')['passed']and read(root/'OPERATIONS_GATE_TESTS.json')['passed']and read(root/'qualification/TIMED_GATE_QUALIFICATION.json')['passed']
old=read(repo/'experiments/v832_forward_escape_development/CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in old['files'].items())
files=dict(old['files'])
for directory in[common,science,probe]:
 for p in directory.iterdir():
  if p.is_file()and p.suffix in['.py','.md','.json']:
   if p.suffix=='.py':ast.parse(p.read_text())
   files[str(p.relative_to(repo))]=sha(p)
for n in['RPCCR_TIMED_ESCAPE_NIGHT_AUTHORIZATION_20261105.json','docs/RPCCR_TIMED_ESCAPE_NIGHT_20261105_PLAN.md','docs/RPCCR_ALGORITHM_COMPARISON_20261106_PLAN.md','docs/RPCCR_ALGORITHM_COMPARISON_20261106_TIMED_ESCAPE_ENTRY.md','runs/timed_escape_night_20261105/ZERO_MODEL_QUALIFICATION.json','runs/timed_escape_night_20261105/OPERATIONS_GATE_TESTS.json','runs/timed_escape_night_20261105/qualify_library.console','runs/timed_escape_night_20261105/qualify_timed_gate.console','runs/timed_escape_night_20261105/qualify_timed_gate_ready02.console','runs/timed_escape_night_20261105/ZERO_MODEL_TOOL_INTERRUPTION.json']:
 files[n]=sha(repo/n)
for p in(root/'qualification').rglob('*'):
 if p.is_file()and not p.is_symlink()and p.suffix not in['.lock','.pyc']:files[str(p.relative_to(repo))]=sha(p)
manifest=dict(status='FROZEN_BEFORE_ANY_NEW_MODEL',algorithm='RETURN_ONLY_JOINT_SPEED_BRAKE_WITH_GOAL_PROGRESS',absolute_deadline_unix=1793923200,scientific_revisions=1,files=files)
dump(probe/'INPUT_FREEZE.json',manifest);dump(science/'CANDIDATE_FREEZE.json',manifest)
dump(root/'PREPARED.json',dict(status='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED',source_freezes={science.name:sha(science/'CANDIDATE_FREEZE.json'),probe.name:sha(probe/'INPUT_FREEZE.json')},frozen_files=len(files),models=0,integrations=0,absolute_deadline_unix=1793923200,new_confirmation=0))
print('JOINT_SPEED_BRAKE_AND_CONDITIONAL_NAVIGATION_FROZEN',len(files))
