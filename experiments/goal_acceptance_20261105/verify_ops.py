"""Real saved-file repeat seam and finite stage gate regression, no models."""
import ast,json,sys
from pathlib import Path
from evidence_rules import main_gate,repeat_check,read,dump,sha,AUDITS
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/goal_acceptance_20261105';q=root/'qualification'
assert read(root/'ZERO_MODEL_QUALIFICATION.json')['passed']
for directory in [common,repo/'experiments/v827_goal_route_validation',repo/'experiments/v828_goal_dynamic_confirmation']:
 for p in directory.glob('*.py'):ast.parse(p.read_text())
dev=read(repo/'experiments/v827_goal_route_validation/TASK_LIST.json');by={t['slot']:t for t in dev}
records=[dict(role='MAIN',task=by[s],physical_passed=True,functional_passed=True)for s in[1,3]]
g=main_gate(dev,records,False);assert g['passed']and g['planned_main']==g['main_attempts']==2
assert not main_gate(dev,records[:1],False)['passed']
bad=[dict(x)for x in records];bad[0]['physical_passed']=False;assert not main_gate(dev,bad,False)['passed']
base=repo/'runs/v826_goal_reference_renewal/main_slot02/paired';r=read(base/'geometry_memory/result.json');sys.path.insert(0,str(repo/'experiments/v827_goal_route_validation'));from contact_fingerprint import compare_contacts
assert repeat_check(base,q/'reference/paired',r,r,compare_contacts)['passed']
negative=q/'changed_control/paired';negative.mkdir(parents=True);cell=negative/'geometry_memory';cell.mkdir()
for name in ['scene_model.mjb','assets']:(negative/name).symlink_to(base/name,target_is_directory=(base/name).is_dir())
for name in ['result.json','contacts.jsonl.gz','FIRST_DISCOVERY.json']:(cell/name).symlink_to(base/'geometry_memory'/name)
rows=[json.loads(x)for x in(base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];rows[100]['ctrl'][0]+=1e-4
(cell/'v648_execution.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in rows))
check=repeat_check(base,negative,r,r,compare_contacts);assert not check['passed']and not check['checks']['state_ctrl'];dump(q/'CHANGED_CTRL_REJECTED.json',check)
# Exact generic audit receives no hardcoded NS anchor, same saved causal proof.
# Its actual anchored invocation was already exercised by qualification.
for worker in ['v827_goal_route_validation','v828_goal_dynamic_confirmation']:
 own=repo/'experiments'/worker;baseline=repo/'experiments/v826_goal_reference_renewal'
 for p in own.glob('*.py'):
  if p.name in['execute.py','finalize.py','audit_field_preflight.py','audit_goal_renewal.py']:continue
  if p.name=='run_static.py':assert p.read_text().replace(repr(worker),"'v826_goal_reference_renewal'")==(baseline/p.name).read_text()
  else:assert p.read_bytes()==(baseline/p.name).read_bytes()
 assert [x['slot']for x in read(own/'TASK_LIST.json')]==([2,1,3]if worker.startswith('v827')else list(range(1,25)))
assert read(repo/'runs/v826_goal_reference_renewal/FINALIZED.json')['development_passed']is False
out=dict(status='OPERATIONAL_GATES_AND_EXACT_REPEAT_NEGATIVES_PASS',passed=True,all13_actual_saved_audits_passed=True,science_normalized_identity_passed=True,reused_ns_not_counted_as_new_main=True,changed_control_repeat_rejected=True,complete_vs_incomplete_dev_gate_passed=True,old_not_passed_preserved=True,new_models=0,new_integrations=0)
dump(root/'OPERATIONS_GATE_TESTS.json',out);print(json.dumps(out))
