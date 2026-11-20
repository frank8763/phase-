"""One offline component pair under the nonrenewable day cutoff."""
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

def storage_bytes():
    seen=set();size=0
    roots=[R/'runs'/name for name in ['v1374_day_handoff_validation','v1375_actual_capture_component','v1376_prepared_capture_component','v1377_timed_handoff_witness','v1378_steering_response_32210','v1379_timed_response_preparation','v1380_timed_handoff_component']]
    roots += [R/'runs/v858_nav2_verified'/('v'+str(v)) for v in [1374,1375,1376,1378,1380]]
    roots += [C,R/'experiments/v1379_timed_response_preparation']
    for root in roots:
        if not root.exists():continue
        for p in root.rglob('*'):
            if p.is_symlink() or not p.is_file():continue
            s=p.stat();key=(s.st_dev,s.st_ino)
            if key not in seen:seen.add(key);size+=s.st_size
    return size

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    window=read(O/'ROUND_WINDOW.json');guard=(O/'REVIEW_PENDING.before').read_bytes();tasks=read(C/'TASKS.json');summary=dict(passed=False,closed=False,results=[],unexecuted=[t['task_id'] for t in tasks],new_navigation=0)
    job=None;log=None
    def stop(*_):raise TimeoutError('DAY_CAPTURE_ROOT_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining(window)-5))
    try:
        for task in tasks:
            assert remaining(window)>1200 and storage_bytes()<2*1024**3-180*1024**2,'ROOT_TIME_OR_STORAGE_RESERVE'
            authorize(task,window);out=Path(task['output']);out.mkdir(parents=True,exist_ok=False);dump(out/'TASK.json',task)
            ledger=read(DAY/'DAY_LEDGER.json');assert ledger['supplemental_components_started']<2;ledger['supplemental_components_started']+=1;ledger.update(status='RUNNING_FROZEN_CAPTURE',active_batch=C.name,active_task=task['task_id']);dump(DAY/'DAY_LEDGER.json',ledger)
            row=dict(task=task['task_id'],passed=False);summary['results'].append(row);summary['unexecuted'].remove(task['task_id']);dump(O/'PARTIAL_RESULTS.json',summary['results'])
            (R/'REVIEW_PENDING').unlink();log=(out/'native.console').open('x')
            job=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'native.py').relative_to(R)),str(out/'TASK.json')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            dump(O/'ACTIVE.json',dict(task=task['task_id'],phase='PREFIX_AND_MEASURED_CAPTURE',owned_native_pid=job.pid))
            until=min(time.monotonic()+905,window['hard_stop_monotonic']-70)
            while job.poll() is None:
                assert time.monotonic()<until and storage_bytes()<2*1024**3-180*1024**2,'OUTER_TIME_OR_STORAGE_STOP';time.sleep(.3)
            log.close();log=None;(R/'REVIEW_PENDING').write_bytes(guard)
            row.update(returncode=job.returncode,native=read(out/'RESULT.json') if (out/'RESULT.json').exists() else None);job=None
            if row['native'] and row['native'].get('replay',{}).get('passed'):
                # Capture proofs are produced in the native runtime, not ROS.
                # Match that exact producer Python/NumPy for dictionary proofs.
                spec=importlib.util.spec_from_file_location('phase_capture_audit_isolation',R/'tools/isolate.py');isolation=importlib.util.module_from_spec(spec);spec.loader.exec_module(isolation)
                (R/'REVIEW_PENDING').unlink()
                p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'audit_entry.py').relative_to(R)),str(out/'TASK.json')],cwd=R,env=native_environment(),capture_output=True,text=True,timeout=min(120,max(1,remaining(window)-20)))
                (R/'REVIEW_PENDING').write_bytes(guard);(out/'audit.console').write_text(p.stdout+p.stderr);row['audit_returncode']=p.returncode
                if (out/'FINAL_INDEPENDENT_AUDIT.json').exists():row['audit']=read(out/'FINAL_INDEPENDENT_AUDIT.json')
            row['passed']=bool(row['returncode']==0 and row['native'] is not None and row['native']['passed'] and row.get('audit',{}).get('passed') and row.get('audit_returncode')==0)
            dump(O/'PARTIAL_RESULTS.json',summary['results'])
            if not row['passed']:summary['stop_reason']='FIRST_FUNCTIONAL_SAFETY_SOURCE_OR_EVIDENCE_FAILURE';break
        else:summary.update(passed=True,stop_reason='MAIN_AND_REPEAT_TIMED_HANDOFF_PASSED')
    except BaseException as exc:summary.update(error=repr(exc),traceback=traceback.format_exc(),stop_reason='OPERATION_DEADLINE_OR_STORAGE_EXCEPTION')
    finally:
        if job is not None:terminate(job)
        if log is not None:log.close()
        (R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        summary.update(closed=True,closed_unix=time.time(),source_unchanged=sources(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard)
        dump(O/'COMPLETION.json',summary);(O/'ACTIVE.json').unlink(missing_ok=True)
        functional={'endpoint_position','endpoint_heading','component_functional'}
        evidence_fault=bool(summary.get('error')) or any(not row.get('audit') or (row.get('native') or {}).get('error') or any(not v for k,v in row.get('audit',{}).get('checks',{}).items() if k not in functional) for row in summary['results'])
        ledger=read(DAY/'DAY_LEDGER.json');ledger.update(status='SUPPLEMENTAL_TIMED_HANDOFF_CLOSED',active_batch=None,active_task=None,latest_32210_timed_handoff_pair_passed=summary['passed'],full9390_handoff_qualified=False,full32210_handoff_qualified=False,physical_entry_ready=False,models_now_authorized=False,safety_or_evidence_fault_stops_today_physics=evidence_fault)
        batches=[read(R/'runs/v1375_actual_capture_component/COMPLETION.json'),read(R/'runs/v1376_prepared_capture_component/COMPLETION.json'),read(R/'runs/v1378_steering_response_32210/COMPLETION.json'),summary]
        native_results=[row.get('native') for batch in batches for row in batch['results']]
        for field in ['actual_total_native','historical_prefix_replay_native','new_component_native','own_replay_native','canonical_vehicle_initializations']:
            values=[n.get(field) if n is not None else None for n in native_results];ledger[field]=sum(values) if all(v is not None for v in values) else None
        ledger.update(counts_scope='all closed day batches, historical/native/replay separated',internal_factory_model_constructions=None,supplemental_current_jobs=0)
        dump(DAY/'DAY_LEDGER.json',ledger)
        pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False);pointer['latest_v1380']=dict(closed=True,timed_handoff_pair_passed=summary['passed'],full_dynamic_route_qualified=False,report='docs/TIMED_HANDOFF_V1380_REPORT.md');dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'finalize.console').open('x') as f:closed=subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=300)
    dump(O/'FINALIZER_EXIT.json',dict(returncode=closed.returncode,models=0));return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
