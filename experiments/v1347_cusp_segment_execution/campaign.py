"""Offline frozen sequential branch relay. Single physical owner, bounded root."""
import importlib.util
import os
import signal
import subprocess
import sys
import time
import traceback
from component_context import *
from worker_monitor import monitor,terminate
from relay_policy import classify,eligible


def native_environment():
    env=dict(os.environ);lib=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
    env['LD_LIBRARY_PATH']=str(lib)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    env.pop('LD_PRELOAD',None)
    env.update(CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    return env


def ros_environment(out,branch):
    spec=importlib.util.spec_from_file_location('phase_ros_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);env=module.environment()
    installs=[R/'runs/v1340_overnight_preparation/install',R/'runs/v931_deadband_consistent_mppi/install']
    env['AMENT_PREFIX_PATH']=':'.join(map(str,installs))+':'+env['AMENT_PREFIX_PATH']
    env['LD_LIBRARY_PATH']=':'.join(str(p/'lib') for p in installs)+':'+env['LD_LIBRARY_PATH']
    env.update(ROS_DOMAIN_ID='225',ROS_LOG_DIR=str(out/'ros_logs'),CUDA_VISIBLE_DEVICES='')
    if branch=='coherent_mppi_causal':env.update(LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),PHASE_COHERENT_NOISE='1')
    else:env.pop('LD_PRELOAD',None)
    return module,env


def storage_bytes():
    return sum(p.stat().st_size for root in [O,RAW,R/'runs/v1340_overnight_preparation',R/'runs/v1341_overnight_baseline_relay',R/'runs/v858_nav2_verified/v1341',R/'runs/v1342_dynamic_relay_preparation'] for p in root.rglob('*') if p.is_file() and not p.is_symlink())


def main():
    os.sched_setaffinity(0,{2,3,4,5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    config=read(C/'CAMPAIGN_CONFIG.json');window=read(O/'ROUND_WINDOW.json');guard=(O/'REVIEW_PENDING.before').read_bytes()
    tasks=read(C/'TASKS.json');completed={};results=[];jobs=[]
    summary=dict(passed=False,results=results,unexecuted=[t['task_id'] for t in tasks],skipped_dependencies=[],scope='one frozen adaptedRPP branch staticpair thenconditionaldynamicpair with orderedcuspsegments and measuredgearinterlock',offline=True)
    def rootstop(*_):raise TimeoutError('ROOT_HARD_STOP')
    signal.signal(signal.SIGALRM,rootstop);signal.signal(signal.SIGTERM,rootstop)
    signal.setitimer(signal.ITIMER_REAL,max(.01,remaining(window)-5))
    try:
        for task in tasks:
            if not eligible(task,completed):
                summary['skipped_dependencies'].append(task['task_id']);continue
            authorize(task,window)
            assert storage_bytes()<config['storage_limit_bytes'],'STORAGE_LIMIT'
            out=Path(task['output']);out.mkdir(parents=True,exist_ok=False);dump(out/'TASK.json',task)
            row=dict(task=task['task_id'],branch=task['branch'],stage=task['stage'],role=task['role'],attempted=True,passed=False,native=None,ros=None,audit=None)
            results.append(row);summary['unexecuted'].remove(task['task_id']);dump(O/'PARTIAL_RESULTS.json',results)
            logs=[];(R/'REVIEW_PENDING').unlink()
            try:
                ros,renv=ros_environment(out,task['branch'])
                definitions=[('ros',ros.command(['/usr/bin/python3.12','-B',str(C/'ros_component.py'),str(out/'TASK.json')]),renv),('native',[str(R/'run_phase.sh'),str((C/'native_component.py').relative_to(R)),str(out/'TASK.json')],native_environment())]
                for name,args,env in definitions:
                    log=(out/(name+'.console')).open('x');logs.append(log)
                    jobs.append(subprocess.Popen(args,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True))
                dump(O/'ACTIVE.json',dict(task=task['task_id'],branch=task['branch'],stage=task['stage'],pids=[p.pid for p in jobs],physics_single_instance=True))
                row['monitor']=monitor(jobs,out,remaining=lambda:remaining(window),task_seconds=1600,drain_seconds=90,storage_check=lambda:storage_bytes()<config['storage_limit_bytes'])
            finally:
                for job in jobs:terminate(job)
                for log in logs:log.close()
                (R/'REVIEW_PENDING').write_bytes(guard)
            row.update(worker_returncodes=[p.returncode for p in jobs],native=read(out/'RESULT.json') if (out/'RESULT.json').exists() else None,ros=read(out/'ROS_RESULT.json') if (out/'ROS_RESULT.json').exists() else None)
            jobs=[];dump(O/'PARTIAL_RESULTS.json',results)
            if (row['native'] or {}).get('evidence_saved') and (row['native'] or {}).get('replay',{}).get('passed'):
                code='import sys,json;sys.path.insert(0,sys.argv[1]);from audit import audit;print(json.dumps(audit(json.load(open(sys.argv[2])))))'
                result=subprocess.run([sys.executable,'-B','-c',code,str(C),str(out/'TASK.json')],cwd=R,capture_output=True,text=True,timeout=min(60,max(1,remaining(window)-10)))
                (out/'audit.console').write_text(result.stdout+result.stderr)
                if result.returncode==0:row['audit']=json.loads(result.stdout);dump(out/'FINAL_INDEPENDENT_AUDIT.json',row['audit'])
            row['classification']=classify(row);row['passed']=row['classification']=='PASSED'
            completed[(task['branch'],task['stage'],task['role'])]=row['classification']
            dump(O/'PARTIAL_RESULTS.json',results)
            if row['classification'] not in ['PASSED','FUNCTIONAL_FAILURE_SAFE_COMPLETE']:
                summary['stop_reason']=row['classification'];break
        else:summary['stop_reason']='ALL_FROZEN_BRANCH_DEPENDENCIES_CLOSED'
        summary['passed']=any(all(completed.get((branch,stage,role))=='PASSED' for stage in ['static','dynamic'] for role in ['main','repeat']) for branch in config['branches'])
        summary['passed_scope']='one staticpair and conditional dynamicpair validation; not24/generalization'
    except BaseException as error:
        summary.update(error=repr(error),traceback=traceback.format_exc(),stop_reason='OPERATION_STORAGE_SOURCE_OR_DEADLINE_STOP')
    finally:
        for job in jobs:terminate(job)
        (R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0)
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        summary.update(closed=True,closed_unix=time.time(),source_unchanged=sources(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard,storage_bytes=storage_bytes(),hard_stop_unix=window['absolute_deadline_unix'])
        dump(O/'COMPLETION.json',summary)
        if (O/'ACTIVE.json').exists():(O/'ACTIVE.json').unlink()
        pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False)
        pointer['latest_v1347']=dict(closed=True,any_complete_branch_passed=summary['passed'],attempted=[r['task'] for r in results],unexecuted=summary['unexecuted'],stop_reason=summary.get('stop_reason'),report='docs/CUSP_SEGMENT_V1347_REPORT.md')
        dump(R/'CURRENT_EXPERIMENT.json',pointer)
    # Entirely local zero-model closure, no network dependency and no restart.
    with (O/'finalize.console').open('x') as log:
        result=subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    dump(O/'FINALIZER_EXIT.json',dict(returncode=result.returncode,models=0))
    return 0 if summary['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
