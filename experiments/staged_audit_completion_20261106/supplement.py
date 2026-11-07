"""Exactly one independent pass over saved pilot evidence; no navigation/replay."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v842_staged_long_navigation';ROOT=R/'runs/staged_audit_completion_20261106';pair=ROOT/'reference/paired'
sys.path.insert(0,str(R/'experiments/staged_90_then12_20261106'));from evidence_rules import AUDITS,dump,read,sha
claim=ROOT/'AUDIT_CLAIM.json'
with claim.open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),attempts=1),f)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
guard=(R/'REVIEW_PENDING').read_bytes();(ROOT/'REVIEW_PENDING.before').write_bytes(guard);a=read(ROOT/'AUTHORIZATION.json');rows=[];child=None;passed=False
def unchanged():
 assert all(sha(R/p)==h for p,h in read(ROOT/'PREPARED.json')['files'].items())
 assert all(sha(R/x['path'])==x['sha256']for x in read(ROOT/'ORIGINAL_EVIDENCE_FREEZE.json'))
def execute(script,args,cap):
 global child
 command=[str(R/'run_phase.sh'),str(C.relative_to(R)/'audit_entry.py'),'--write-root',str(pair)]
 if script=='audit_run.py':
  assert time.time()+cap+3<a['original_model_deadline_unix'];command+=['--model-deadline',str(a['original_model_deadline_unix'])]
 command+=[script,*map(str,args)];dump(ROOT/'ACTIVE.json',dict(script=script,cap_s=cap,started_unix=time.time(),models=script=='audit_run.py'))
 with(ROOT/(script+'.console')).open('x')as stream:
  child=subprocess.Popen(command,cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:return child.wait(timeout=cap)
  finally:
   if child.poll()is None:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   child=None
try:
 unchanged();assert read(ROOT/'QUALIFICATION.json')['passed'];(R/'REVIEW_PENDING').unlink()
 expected=read(R/'runs/staged_90_then12_20261106/ZERO_MODEL_QUALIFICATION.json')['expected_audit_statuses']
 for script,filename,oldcap in AUDITS:
  args=[pair]
  if script=='audit_run.py':args+=['--window',R/'runs/v842_staged_long_navigation/pilot90']
  if script=='audit_projection_learning.py':args+=['--model',R/'runs/v690_visible_eight_meter/training_8m/proposer.json']
  cap=600 if script=='audit_run.py'else oldcap
  started=time.time();code=execute(script,args,cap);row=dict(script=script,exit=code,elapsed_s=time.time()-started);rows.append(row);dump(ROOT/'RESULTS.json',rows)
  assert code==0,script+'_FAILED_STOP'
  result=read(pair/filename);assert result['status']==expected[script]and all(result.get('checks',{}).values()),script+'_GATES_FAILED_STOP'
 code=execute('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],240);assert code==0,'DISCOVERY_CHAIN_FAILED_STOP'
 chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json');assert chain['status']=='PASS' and all(chain['checks'].values())
 replay=read(pair/'NATIVE_REPLAY_AUDIT.json');assert replay['maximum_full_native_state_ctrl_error']<=1e-8 and replay['replay_integration_steps']==5800
 unchanged();passed=True
except BaseException as e:dump(ROOT/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (R/'REVIEW_PENDING').write_bytes(guard);lock.close()
 dump(ROOT/'ACTIVE.json',dict(completed=True,passed=passed));dump(ROOT/'AUDIT_COMPLETION.json',dict(passed=passed,auditors_completed=len(rows),new_navigation=0,new_integrations=0,metadata_model_reads=1 if rows else None,original_batch_still_not_passed=True,closed_unix=time.time()))
 print(json.dumps(read(ROOT/'AUDIT_COMPLETION.json')),flush=True)
