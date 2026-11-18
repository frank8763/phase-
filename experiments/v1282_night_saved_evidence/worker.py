"""Finite saved-data night programme; no new physical model is importable."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('NIGHT_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import concurrent.futures,fcntl,hashlib,json,multiprocessing,os,signal,time,traceback
import night_math
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name;P=R/'runs/v1281_partial_reconnection_fixed24'
def rd(p):return json.loads(Path(p).read_text())
def dump(p,x):
    temp=p.with_suffix('.tmp');temp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(p)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def check_root(w):
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'NIGHT_BOOT_CHANGED'
    remaining=min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
    assert remaining>30,'NIGHT_ROOT_DEADLINE'
    assert sum(p.stat().st_size for p in O.rglob('*')if p.is_file()and not p.is_symlink())+128*1024**2<2*1024**3,'NIGHT2GIB_CAP'
    return remaining
def run_jobs(function,jobs,parallel):
    results=[]
    if parallel:
        with concurrent.futures.ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'))as pool:
            futures=[pool.submit(function,j)for j in jobs]
            for f in futures:results.append(f.result())
    else:
        # Also use a spawned process for serial jobs: identical imports and
        # process-local native counters, no scheduler inheritance artifact.
        with concurrent.futures.ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn'))as pool:
            for j in jobs:results.append(pool.submit(function,j).result())
    return results
def main():
    assert not(O/'WORKER_STARTED.json').exists(),'ONE_NIGHT_WORKER_NO_RETRY'
    assert rd(O/'AUTHORIZATION.json')['models_authorized']is False
    assert not(R/'REVIEW_PENDING').exists(),'NIGHT_LAUNCH_NOT_APPROVED'
    assert all(sha(R/n)==h for n,h in rd(C/'SOURCE_FREEZE.json')['files'].items()),'NIGHT_SOURCE_CHANGED'
    window=rd(O/'ROUND_WINDOW.json');check_root(window)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    sys.addaudithook(night_math.write_scope)
    dump(O/'WORKER_STARTED.json',dict(pid=os.getpid(),started_unix=time.time(),models=0,physical_native=0))
    begin=time.monotonic();error=None;timings=[];ablation=[];counts=0;speed=None;before={};parent_pass=False
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('NIGHT_HARD_STOP')));signal.alarm(max(1,int(check_root(window)-10)))
    try:
        d=rd(P/'COMPLETION.json');f=rd(P/'FINALIZED.json');assert d['closed']and f['closed']and f['manifest_readback']and d['source_unchanged']
        files=rd(P/'LOCAL_MANIFEST.json')['files'];assert len(files)==f['files']
        for n,v in files.items():
            check_root(window);p=R/n;assert p.is_file()and p.stat().st_size==v['bytes']and sha(p)==v['sha256'],'PARENT_MEMBER_CHANGED '+n
        parent_pass=bool(d['passed']and f['fixed24_confirmation_passed'])
        dump(O/'PARENT_READBACK.json',dict(passed=True,files=len(files),parent_confirmation_passed=parent_pass,
            main_gate=d.get('main_gate'),unexecuted=d.get('unexecuted'),complete_repeats=d.get('complete_repeats'),physical_counts=d.get('physical_counts'),old_samples_imported=0))
        # Avoid hiding any safety/evidence/operation failure behind new math.
        safe_failure=d.get('stop_reason')in['SECOND_FUNCTIONAL_FAILURE_FIXED_POOL_STOP','INSUFFICIENT_REMAINING_FOR_COMPLETE_TASK_AUDIT','FIXED24_AND_THREE_REPEATS_COMPLETE']
        if not parent_pass and not safe_failure:
            dump(O/'DIAGNOSTIC_ONLY.json',dict(reason='parent safety/evidence/operation gate failed; no analytical propagation',parent_stop_reason=d['stop_reason'],models=0,physical_native=0))
        else:
            raw=R/'runs/v858_nav2_verified/v1281'
            for p in raw.rglob('*.json'):
                if p.name in['RESULT.json','FINAL_INDEPENDENT_AUDIT.json','AUDIT_ERROR.json']:before[str(p.relative_to(R))]=sha(p)
            if parent_pass:
                jobs=[dict(slot=slot,cpu=2,label='serial_'+str(slot),deadline=window['hard_stop_monotonic']-20)for slot in[1,9,17]]
                t=time.monotonic();serial=run_jobs(night_math.native_audit_job,jobs,False);serial_wall=time.monotonic()-t;timings+=serial
                check_root(window)
                jobs=[dict(slot=slot,cpu=2+i,label='parallel_'+str(slot),deadline=window['hard_stop_monotonic']-20)for i,slot in enumerate([1,9,17])]
                t=time.monotonic();parallel=run_jobs(night_math.native_audit_job,jobs,True);parallel_wall=time.monotonic()-t;timings+=parallel
                assert len(serial)==len(parallel)==3 and all(a['passed']and b['passed']and a['canonical']==b['canonical']for a,b in zip(serial,parallel)),'PARALLEL_AUDIT_NOT_EQUIVALENT'
                speed=dict(serial_wall_s=serial_wall,parallel_wall_s=parallel_wall,throughput_speedup=serial_wall/parallel_wall,
                    exact_results_equal=True,independent_audit_throughput_only=True,not_single_navigation_realtime=True)
                dump(O/'MULTICORE_EQUIVALENCE_AND_TIMING.json',dict(passed=True,measurement=speed,jobs=timings,models=0,physical_native=0))
            # Fixed all available completed EW mains; never choose only winners.
            cases=[]
            for slot in range(17,25):
                folder=raw/f'main_slot{slot:02}'
                if(folder/'EW_ONWARD_SELECTION.json').exists()and(folder/'EW_ONWARD_INPUT.json').exists():cases.append(slot)
            for i in range(0,len(cases),3):
                check_root(window);batch=cases[i:i+3]
                jobs=[dict(slot=slot,cpu=2+j,deadline=window['hard_stop_monotonic']-20)for j,slot in enumerate(batch)]
                result=run_jobs(night_math.timing_job,jobs,True);ablation+=result;counts+=sum(x['analytical_cpp_native']for x in result)
                dump(O/'SAVED_TEMPORAL_ABLATION.json',dict(cases=ablation,scope='fixed current-run saved-state mechanism; not new actual trials',models=0,physical_native=0,analytical_cpp_native=counts))
                dump(O/'PROGRESS.json',dict(stage='saved_temporal_ablation',complete=len(ablation),available=len(cases),models=0,physical_native=0))
            assert all(sha(R/n)==h for n,h in before.items()),'ORIGINAL_MAIN_OR_AUDIT_BYTES_CHANGED'
        if parent_pass:
            inventory=[]
            for method,paths in [
                ('RPP',['experiments/v880_reference_controller_grid']),
                ('Ackermann_MPPI',['experiments/v929_executable_mppi/PROTOCOL.md','experiments/v929_executable_mppi/params.yaml','experiments/v929_executable_mppi/UPSTREAM_SOURCES.json']),
                ('PRIEST',[])]:
                items=[]
                for relative in paths:
                    path=R/relative
                    selected=[path]if path.is_file()else sorted(path.glob('*.yaml'))if path.is_dir()else[]
                    for item in selected:items.append(dict(path=str(item.relative_to(R)),sha256=sha(item),bytes=item.stat().st_size))
                inventory.append(dict(method=method,local_records=items,current_science_vehicle_interface_qualified=False,formal_comparison_executed=False))
            dump(O/'BASELINE_INTERFACE_INVENTORY.json',dict(methods=inventory,models=0,physical_native=0,
                same_model_observation_controls_and_offline_evaluator_required=True,gpu_implementation_qualified=False,
                next_gate='current model Ackermann input, sensor causality, complete ctrl/replay/evaluator qualification before paired baseline development'))
        for n,v in files.items():
            check_root(window);assert sha(R/n)==v['sha256']and(R/n).stat().st_size==v['bytes'],'ORIGINAL_ARCHIVE_MEMBER_CHANGED '+n
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
    finally:
        signal.alarm(0)
        summary=dict(closed=True,passed=error is None,error=error,parent_confirmation_passed=parent_pass,
            multicore_measurement=speed,temporal_ablation_cases=len(ablation),models=0,physical_native=0,training_updates=0,
            analytical_cpp_native=counts+sum(t['analytical_cpp_native']or 0 for t in timings),partial_counts_unknown=error is not None,
            wall_s=time.monotonic()-begin,original_evidence_unchanged=all(sha(R/n)==h for n,h in before.items()),closed_unix=time.time())
        dump(O/'SOFTWARE_COMPLETION.json',summary);print((O/'SOFTWARE_COMPLETION.json').read_text());fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
