"""One short independently authorized physical test, bounded and offline."""
from common_short import *
import subprocess,signal,fcntl,traceback

def main():
 assert not(O/'DRIVER_STARTED.json').exists()and source_ok()
 guard=(O/'GUARD.bin').read_bytes();assert sha(R/'REVIEW_PENDING')==GUARD_SHA
 driver=(O/'driver.lock').open('a+');fcntl.flock(driver,fcntl.LOCK_EX|fcntl.LOCK_NB)
 dump(O/'DRIVER_STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21]))
 child=None;error=None;result=None;audit=None;code=None;reason='SHORT_TEST_NOT_COMPLETED'
 def stop():
  nonlocal child
  if child and child.poll()is None:
   try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
   except BaseException:
    try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
    except ProcessLookupError:pass
  child=None
 def halt(*_):raise TimeoutError('TEN_MINUTE_ROOT_DEADLINE')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining()-3))
 task=json.loads((C/'TASK.json').read_text());out=Path(task['output'])
 try:
  assert all(json.loads((O/name).read_text())['passed']for name in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json'])
  assert source_ok()and remaining()>520
  lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
  assert (R/'REVIEW_PENDING').read_bytes()==guard
  (R/'REVIEW_PENDING').unlink()
  try:
   with(O/'worker.console').open('x')as log:
    child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R))],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    dump(O/'ACTIVE.json',dict(stage='short_physical_component',pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21]));code=child.wait(timeout=min(450,remaining()-75))
  finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
  path=out/'RESULT.json';result=json.loads(path.read_text())if path.exists()else None
  if code!=0 or not result or not result['passed']:reason='FIRST_PHYSICAL_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE';return
  assert remaining()>65
  with(O/'audit.console').open('x')as log:
   child=subprocess.Popen([sys.executable,'-B',str(C/'audit.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);acode=child.wait(timeout=min(65,remaining()-10))
  stop();path=out/'FINAL_INDEPENDENT_AUDIT.json';audit=json.loads(path.read_text())if path.exists()else None
  reason='SHORT_COMPONENT_PASSED'if acode==0 and audit and audit['passed']else'INDEPENDENT_AUDIT_FAILED'
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc());reason='EXCEPTION_OR_DEADLINE';dump(O/'ERROR.json',error)
 finally:
  stop();(R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0)
  if result is None and (out/'RESULT.json').exists():result=json.loads((out/'RESULT.json').read_text())
  summary=dict(closed=True,passed=bool(reason=='SHORT_COMPONENT_PASSED'),stop_reason=reason,error=error,worker_returncode=code,result=result,independent_audit=audit,models=None if result is None else result.get('models'),actual_native=None if result is None else result.get('new_actual_native'),historical_native=None if result is None else result.get('historical_reconstruction_native'),new_component_native=None if result is None else result.get('new_component_native'),own_replay_native=None if result is None else result.get('own_replay_native'),no_route_or_confirmation=True,new24_executed=False,new24_denominator=None,old_window_not_extended=True,guard_original=sha(R/'REVIEW_PENDING')==GUARD_SHA,source_unchanged=source_ok(),closed_unix=time.time(),remote_delivery_pending=True)
  dump(O/'COMPLETION.json',summary);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True))
  report=R/'docs/RPCCR_SHORT_REFRESH_V1147_REPORT.md';report.write_text('# V1147短时真实证书交接组件\n\n'+encode(summary)+'\n本次只验证真实8步交接与完整2200停车，不是原目标/三路线/24项通过。历史重建、实际新组件与自身控制重放独立计数；旧失败和旧窗口不改。未知账目保持null。源冻结后不修补、不重跑，训练/私有MuJoCo/实体机0。\n')
  cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,active_zero_model_diagnostic=None,next_physical_authorized=False,latest_report=str(report.relative_to(R)),latest_short_physical_result=summary);dump(R/'CURRENT_EXPERIMENT.json',cur)
  with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V1147用户要求短时间新测试，独立600s；'+reason+'；实际/历史/新组件/自身重放='+str([summary[k]for k in ['actual_native','historical_native','new_component_native','own_replay_native']])+'，无整路/三路线/24自动任务，旧21:00不延长，guard恢复。docs/RPCCR_SHORT_REFRESH_V1147_REPORT.md。\n')
  files=[]
  for root in [C,O,out]:
   if root.exists():
    for p in root.rglob('*'):
     if p.is_file()and not p.is_symlink()and p.name not in ['campaign.console','LOCAL_MANIFEST.json']:files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
  files.append(dict(path=str(report.relative_to(R)),bytes=report.stat().st_size,sha256=sha(report)))
  assert sum(p['bytes']for p in files)<2*1024**3,'TEMPORARY_LIMIT'
  dump(O/'LOCAL_MANIFEST.json',dict(files=files,readback_verified=all(sha(R/p['path'])==p['sha256']for p in files),remote_verified=False,raw_retained=True));print(encode(summary),flush=True)

if __name__=='__main__':main()
