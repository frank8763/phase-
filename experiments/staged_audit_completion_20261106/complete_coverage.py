"""All persisted rejection witnesses, then all as-yet missing saved-only auditors."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/staged_audit_completion_20261106';pair=ROOT/'reference/paired';W=R/'experiments/v842_staged_long_navigation'
sys.path.insert(0,str(R/'experiments/staged_90_then12_20261106'));from evidence_rules import AUDITS,dump,read,sha
with(ROOT/'COMPLETE_COVERAGE_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),model_reads=0,integrations=0),f)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(R/'REVIEW_PENDING').read_bytes();rows=read(ROOT/'SAVED_RESULTS.json');assert len(rows)==10 and rows[-1]['exit']==1;rows=rows[:-1]
prepared={str(p.relative_to(R)):sha(p)for p in C.glob('*')if p.is_file()};dump(ROOT/'COMPLETE_COVERAGE_SOURCE_FREEZE.json',prepared);deadline=time.time()+7200;passed=False;child=None
def execute(script,args):
 global child
 assert script!='audit_run.py'and time.time()+603<deadline
 dump(ROOT/'COVERAGE_ACTIVE.json',dict(script=script,models=0,integrations=0,started_unix=time.time()))
 command=[str(R/'run_phase.sh'),str(C.relative_to(R)/'complete_audit_entry.py'),'--write-root',str(pair)]
 if script=='audit_reactive.py':command+=['--supplement-output']
 with(ROOT/(script+'.complete.console')).open('x')as stream:
  child=subprocess.Popen([*command,script,*map(str,args)],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:return child.wait(timeout=600)
  finally:
   if child.poll()is None:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   child=None
try:
 original=read(W/'CANDIDATE_FREEZE.json');assert all(sha(R/p)==h for p,h in original['files'].items());(R/'REVIEW_PENDING').unlink()
 expected=read(R/'runs/staged_90_then12_20261106/ZERO_MODEL_QUALIFICATION.json')['expected_audit_statuses']
 for script,filename,_ in AUDITS[9:]:
  output='REACTIVE_POLICY_AUDIT_COMPLETE_LOGS.json'if script=='audit_reactive.py'else filename
  assert not(pair/output).exists(),'EXISTING_OUTPUT_NO_OVERWRITE'
  started=time.time();code=execute(script,[pair]);row=dict(script=script,exit=code,elapsed_s=time.time()-started,new_model_reads=0,new_integrations=0,output=output,complete_log_coverage=script=='audit_reactive.py');rows.append(row);dump(ROOT/'COMPLETE_RESULTS.json',rows)
  assert code==0,script+'_FAILED_STOP';data=read(pair/output);assert data['status']==expected[script]and all(data.get('checks',{}).values())
 assert execute('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'])==0,'DISCOVERY_CHAIN_FAILED_STOP'
 chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json');assert chain['status']=='PASS'and all(chain['checks'].values())
 assert all(sha(R/p)==h for p,h in original['files'].items())and all(sha(R/x['path'])==x['sha256']for x in read(ROOT/'ORIGINAL_EVIDENCE_FREEZE.json'))
 assert all(sha(R/p)==h for p,h in prepared.items());passed=True
except BaseException as e:dump(ROOT/'COVERAGE_ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (R/'REVIEW_PENDING').write_bytes(guard);lock.close();dump(ROOT/'COVERAGE_ACTIVE.json',dict(completed=True,passed=passed));dump(ROOT/'COMPLETE_COVERAGE_COMPLETION.json',dict(passed=passed,audit_scopes_completed=len(rows),new_model_reads=0,new_integrations=0,previous_metadata_model_reads=1,original_reactive_audit_FAIL_preserved=True,closed_unix=time.time()));print(json.dumps(read(ROOT/'COMPLETE_COVERAGE_COMPLETION.json')),flush=True)
