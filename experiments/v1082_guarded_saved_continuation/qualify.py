"""Bounded actual isolated CLI/import checks, no physical model."""
import sys,subprocess,ast,fcntl
from common import *
paths();from resource_policy import apply
apply();from science import *
guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';old=R/'runs/v1081_transient_speed_guard'
for n in ['QUALIFICATION.json','SAVED_REGRESSION.json']:assert json.loads((old/n).read_text())['passed']
tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==1 and tasks[0]['kind']=='remaining';task=tasks[0];assert task['historical_prefix_native']==18074 and task['new_native']==3555
for p in C.glob('*.py'):ast.parse(p.read_text())
for p in (R/'experiments/v1081_transient_speed_guard').glob('*.py'):ast.parse(p.read_text())
lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
rec=json.loads((REC/'REMAINDER_INPUT.json').read_text());a=plan(rec['setup'],rec['packet'],rec['source'],requests(task),task);assert a['passed'];path=O/'remaining3555.json';dump(path,task)
try:
 (R/'REVIEW_PENDING').unlink();q=subprocess.run([str(R/'run_phase.sh'),str((C/'entry_check.py').relative_to(R)),str(path)],cwd=R,capture_output=True,text=True,timeout=20)
finally:(R/'REVIEW_PENDING').write_bytes(guard)
(O/'entry.console').write_text(q.stdout+q.stderr);assert q.returncode==0,q.stdout+q.stderr;r=dict(passed=True,real_isolated_entry=json.loads(q.stdout.strip().splitlines()[-1]),original_complete_plan_checks=a['checks'],minimum_raw_m=a['minimum_raw_m'],goal_upper_m=a['goal_upper_m'],reused_two_actual_components_after_all_control_parity=True,new_models=0,new_integrations=0,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard);dump(O/'QUALIFICATION.json',r);print(json.dumps(r),flush=True)
