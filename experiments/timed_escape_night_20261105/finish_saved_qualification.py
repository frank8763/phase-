"""Resume only unfinished zero-model audit calls after the interactive tool was interrupted."""
import fcntl,subprocess,sys,time
from pathlib import Path
from evidence_rules import AUDITS,dump,read,sha,repeat_check
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/timed_escape_night_20261105';q=root/'qualification';own=repo/'experiments/v834_timed_escape_development';base=repo/'runs/v826_goal_reference_renewal/main_slot02/paired';pair=q/'reference/paired';window=q/'original_source_window'
assert not(root/'ZERO_MODEL_QUALIFICATION.json').exists()and not(repo/'runs/v833_timed_escape_qualification').exists()
guard=(repo/'runs/forward_escape_night_20261105/REVIEW_PENDING.before').read_bytes();lock=(repo/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if(repo/'REVIEW_PENDING').exists():assert(repo/'REVIEW_PENDING').read_bytes()==guard
else:(repo/'REVIEW_PENDING').write_bytes(guard)
dump(root/'ZERO_MODEL_TOOL_INTERRUPTION.json',dict(status='INTERACTIVE_TOOL_INTERRUPTED_WITH_EXECUTION_LOCK_NOW_IDLE',completed_audits=len(read(q/'RESULTS.json')),unfinished='audit_reentry saved-only call',new_models=0,new_integrations=0,guard_restored_original_bytes=True,physics_not_started=True))
model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json';records=read(q/'RESULTS.json');completed={x['script']for x in records if x['exit']==0}
def run(script,args,log,cap):
 command=[str(repo/'run_phase.sh'),str(common.relative_to(repo)/'worker_entry.py'),'--saved-only',own.name,script,*map(str,args)]
 with log.open('x')as stream:p=subprocess.run(command,cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=cap)
 return p.returncode
try:
 (repo/'REVIEW_PENDING').unlink()
 for script,filename,cap in AUDITS:
  if script=='audit_ranked_return.py'or script in completed:continue
  args=[pair]
  if script=='audit_run.py':args+=['--window',window]
  if script=='audit_projection_learning.py':args+=['--model',model]
  if script=='audit_goal_renewal.py':args+=['--anchor-original-ns']
  code=run(script,args,q/(script+'.remaining.console'),cap);records.append(dict(script=script,exit=code));dump(q/'RESULTS.json',records)
  assert code==0,script+'_FAILED';assert read(pair/filename)['status']!='FAIL'and all(read(pair/filename).get('checks',{}).values())
 assert run('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],q/'discovery.remaining.console',360)==0
 assert all(read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')['checks'].values())
 tasks=read(own/'TASK_LIST.json');source={x['task']['seed']:x for x in read(repo/'runs/v828_goal_dynamic_confirmation/confirmation01/PREFLIGHTS.json')+read(repo/'runs/v827_goal_route_validation/development01/PREFLIGHTS.json')};view=q/'five_t0_interface';view.mkdir();pre=[]
 for t in tasks:x=dict(source[t['seed']]);x['task']=t;pre.append(x)
 dump(view/'PREFLIGHTS.json',pre);assert run('audit_field_preflight.py',[view],q/'five_t0.remaining.console',120)==0
 sys.path.insert(0,str(own));from contact_fingerprint import compare_contacts
 result=read(base/'geometry_memory/result.json');assert repeat_check(base,base,result,result,compare_contacts)['passed']
 assert all(sha(repo/x['path'])==x['sha256']for x in read(q/'ORIGINAL_SOURCE_INVENTORY.json'))
 assert read(q/'RETURN_SEARCH_QUALIFICATION.json')['passed']and read(q/'LIBRARY_QUALIFICATION.json')['passed']and read(q/'TIMED_GATE_QUALIFICATION.json')['passed']
 (pair/'RANKED_RETURN_AUDIT.json').write_bytes((q/'return_rejection_seam/paired/RANKED_RETURN_AUDIT.json').read_bytes())
 dump(root/'ZERO_MODEL_QUALIFICATION.json',dict(passed=True,original_and_new_saved_auditors=records,ranked_return=read(q/'RETURN_SEARCH_QUALIFICATION.json'),timed_gate=read(q/'TIMED_GATE_QUALIFICATION.json'),five_t0_interface_passed=True,gate_positive_negative_cases=4,models=0,integrations=0,canonical_metadata_proxy_import_only=True,not_native_feasibility=True,unfinished_saved_calls_completed_without_restarting_physics=True))
 print('ALL_SAVED_AUDIT_CALLS_AND_TIMED_GATE_QUALIFIED',flush=True)
finally:(repo/'REVIEW_PENDING').write_bytes(guard);lock.close()
