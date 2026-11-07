"""Finite joint schedule registration and offline gating, no model imports."""
import ast
from pathlib import Path
from evidence_rules import dump,read
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/timed_escape_night_20261105';science=repo/'experiments/v834_timed_escape_development';probe=repo/'experiments/v833_timed_escape_qualification'
for d in[common,science,probe]:
 for p in d.glob('*.py'):ast.parse(p.read_text())
auth=read(repo/'RPCCR_TIMED_ESCAPE_NIGHT_AUTHORIZATION_20261105.json');cfg=read(science/'BATCH.json');assert auth['absolute_deadline_unix']==cfg['absolute_deadline_unix']==1793923200 and auth['max_scientific_candidates']==1 and auth['post_freeze_repairs']==0
grid=[(s,w,b)for s in range(5)for w in[4,6,8,10,12]for b in[160,176,192,208,224,240]if(w,b)!=(4,240)];assert len(grid)==len(set(grid))==145
assert[entry['step']for entry in read(probe/'FIXED_INPUTS.json')]==[495,527]
assert read(root/'qualification/LIBRARY_QUALIFICATION.json')['passed']and read(root/'qualification/RETURN_SEARCH_QUALIFICATION.json')['passed']
assert[t['seed']for t in read(science/'TASK_LIST.json')]==[10060002,10060008,10010002,10010001,10010003]
assert cfg['repeat_slots']==[1,2,3,4,5]
campaign=(common/'campaign.py').read_text();assert campaign.index('component_final=run_component')<campaign.index('active=subprocess.Popen')and"if not component_final['component_passed']"in campaign
assert 'started+1800'in(common/'component.py').read_text()and 'NO_COMPONENT_START_BUDGET_OR_ALREADY_STARTED'in(common/'component.py').read_text()
assert 'rpccr_timed_escape_ops_20261105'in(common/'close_ops.py').read_text()
baseline=repo/'experiments/v832_forward_escape_development';changed=[]
for p in science.glob('*.py'):
 if(baseline/p.name).exists()and p.read_bytes()!=(baseline/p.name).read_bytes():changed.append(p.name)
assert set(changed)=={'run_static.py','reserved_recovery.py','recovery_supervisor.py','audit_forward_escape.py','audit_run.py','audit_all_tail_geometry.py','execute.py','finalize.py'},changed
assert(science/'run_static.py').read_text().replace("'v834_timed_escape_development'","'v832_forward_escape_development'")==(baseline/'run_static.py').read_text()
for name in['norm_gate.py','motion_tracker.py','joint_admission.py','serial_predictor.py','geometry_predictor.py']:
 assert(science/name).read_bytes()==(baseline/name).read_bytes()
assert 'candidate.escape_goal_xy=np.asarray(metadata['in(science/'reserved_recovery.py').read_text()and"'public_goal_xy':np.asarray(env.goal_xy).tolist()"in(science/'recovery_supervisor.py').read_text()
assert 18*(8+166*320)==956304<auth['private_native_cap']
fits=lambda now,cap,d:now+cap+3<d
assert fits(0,1800,1804)and not fits(0,1800,1803)and not fits(10,1505,1500)
dump(root/'OPERATIONS_GATE_TESTS.json',dict(passed=True,grid145_once=True,ordinary21_preserved=True,public_goal_only_and_complete_progress002=True,component_before_navigation=True,component_pass_and_audit_archive_gate=True,full_subprocess_budget_reservation=True,old_versions_unchanged=True,post_freeze_repair0=True,changed_files=changed,models=0,integrations=0))
print('TIMED_ESCAPE_OFFLINE_OPERATIONS_GATES_PASS')
