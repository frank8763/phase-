"""One frozen queue, real wall-paced physics, dependency gates and bounded shutdown."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v858_nav2_verified';END=1794052800.
sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'))
from ros_environment import command,environment
from audit_navigation import audit
def dump(p,v):
 p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def verify():
 for path,h in json.loads((C/'NAVIGATION_FREEZE.json').read_text())['files'].items():
  assert hashlib.sha256((R/path).read_bytes()).hexdigest()==h,'FROZEN_SOURCE_CHANGED '+path
def stop(p):
 if p and p.poll()is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=4)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def storage():
 return sum(p.stat().st_size for base in [OUT,R/'runs/v856_nav2_foundation']for p in base.rglob('*')if p.is_file())
def task_path(t):return OUT/(t['id']+'.task.json')
def run_task(t):
 verify();assert time.time()<END-300,'INSUFFICIENT_NEXT_TASK_TIME';assert storage()<2*1024**3,'STORAGE_CAP';assert json.loads(task_path(t).read_text())==t
 out=Path(t['output']);assert not out.exists(),'TASK_ALREADY_ATTEMPTED';out.mkdir();dump(OUT/'ACTIVE.json',dict(task=t,started_unix=time.time()));jobs=[];files=[];until=min(END,time.time()+240)
 try:
  rf=(out/'ros.console').open('w');files.append(rf);ros=subprocess.Popen(command(['/usr/bin/python3.12',str(C/'native_ros.py'),str(task_path(t))]),cwd=R,env=environment(),stdout=rf,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(ros)
  nf=(out/'native.console').open('w');files.append(nf);native=subprocess.Popen([str(R/'run_phase.sh'),str((C/'native_worker.py').relative_to(R)),str(task_path(t))],cwd=R,env=dict(os.environ,PHASE_MODEL_ABSOLUTE_DEADLINE=str(until-3)),stdout=nf,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(native)
  native.wait(timeout=max(.01,until-time.time()));ros.wait(timeout=max(.01,until-time.time()))
 finally:
  for p in reversed(jobs):stop(p)
  for f in files:f.close()
 verify();assert(out/'RESULT.json').exists(),'NATIVE_RESULT_MISSING_COUNTS_UNKNOWN';result=json.loads((out/'RESULT.json').read_text());assert result.get('status')=='NATIVE_COMPLETE','NATIVE_EXCEPTION '+str(result.get('error'));saved=audit(t)
 return dict(id=t['id'],stage=t['stage'],case_id=t['case_id'],slot=t.get('slot'),direction=t.get('initial_axis_direction'),result=result,audit=saved,passed=saved['passed'])
def confirm_t0(tasks):
 rows=[]
 for t in tasks:
  verify();assert time.time()<END-300
  with(OUT/'preflights'/(t['id']+'.console')).open('w')as f:p=subprocess.run([str(R/'run_phase.sh'),str((C/'preflight.py').relative_to(R)),str(task_path(t))],cwd=R,env=dict(os.environ,PHASE_MODEL_ABSOLUTE_DEADLINE=str(min(END-5,time.time()+88))),stdout=f,stderr=subprocess.STDOUT,timeout=90)
  r=json.loads((OUT/'preflights'/(t['id']+'.RESULT.json')).read_text());rows.append(dict(id=t['id'],result=r,returncode=p.returncode));dump(OUT/'CONFIRMATION_PREFLIGHTS.json',dict(passed=len(rows)==24 and all(r['result']['passed']for r in rows),rows=rows,native_integrations=0));assert p.returncode==0 and r['passed'],'CONFIRMATION_T0_FAILED'
def main():
 verify();assert json.loads((OUT/'PREFLIGHT_RESULTS.json').read_text())['passed'];assert json.loads((OUT/'COMPONENT_INDEPENDENT_AUDIT.json').read_text())['passed']
 lock=(OUT/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(R/'REVIEW_PENDING').read_bytes();tasks=json.loads((C/'TASK_LIST.json').read_text());rows=[];status='ENTRY';confirmation_started=False;errors=None
 with(OUT/'NAVIGATION_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),root_deadline_unix=END),f)
 window=dict(started_unix=time.time(),absolute_deadline_unix=END,closed=False);dump(OUT/'ROUND_WINDOW.json',window)
 try:
  (R/'REVIEW_PENDING').unlink();status='DEVELOPMENT_RUNNING'
  for t in tasks[:9]:
   row=run_task(t);rows.append(row);dump(OUT/'RESULTS.json',dict(rows=rows));assert row['audit']['evidence_passed'],'DEVELOPMENT_SAFETY_OR_EVIDENCE_FAILED';assert row['passed'],'DEVELOPMENT_FUNCTIONAL_FAILED '+t['id']
  dump(OUT/'DEVELOPMENT_GATE.json',dict(passed=True,navigation_count=9,independent_saved_audits_passed=True))
  if END-time.time()<5700:status='DEVELOPMENT_PASSED_CONFIRMATION_NOT_STARTED_INSUFFICIENT_95MIN';return
  confirmation=[t for t in tasks if t['stage']=='confirmation'];confirmation_started=True;confirm_t0(confirmation);failures=0
  for t in confirmation:
   row=run_task(t);rows.append(row);dump(OUT/'RESULTS.json',dict(rows=rows));assert row['audit']['evidence_passed'],'CONFIRMATION_SAFETY_OR_EVIDENCE_FAILED';failures+=int(not row['passed']);assert failures<2,'SECOND_CONFIRMATION_FUNCTIONAL_FAILURE'
  cr=[r for r in rows if r['stage']=='confirmation'];good=[r for r in cr if r['passed']];route={k:sum(r['case_id']==k for r in good)for k in ['WEST_EAST','NORTH_SOUTH','EAST_WEST']};direction={k:sum(r['direction']==k for r in good)for k in ['POSITIVE','NEGATIVE']};gate=len(cr)==24 and len(good)>=23 and min(route.values())>=7 and min(direction.values())>=11
  dump(OUT/'CONFIRMATION_GATE.json',dict(passed=gate,executed=24,successful=len(good),route=route,direction=direction));assert gate,'CONFIRMATION_DISTRIBUTION_GATE_FAILED'
  for t in tasks[-3:]:
   assert next(r for r in cr if r['slot']==t['slot'])['passed'],'FIXED_REPEAT_BASELINE_FAILED'
   row=run_task(t);rows.append(row);dump(OUT/'RESULTS.json',dict(rows=rows));assert row['passed'],'FIXED_REPEAT_FAILED'
  status='NAV2_FINITE_COURSE_24_ACCEPTANCE_PASSED'
 except BaseException as e:
  status='STOPPED_NOT_PASSED';errors=dict(error=repr(e),traceback=traceback.format_exc());dump(OUT/'ERROR.json',errors)
 finally:
  (R/'REVIEW_PENDING').write_bytes(guard);window.update(closed=True,status=status,closed_unix=time.time(),guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard);dump(OUT/'ROUND_WINDOW.json',window)
  complete=dict(status=status,closed=True,passed=status=='NAV2_FINITE_COURSE_24_ACCEPTANCE_PASSED',confirmation_started=confirmation_started,executed_ids=[r['id']for r in rows],unexecuted_ids=[t['id']for t in tasks if t['id']not in {r['id']for r in rows}],actual_native=sum(r['audit']['native_count']for r in rows),replay_native=sum(r['audit']['replay_native']for r in rows),private_native=0,interrupted_task_count_may_be_unknown=errors is not None and (not rows or rows[-1]['id']!=json.loads((OUT/'ACTIVE.json').read_text())['task']['id']),guard_restored=window['guard_restored']);dump(OUT/'COMPLETION.json',complete);print(json.dumps(complete),flush=True)
if __name__=='__main__':main()
