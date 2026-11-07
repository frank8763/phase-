"""Freeze all science, operations, tasks and negative gates before any new model."""
import ast,json
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/goal_acceptance_20261105'
assert read(root/'ZERO_MODEL_QUALIFICATION.json')['passed'];assert not(root/'ROUND_WINDOW.json').exists()
base=read(repo/'experiments/v826_goal_reference_renewal/CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in base['files'].items())
files=dict(base['files']);auth=read(repo/'RPCCR_GOAL_ACCEPTANCE_AUTHORIZATION_20261105.json')
for p in [repo/'RPCCR_GOAL_ACCEPTANCE_AUTHORIZATION_20261105.json',repo/'docs/RPCCR_GOAL_ACCEPTANCE_20261105_PLAN.md',root/'ALGORITHM_IDENTITY.json',root/'POOL_UNUSED.json',root/'RESERVED_CONFIRMATION_TASKS.json',root/'ZERO_MODEL_QUALIFICATION.json',root/'OPERATIONS_GATE_TESTS.json',repo/'experiments/global_day_20261104_analysis/transport_archive.py',repo/'runs/v826_goal_reference_renewal/FINALIZED.json',repo/'runs/v826_goal_reference_renewal/FINAL_INDEPENDENT_AUDIT.json']:
 files[str(p.relative_to(repo))]=sha(p)
for p in common.glob('*.py'):ast.parse(p.read_text());files[str(p.relative_to(repo))]=sha(p)
for p in (root/'qualification').rglob('*'):
 if p.is_file()and not p.is_symlink()and p.suffix not in['.lock','.pyc']:files[str(p.relative_to(repo))]=sha(p)
# Critical full-state/contact/model/reference files are checked at each subprocess.
reference=repo/'runs/v826_goal_reference_renewal/main_slot02/paired'
for p in [*reference.glob('*.json'),reference/'scene_model.mjb',reference/'assets/isolated_indoor.xml',*reference.parent.joinpath('source_snapshot').glob('*.py'),*reference.joinpath('geometry_memory').glob('*.jsonl'),reference/'geometry_memory/dynamic_native.jsonl.gz',reference/'geometry_memory/contacts.jsonl.gz']:
 files[str(p.relative_to(repo))]=sha(p)
for name in ['v827_goal_route_validation','v828_goal_dynamic_confirmation']:
 own=repo/'experiments'/name;assert not(own/'CANDIDATE_FREEZE.json').exists();cfg=read(own/'BATCH.json');assert cfg['absolute_deadline_unix']==auth['absolute_deadline_unix']
 for p in own.iterdir():
  if p.is_file()and p.suffix in['.py','.md','.json']:
   if p.suffix=='.py':ast.parse(p.read_text())
   files[str(p.relative_to(repo))]=sha(p)
# Each stage includes both stages, so future confirmation science is already frozen.
for name in ['v827_goal_route_validation','v828_goal_dynamic_confirmation']:
 own=repo/'experiments'/name;dump(own/'CANDIDATE_FREEZE.json',dict(status='FROZEN_BEFORE_ANY_NEW_MODEL',algorithm='V826_EXACT_SCIENCE',confirmation=read(own/'BATCH.json')['confirmation'],absolute_deadline_unix=auth['absolute_deadline_unix'],files=files))
dump(root/'PREPARED.json',dict(status='BOTH_STAGES_FROZEN_AND_ZERO_MODEL_QUALIFIED',new_models=0,new_integrations=0,frozen_files=len(files),source_freezes={name:sha(repo/'experiments'/name/'CANDIDATE_FREEZE.json')for name in ['v827_goal_route_validation','v828_goal_dynamic_confirmation']},absolute_deadline_unix=auth['absolute_deadline_unix']))
print(json.dumps(read(root/'PREPARED.json')))
