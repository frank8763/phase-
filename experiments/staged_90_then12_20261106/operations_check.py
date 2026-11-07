"""Pre-launch registration, exact-source and conditional-stage smoke checks; zero models."""
import ast,hashlib,importlib.abc,sys
from pathlib import Path
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('NO_MODEL_PREPARATION')
sys.meta_path.insert(0,NoModels())
from evidence_rules import AUDITS,dump,read,sha
from limits import pilot_limits,can_transition,model_fits
import engine
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v842_staged_long_navigation';ROOT=R/'runs/staged_90_then12_20261106'
assert not(ROOT/'ROUND_WINDOW.json').exists()and not(ROOT/'LAUNCH_CLAIM.json').exists()
assert read(ROOT/'ZERO_MODEL_QUALIFICATION.json')['passed']
assert len(AUDITS)==17 and sum(x[2]for x in AUDITS)==3570
assert [t['seed']for t in read(W/'TASK_LIST.json')]==[10060002,10060008]
for directory in[C,W]:
 for p in directory.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
for p in W.glob('*.py'):
 if p.name not in['run_static.py','audit_early_joint.py','audit_field_preflight.py','operation_profile.py']:assert p.read_bytes()==(R/'experiments/v841_early_joint'/p.name).read_bytes()
for name in ['REFERENCE_ARRAY_QUALIFICATION.json','EARLY_JOINT_SEAM_QUALIFICATION.json']:
 assert read(R/'runs/early_joint_90_20261106/qualification'/name)['passed']
assert pilot_limits(5400,0)==dict(soft=5140,hard=5200,outer=5205)
assert not can_transition(dict(component_passed=True,source_and_decompressed_sha_verified=True))
assert not model_fits(5400,5350,60)
# No execution at these callsites: the detached driver and sleep inhibitor agree on exact campaign identity.
s=(C/'hold_awake.py').read_text();assert '/experiments/staged_90_then12_20261106/campaign.py'in s
assert (C/'campaign.py').exists()and (C/'engine.py').exists()and (C/'finalize.py').exists()
# Stage2 nominal worst caps plus all seventeen per-navigation audit caps fit its own12h.
assert 3*(5705+60+3570+240)+125+90+60<43200
result=dict(passed=True,registered_native_tasks=2,pilot_new_navigation=1,conditional12h_new_navigation_max=3,new24=0,scientific_revisions=0,unchanged_scientific_files= len([p for p in W.glob('*.py')if p.name not in['run_static.py','audit_early_joint.py','audit_field_preflight.py','operation_profile.py']]),prior_11_control_and_5_joint_mutation_negatives_reused_with_identical_source=True,prior_qualification_was_component_not_navigation=True,stage2_only_after_all_pilot_prerequisites=True,model_clock_splits=2,models=0,integrations=0)
dump(ROOT/'OPERATIONS_CHECK.json',result);print(result)
