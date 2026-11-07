"""Check frozen phase ordering, interfaces and budget gates without models."""
import ast
from pathlib import Path
from evidence_rules import dump,read
repo=Path(__file__).resolve().parents[2];root=repo/'runs/forward_escape_night_20261105';common=Path(__file__).parent;own=repo/'experiments/v832_forward_escape_development';probe=repo/'experiments/v831_forward_escape_qualification'
for directory in[common,own,probe]:
 for p in directory.glob('*.py'):ast.parse(p.read_text())
auth=read(repo/'RPCCR_FORWARD_ESCAPE_NIGHT_AUTHORIZATION_20261105.json');cfg=read(own/'BATCH.json');assert auth['absolute_deadline_unix']==cfg['absolute_deadline_unix']==1793923200 and auth['max_scientific_candidates']==1 and auth['post_freeze_repairs']==0
assert[entry['step']for entry in read(probe/'FIXED_INPUTS.json')]==[495,527]
assert read(root/'qualification/LIBRARY_QUALIFICATION.json')['passed']and read(root/'qualification/RETURN_SEARCH_QUALIFICATION.json')['passed']
tasks=read(own/'TASK_LIST.json');assert[t['seed']for t in tasks]==[10060002,10060008,10010002,10010001,10010003]and cfg['repeat_slots']==[1,2,3,4,5]
campaign=(common/'campaign.py').read_text();assert campaign.index('component_final=run_component')<campaign.index("active=subprocess.Popen")
assert "if not component_final['component_passed']"in campaign and "INSUFFICIENT_REMAINING_NAVIGATION_BUDGET"in campaign
assert 'PHASE_ESCAPE_DEADLINE'in(common/'component.py').read_text()and "ALREADY_CLAIMED_NO_SECOND_INSTANCE"in(common/'launch.py').read_text()
runner=(common/'runner.py').read_text();assert 'min(cap,deadline-time.time())'in runner and "if not config['confirmation']or failures>=2"in runner
baseline=repo/'experiments/v830_ranked_return_development';changed=[]
for p in own.glob('*.py'):
 if(baseline/p.name).exists()and p.read_bytes()!=(baseline/p.name).read_bytes():changed.append(p.name)
assert set(changed)=={'run_static.py','reserved_recovery.py','audit_run.py','audit_all_tail_geometry.py','execute.py','finalize.py'},changed
assert(own/'run_static.py').read_text().replace("'v832_forward_escape_development'","'v830_ranked_return_development'")==(baseline/'run_static.py').read_text()
for name in ['recovery_supervisor.py','norm_gate.py','motion_tracker.py','joint_admission.py','serial_predictor.py','geometry_predictor.py']:
 assert(own/name).read_bytes()==(baseline/name).read_bytes()
assert 'candidate.allow_forward_escape=True'in(own/'reserved_recovery.py').read_text()
fits=lambda now,cap,deadline:now+cap+3<deadline
assert fits(0,1200,1204)and not fits(0,1200,1203)and not fits(10,1505,1500)
dump(root/'OPERATIONS_GATE_TESTS.json',dict(passed=True,component_before_navigation=True,component_must_pass_audit_and_full_sha_archive=True,same_morning_hard_deadline=True,no_post_freeze_repair=True,five_known_tasks_conditional_full_repeats=True,full_subprocess_budget_reservation=True,changed_source_files=changed,scientific_change_only_return_library=True,models=0,integrations=0))
print('COMPONENT_TO_NAVIGATION_OPERATIONS_GATES_PASS')
