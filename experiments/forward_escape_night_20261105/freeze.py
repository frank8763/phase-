"""Freeze component, conditional global science, operations and all actual inputs."""
import ast
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/forward_escape_night_20261105';own=repo/'experiments/v832_forward_escape_development';probe=repo/'experiments/v831_forward_escape_qualification'
assert not(root/'ROUND_WINDOW.json').exists()and not(own/'CANDIDATE_FREEZE.json').exists()and not(probe/'INPUT_FREEZE.json').exists()
assert read(root/'ZERO_MODEL_QUALIFICATION.json')['passed']and read(root/'OPERATIONS_GATE_TESTS.json')['passed']
old=read(repo/'experiments/v830_ranked_return_development/CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in old['files'].items())
files=dict(old['files'])
for directory in[common,own,probe]:
 for p in directory.iterdir():
  if p.is_file()and p.suffix in['.py','.json','.md']:
   if p.suffix=='.py':ast.parse(p.read_text())
   files[str(p.relative_to(repo))]=sha(p)
for n in ['RPCCR_FORWARD_ESCAPE_NIGHT_AUTHORIZATION_20261105.json','docs/RPCCR_FORWARD_ESCAPE_NIGHT_20261105_PLAN.md','docs/RPCCR_ALGORITHM_COMPARISON_20261106_PLAN.md','runs/forward_escape_night_20261105/ZERO_MODEL_QUALIFICATION.json','runs/forward_escape_night_20261105/OPERATIONS_GATE_TESTS.json','runs/forward_escape_night_20261105/original_forward_red.console','runs/forward_escape_night_20261105/qualify_library.console','runs/forward_escape_night_20261105/qualify_library_ready02.console']:
 files[n]=sha(repo/n)
for p in(root/'qualification').rglob('*'):
 if p.is_file()and not p.is_symlink()and p.suffix not in['.lock','.pyc']:files[str(p.relative_to(repo))]=sha(p)
pair=repo/'runs/v830_ranked_return_development/main_slot01/paired';cell=pair/'geometry_memory'
for p in [*pair.glob('*.json'),pair/'scene_model.mjb',pair/'assets/isolated_indoor.xml',cell/'ACTUATOR_COMMAND_CONTRACT.json',cell/'dynamic_native.jsonl.gz',cell/'sensor_packets.jsonl.gz',cell/'contacts.jsonl.gz',cell/'v648_execution.jsonl',cell/'control_decisions.jsonl']:
 files[str(p.relative_to(repo))]=sha(p)
for entry in read(probe/'FIXED_INPUTS.json'):
 for c in entry['nominal']:
  p=cell/'nominal_forecasts'/c['nominal_saved_forecast'];files[str(p.relative_to(repo))]=sha(p)
 for a in entry['old_attempts']:
  for c in a['detail']['candidates']:
   p=cell/c['early_rejection_witness_file'];files[str(p.relative_to(repo))]=sha(p)
manifest=dict(status='FROZEN_BEFORE_ANY_NEW_MODEL',algorithm='RETURN_ONLY_FORWARD_ESCAPE_AFTER_ORIGINAL21',scientific_revisions=1,absolute_deadline_unix=1793923200,files=files)
dump(probe/'INPUT_FREEZE.json',manifest);dump(own/'CANDIDATE_FREEZE.json',manifest)
dump(root/'PREPARED.json',dict(status='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED',source_freezes={own.name:sha(own/'CANDIDATE_FREEZE.json'),probe.name:sha(probe/'INPUT_FREEZE.json')},frozen_files=len(files),models=0,integrations=0,absolute_deadline_unix=1793923200,new_confirmation=0))
print('COMPONENT_AND_CONDITIONAL_NAVIGATION_FROZEN',len(files))
