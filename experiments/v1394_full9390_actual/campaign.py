"""One inspected component pair under its own round and campaign cutoffs."""
import os
import importlib.util
import signal
import subprocess
import sys
import traceback
from component_context import *
sys.path.insert(0,str(R/'experiments/v1372_coherent_sampling_fault'))
from worker_monitor import terminate
spec=importlib.util.spec_from_file_location('phase_capture_environment_helpers',R/'experiments/v1372_coherent_sampling_fault/campaign.py')
environment_helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(environment_helpers)
native_environment=environment_helpers.native_environment;peer_environment=environment_helpers.peer_environment

_storage_cache=[0.,0]
def storage_bytes():
    if time.monotonic()-_storage_cache[0]>5:
        p=subprocess.run(['du','-sx','--block-size=1',str(R/'runs')],capture_output=True,text=True,check=True,timeout=90)
        _storage_cache[:]=[time.monotonic(),int(p.stdout.split()[0])]
    return _storage_cache[1]

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    window=read(O/'ROUND_WINDOW.json');guard=(O/'REVIEW_PENDING.before').read_bytes();tasks=read(C/'TASKS.json');summary=dict(passed=False,closed=False,results=[],unexecuted=[t['task_id'] for t in tasks],new_navigation=0)
    job=None;log=None
    def stop(*_):raise TimeoutError('DAY_CAPTURE_ROOT_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining(window)-5))
    try:
        for task in tasks:
            assert remaining(window)>1500 and storage_bytes()<10*1024**3-512*1024**2,'ROOT_TIME_OR_STORAGE_RESERVE'
            authorize(task,window);out=Path(task['output']);out.mkdir(parents=True,exist_ok=False);dump(out/'TASK.json',task)
            ledger=read(DAY/'LEDGER.json');local=read(O/'ROUND_LEDGER.json');assert local['task_starts']<2 and ledger['vehicle_task_starts']<256;local['task_starts']+=1;ledger['vehicle_task_starts']+=1;ledger.update(status='RUNNING_FIXED_ROUND',active_round=C.name,active_task=task['task_id']);dump(O/'ROUND_LEDGER.json',local);dump(DAY/'LEDGER.json',ledger)
            row=dict(task=task['task_id'],passed=False);summary['results'].append(row);summary['unexecuted'].remove(task['task_id']);dump(O/'PARTIAL_RESULTS.json',summary['results'])
            (R/'REVIEW_PENDING').unlink();log=(out/'native.console').open('x')
            job=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'native.py').relative_to(R)),str(out/'TASK.json')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            dump(O/'ACTIVE.json',dict(task=task['task_id'],phase='PREFIX_AND_TIMED_HANDOFF',owned_native_pid=job.pid))
            until=min(time.monotonic()+905,window['hard_stop_monotonic']-70)
            while job.poll() is None:
                assert time.monotonic()<until and storage_bytes()<10*1024**3-512*1024**2,'OUTER_TIME_OR_STORAGE_STOP';time.sleep(.3)
            log.close();log=None;(R/'REVIEW_PENDING').write_bytes(guard)
            row.update(returncode=job.returncode,native=read(out/'RESULT.json') if (out/'RESULT.json').exists() else None);job=None
            if row['native'] and row['native'].get('replay',{}).get('passed'):
                # Capture proofs are produced in the native runtime, not ROS.
                # Match that exact producer Python/NumPy for dictionary proofs.
                spec=importlib.util.spec_from_file_location('phase_capture_audit_isolation',R/'tools/isolate.py');isolation=importlib.util.module_from_spec(spec);spec.loader.exec_module(isolation)
                (R/'REVIEW_PENDING').unlink()
                p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'audit_entry.py').relative_to(R)),str(out/'TASK.json')],cwd=R,env=native_environment(),capture_output=True,text=True,timeout=min(240,max(1,remaining(window)-20)))
                (R/'REVIEW_PENDING').write_bytes(guard);(out/'audit.console').write_text(p.stdout+p.stderr);row['audit_returncode']=p.returncode
                if (out/'FINAL_INDEPENDENT_AUDIT.json').exists():row['audit']=read(out/'FINAL_INDEPENDENT_AUDIT.json')
            row['passed']=bool(row['returncode']==0 and row['native'] is not None and row['native']['passed'] and row.get('audit',{}).get('passed') and row.get('audit_returncode')==0)
            dump(O/'PARTIAL_RESULTS.json',summary['results'])
            if not row['passed']:summary['stop_reason']='FIRST_FUNCTIONAL_SAFETY_SOURCE_OR_EVIDENCE_FAILURE';break
        else:summary.update(passed=True,stop_reason='MAIN_AND_REPEAT_FULL9390_PASSED')
    except BaseException as exc:summary.update(error=repr(exc),traceback=traceback.format_exc(),stop_reason='OPERATION_DEADLINE_OR_STORAGE_EXCEPTION')
    finally:
        if job is not None:terminate(job)
        if log is not None:log.close()
        (R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        summary.update(closed=True,closed_unix=time.time(),source_unchanged=sources(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard)
        dump(O/'COMPLETION.json',summary);(O/'ACTIVE.json').unlink(missing_ok=True)
        functional={'endpoint_position','endpoint_heading','component_functional'}
        evidence_fault=bool(summary.get('error')) or any(not row.get('audit') or (row.get('native') or {}).get('error') or any(not v for k,v in row.get('audit',{}).get('checks',{}).items() if k not in functional) for row in summary['results'])
        ledger=read(DAY/'LEDGER.json');ledger.update(status='ROUND_CLOSED_REVIEW_REQUIRED',active_round=None,active_task=None,models_now_authorized=False,last_round_failure_requires_inspection=not summary['passed'])
        record=next(x for x in ledger['rounds'] if x['id']==C.name);record.update(closed=True,passed=summary['passed'],completion=str((O/'COMPLETION.json').relative_to(R)),completion_sha256=sha(O/'COMPLETION.json'),stop_reason=summary.get('stop_reason'),source_or_evidence_fault=evidence_fault)
        dump(DAY/'LEDGER.json',ledger)
        pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False);pointer['latest_v1394']=dict(closed=True,full9390_pair_passed=summary['passed'],full_dynamic_route_qualified=False,report='docs/FULL9390_ACTUAL_V1394_REPORT.md');dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'finalize.console').open('x') as f:closed=subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
    dump(O/'FINALIZER_EXIT.json',dict(returncode=closed.returncode,models=0));return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
