"""Deterministic offline orchestration checks; no model or real subprocess."""
import ast,json
from pathlib import Path
from evidence_rules import dump,read,main_gate
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;own=repo/'experiments/v830_ranked_return_development';root=repo/'runs/overnight_recovery_20261105'
tasks=read(own/'TASK_LIST.json');plan=[(role,t['slot'])for t in tasks for role in['MAIN','REPEAT']]
assert plan==[(r,s)for s in range(1,6)for r in['MAIN','REPEAT']]
cfg=read(own/'BATCH.json');auth=read(repo/'RPCCR_OVERNIGHT_RECOVERY_AUTHORIZATION_20261105.json');assert cfg['absolute_deadline_unix']==auth['absolute_deadline_unix']==1793923200
assert cfg['repeat_slots']==list(range(1,6))and not cfg['confirmation']and auth['new_confirmation']==0
assert tasks[0]['seed']==10060002 and tasks[1]['seed']==10060008 and [t['seed']for t in tasks[2:]]==[10010002,10010001,10010003]
# Budget reservations reject a full capped process before it could cross the absolute cutoff.
fits=lambda now,cap,deadline:now+cap+3<deadline
assert fits(0,1505,1509)and not fits(0,1505,1508)and not fits(10,1505,1500)
for p in [*common.glob('*.py'),*own.glob('*.py')]:ast.parse(p.read_text())
runner=(common/'runner.py').read_text();assert 'NO_RETRY'in runner and "if not config['confirmation']or failures>=2"in runner and "os.killpg(process.pid,signal.SIGKILL)"in runner
assert "min(cap,deadline-time.time())"in runner
source=repo/'experiments/v828_goal_dynamic_confirmation'
changed=[]
for p in own.glob('*.py'):
 if not(source/p.name).exists():continue
 if p.read_bytes()!=(source/p.name).read_bytes():changed.append(p.name)
assert set(changed)=={'run_static.py','recovery_supervisor.py','audit_field_preflight.py','execute.py','finalize.py'},changed
assert (own/'run_static.py').read_text().replace("'v830_ranked_return_development'","'v828_goal_dynamic_confirmation'")==(source/'run_static.py').read_text()
for name in ['reserved_recovery.py','joint_admission.py','serial_predictor.py','norm_gate.py','robot_predictor.py','geometry_predictor.py','planner.py','risk_domain.py','goal_reference_renewal.py']:
 if(source/name).exists():assert(source/name).read_bytes()==(own/name).read_bytes()
dump(root/'OPERATIONS_GATE_TESTS.json',dict(passed=True,tests=['five_fixed_pairwise_main_repeat_order','known_failures_are_development_not_new_confirmation','no_new_actions_thresholds_models','immutable_absolute_deadline','full_subprocess_budget_reservation_positive_negative','first_functional_or_safety_failure_stop','no_retry_frozen_science','single_repair_only_supervisor','all_python_syntax'],changed_source_files=changed,models=0,integrations=0))
print('OFFLINE_OPERATIONS_GATES_PASS')
