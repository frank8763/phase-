"""One bounded daytime component; no automatic route or confirmation launch."""
import sys,os,json,time,signal,subprocess,fcntl,hashlib,traceback,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1091_certified_exit'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def used():
    seen=set();total=0
    for root,dirs,files in os.walk(R/'runs',followlinks=False):
        dirs[:]=[d for d in dirs if not Path(root,d).is_symlink()]
        for name in files:
            p=Path(root,name)
            if p.is_symlink():continue
            st=p.stat();key=(st.st_dev,st.st_ino)
            if key not in seen:seen.add(key);total+=st.st_size
    return total
def main():
    guard=(R/'REVIEW_PENDING').read_bytes()
    assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((O/'QUALIFICATION.json').read_text())['passed']
    freeze=json.loads((C/'SOURCE_FREEZE.json').read_text())['files']
    assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in freeze.items())
    assert used()+200*1024**2<=2*1024**3,'DEFAULT_2GIB_CAPACITY_STOP'
    own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with (R/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not(O/'ROUND_WINDOW.json').exists()
    now=time.time();mono=time.monotonic();end=now+5400
    window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=end,
                hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),old_windows_unchanged=True)
    dump(O/'ROUND_WINDOW.json',window);(O/'GUARD.bin').write_bytes(guard)
    dump(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=end,allowed_task_ids=['exit_saved_we']))
    dump(O/'AUTHORIZATION.json',dict(models_authorized=True,user_instruction='白天一步一步推进，将三路线跑出来再说',bounded_intermediate_step='one exact saved failure exit component',duration_s=5400,automatic_routes_or24=False,temporary_limit_bytes=2*1024**3))
    current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='RUNNING_COMPONENT',active_run=str(O.relative_to(R)),active_window=window,active_entrypoint=str(C.relative_to(R)/'worker.py'),next_physical_authorized=True,automatic_additional_simulation=False);dump(R/'CURRENT_EXPERIMENT.json',current)
    child=None;error=None;result={};audit={}
    def halt(*_):raise TimeoutError('COMPONENT_DEADLINE_OR_STOP')
    def run(command,filename,timeout):
        nonlocal child
        with (O/filename).open('x')as log:
            child=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            dump(O/'ACTIVE.json',dict(pid=child.pid,starttime=Path('/proc/'+str(child.pid)+'/stat').read_text().split()[21],stage=filename))
            code=child.wait(timeout=min(timeout,end-time.time()-10));child=None;return code
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,5400)
    try:
        (R/'REVIEW_PENDING').unlink()
        try:code=run([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(O)],'worker.console',905)
        finally:(R/'REVIEW_PENDING').write_bytes(guard)
        task=json.loads((O/'TASK.json').read_text());out=Path(task['output'])
        result=json.loads((out/'RESULT.json').read_text())if(out/'RESULT.json').exists()else dict(passed=False,counts_unknown=True)
        dump(O/'RESULTS.json',result);assert code==0 and result['passed'],'FIRST_COMPONENT_FAILURE'
        code=run([sys.executable,'-B',str(C/'audit.py'),str(O)],'audit.console',180)
        audit=json.loads((out/'FINAL_INDEPENDENT_AUDIT.json').read_text())if(out/'FINAL_INDEPENDENT_AUDIT.json').exists()else {}
        assert code==0 and audit.get('passed'),'FIRST_INDEPENDENT_AUDIT_FAILURE'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
            except BaseException:
                try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
                except ProcessLookupError:pass
        (R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0)
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True));dump(O/'AUTHORIZATION_CLOSED.json',dict(closed=True,absolute_deadline_unix=end,no_extension=True))
    unchanged=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in freeze.items())
    keys=['vehicle_initializations','historical_replay_native','new_actual_native','own_replay_native','replay_state_initializations','private_mujoco_native','training_updates','analytical_prediction_native']
    summary=dict(closed=True,passed=bool(result.get('passed')and audit.get('passed')and unchanged and error is None),version='v1091',scope='EXIT_COMPONENT_ONLY',navigation_passed=False,three_route_passed=False,new24_executed=0,counts={k:result.get(k)for k in keys},error=error,source_unchanged=unchanged,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,models_not_restarted=True)
    dump(O/'COMPLETION.json',summary)
    if error:dump(O/'ERROR.json',error)
    report=R/'docs/RPCCR_CERTIFIED_EXIT_V1091_REPORT.md';report.write_text('# V1091 saved rejection exit component\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n\nThis is not full-route success. Original V1090 moving exit remains failed. No route/24 launched automatically.\n')
    current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_report=str(report.relative_to(R)),latest_completed=summary);dump(R/'CURRENT_EXPERIMENT.json',current)
    with (R/'RESEARCH_STATUS.md').open('a')as file:file.write('\n- V1091日间退出组件闭批：passed='+str(summary['passed'])+'；分账='+json.dumps(summary['counts'])+'；不等于WE整路/三路线/24通过，旧V1090失败保持。见docs/RPCCR_CERTIFIED_EXIT_V1091_REPORT.md。\n')
    # Zero-model bounded archive. Existing archives never overwritten.
    task=json.loads((O/'TASK.json').read_text());out=Path(task['output'])
    spec=importlib.util.spec_from_file_location('exit_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
    files=list(arc.walk(out))+[p for p in C.iterdir()if p.is_file()]+[p for p in O.iterdir()if p.is_file()and p.name not in ['driver.console']]+[report]
    record,inventory=arc.package(R,files,O/'cloud','v1091-exit',budget_check=lambda:used()+1024**2<=2*1024**3)
    dump(O/'ARCHIVE_INDEX.json',dict(archive=record,inventory=inventory))
    dump(O/'FINALIZED.json',dict(passed=summary['passed'],independent_audit_passed=bool(audit.get('passed')),all_source_and_decompressed_sha_verified=True,part_reassembly_sha_verified=True,models=0,integrations=0,remote_delivery_pending=True))
    print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
