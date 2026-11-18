"""Same fixed independent jobs, serial vs four processes; no physics."""
from pathlib import Path
import sys,os,json,time,signal,fcntl,hashlib,traceback,statistics
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1176_multicore_stop_backend'
sys.path.insert(0,str(C))
import backend
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import numpy as np
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    assert not(O/'COMPLETION.json').exists()and not(C/'SOURCE_FREEZE.json').exists(),'NO_BENCHMARK_RESTART'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    original=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(original).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    begin=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('MULTICORE_SOFTWARE_900S')));signal.setitimer(signal.ITIMER_REAL,900)
    frozen={};jobs=[];serial_rows=[];parallel_rows=[];error=None;sr=None;pr=None
    dump(O/'ROUND_WINDOW.json',dict(software_only=True,started_unix=time.time(),deadline_monotonic=begin+900,multicore_authorized_by_user=True,physical_window_open=False))
    try:
        bundle=json.loads((R/'runs/v1175_low_speed_input_entry/BUNDLE.json').read_text())
        files=[*C.glob('*.py'),C/'PROTOCOL.md',C/'TASKS.json',R/'runs/v1175_low_speed_input_entry/BUNDLE.json',R/'runs/v1173_rate_preconditioned_input/INPUTS.json',R/'runs/v1159_bounded_steering_load/profile.so',R/'experiments/v1159_bounded_steering_load/profile.cpp',R/'experiments/v1159_bounded_steering_load/PARAMETERS.json']
        # Capture all legacy analytical source/JSON dependencies already bound
        # by input qualification; no old source mutation to enable extra cores.
        for rel in ['experiments/v1175_low_speed_input_entry/SOURCE_FREEZE.json','experiments/v1159_bounded_steering_load/SOURCE_FREEZE.json']:
            ff=json.loads((R/rel).read_text())['files'];files.append(R/rel);files.extend(R/p for p in ff if Path(p).suffix in ['.py','.json','.cpp'])
        top=[]
        for core in [2,3,4,5]:
            p=Path(f'/sys/devices/system/cpu/cpu{core}/topology');top.append(dict(cpu=core,package=(p/'physical_package_id').read_text().strip(),core=(p/'core_id').read_text().strip()))
        assert len({(v['package'],v['core'])for v in top})==4
        for component in bundle['components']:
            file=R/component['plan'];assert sha(file)==component['plan_sha256'];files.append(file)
            with np.load(file)as z:ss,mm,rr=[z[k].copy()for k in ['states','memory','requests']]
            offsets=sorted(set([*range(0,len(rr),8),len(rr)-1]));loaded=False;flag=[]
            for v,w,_ in rr:
                flag.append(loaded)
                if v>=.005:loaded=True
            for i in offsets:
                jobs.append(dict(id=len(jobs),plan=component['name'],offset=i,origin=dict(state=ss[i].tolist(),last_ctrl=mm[i,:4].tolist(),integral=float(mm[i,4]),virtual_rate=.6,coupled_episode=False,steering_motion_active=False,steering_load_episode=bool(flag[i]))))
        dump(C/'TASKS.json',dict(jobs=jobs,total_jobs=len(jobs),source='immutable software plans, not new actual states',per_job_complete_stop=2200,cores=top,same_jobs_serial_then_parallel=True))
        frozen={str(p.relative_to(R)):sha(p)for p in set(files)};dump(C/'SOURCE_FREEZE.json',dict(files=frozen,before_new_prediction=True,mode='analytical_multiprocessing_only'))
        serial_rows,sr=backend.serial(jobs,frozen);dump(O/'SERIAL.json',dict(rows=serial_rows,timing=sr))
        parallel_rows,pr=backend.parallel(jobs,frozen);dump(O/'PARALLEL.json',dict(rows=parallel_rows,timing=pr))
        keys=['id','plan','offset','passed','checks','minimum_raw','state_sha256','ctrl_sha256','memory_sha256','completed_analytical_native']
        assert len(serial_rows)==len(parallel_rows)==len(jobs)
        for a,b in zip(serial_rows,parallel_rows,strict=True):assert all(a[k]==b[k]for k in keys),'PARALLEL_ARRAY_OR_CHECK_OR_COUNT_MISMATCH'
        assert pr['workers']==4 and pr['cores']==[2,3,4,5],'FOUR_CORE_RESOURCE_DISTRIBUTION'
        assert all(sha(R/p)==h for p,h in frozen.items()),'SOURCE_CHANGED'
        serial_total=sr['setup_s']+sr['execution_s'];parallel_total=pr['end_to_end_including_startup_shutdown_s'];speedup=serial_total/parallel_total
        chosen='four_process'if parallel_total<serial_total else'serial_for_this_workload'
        result=dict(passed=True,source_job_count=len(jobs),exact_complete_arrays_sha_identical=True,work_per_backend=len(jobs)*2200,total_new_analytical_native=len(jobs)*4400,
            original_stop_proof_passed=sum(r['passed']for r in serial_rows),original_stop_proof_rejected=sum(not r['passed']for r in serial_rows),serial_timing=sr,parallel_timing=pr,measured_net_speedup_including_startup=speedup,
            serial_job_p50_s=float(np.quantile([r['wall_s']for r in serial_rows],.5)),serial_job_p95_s=float(np.quantile([r['wall_s']for r in serial_rows],.95)),parallel_job_p50_s=float(np.quantile([r['wall_s']for r in parallel_rows],.5)),parallel_job_p95_s=float(np.quantile([r['wall_s']for r in parallel_rows],.95)),
            selected_backend_for_this_workload=chosen,validated_max_workers=4,max_cpu_thread_count_per_worker=1,physics_still_single_owner=True,gpu_port_started=False,other_processes_inspected=False,zero_resource_contention_guaranteed=False,
            full_reference_or_physics_admission=False,models=0,physical_native=0,training_updates=0)
        dump(O/'RESULT.json',result)
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        done=dict(closed=True,error=error,serial_completed_jobs=len(serial_rows),parallel_completed_jobs=len(parallel_rows),serial_analytical_native=len(serial_rows)*2200,parallel_analytical_native=len(parallel_rows)*2200,parallel_unreturned_work_unknown=error is not None and not parallel_rows,models=0,physical_native=0,training_updates=0,source_unchanged=all(sha(R/p)==h for p,h in frozen.items()),guard_original=(R/'REVIEW_PENDING').read_bytes()==original,physical_window_open=False,wall_s=time.monotonic()-begin)
        dump(O/'COMPLETION.json',done);print(json.dumps(done));fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
