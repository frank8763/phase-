"""Reuse frozen regressions, verify three real isolated imports without models."""
import sys,subprocess,ast,fcntl
from common import *
paths();from resource_policy import apply
apply();from science import *
guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==3;rows=[]
for p in C.glob('*.py'):ast.parse(p.read_text())
for name in ['QUALIFICATION.json','COMPLETE_GOAL_QUALIFICATION.json','NEXT_TRANSITION_PREFLIGHT.json','REMAINDER_QUALIFICATION.json']:assert json.loads((REC/name).read_text())['passed']
for p,h in json.loads((R/'experiments/v1079_dual_steering_qualification/SOURCE_FREEZE.json').read_text())['files'].items():assert sha(R/p)==h,p
setup=json.loads((ARCH/'physics/SETUP.json').read_text());packet=json.loads((R/'runs/v1067_causal_replan_brake_reserve_preparation/NORTH_SOUTH_T0_METADATA.json').read_text())['packet'];inp=json.loads((REC/'REMAINDER_INPUT.json').read_text());numerical=[]
for t in tasks:
 a=plan(setup,packet if t['kind']=='turn_return'else inp['packet'],None if t['kind']=='turn_return'else inp['source'],requests(t),t);assert a['passed'],a['checks'];numerical.append(dict(task_id=t['task_id'],checks=a['checks'],minimum_raw_m=a['minimum_raw_m']))
# Conditional actual stage cannot be admitted before the real two-test gate.
try:contracts(tasks[-1]);raise RuntimeError('EARLY_REMAINDER_ADMITTED')
except FileNotFoundError:pass
try:
 for task in tasks:
  path=O/(task['task_id']+'.json');dump(path,task);(R/'REVIEW_PENDING').unlink()
  try:q=subprocess.run([str(R/'run_phase.sh'),str((C/'entry_check.py').relative_to(R)),str(path)],cwd=R,capture_output=True,text=True,timeout=20)
  finally:(R/'REVIEW_PENDING').write_bytes(guard)
  (O/(task['task_id']+'.entry.console')).write_text(q.stdout+q.stderr);assert q.returncode==0,q.stdout+q.stderr;rows.append(json.loads(q.stdout.strip().splitlines()[-1]))
finally:(R/'REVIEW_PENDING').write_bytes(guard)
r=dict(passed=True,entries=rows,numerical=numerical,early_conditional_gate_rejected=True,models=0,integrations=0,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard);dump(O/'QUALIFICATION.json',r);print(json.dumps(r),flush=True)
