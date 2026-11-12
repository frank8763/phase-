"""Reuse unchanged numerical qualification; test actual sandbox task entry."""
import sys,subprocess,ast,fcntl
from common import *
paths();from resource_policy import apply
apply();guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';old=json.loads((R/'records/nav2_v1076_20261112/NEXT_RESPONSE_NS_PREFLIGHT.json').read_text());assert old['passed'];tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==5 and all(t['target']==x['target']and x['passed']for t,x in zip(tasks,old['cases']));lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);rows=[]
for p in C.glob('*.py'):ast.parse(p.read_text())
try:
 for task in tasks:
  path=O/(task['task_id']+'.json');dump(path,task);(R/'REVIEW_PENDING').unlink()
  try:q=subprocess.run([str(R/'run_phase.sh'),'experiments/v1077_speed125_response/entry_check.py',str(path)],cwd=R,capture_output=True,text=True,timeout=20)
  finally:(R/'REVIEW_PENDING').write_bytes(guard)
  (O/(task['task_id']+'.entry.console')).write_text(q.stdout+q.stderr);assert q.returncode==0,q.stderr;rows.append(json.loads(q.stdout.strip().splitlines()[-1]))
finally:(R/'REVIEW_PENDING').write_bytes(guard)
result=dict(passed=True,cases=5,all_actual_sandbox_entries=rows,reused_prediction_preflight_sha=sha(R/'records/nav2_v1076_20261112/NEXT_RESPONSE_NS_PREFLIGHT.json'),source_asts=True,models=0,integrations=0,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard);dump(O/'QUALIFICATION.json',result);print(json.dumps(result),flush=True)
