"""Once real analytical qualification. No physical factory or navigation."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2]; C=Path(__file__).resolve().parent
O=R/'runs/v1910_dwa_single_writer_reconstruction'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def main():
    os.environ['MUJOCO_GL']='osmesa'
    a=read(O/'ADMISSION.json');w=read(O/'WINDOW.json');identity=read(O/'SOURCE_IDENTITY.json')
    assert a['scope']=='EXACT_ANALYTICAL_RECONSTRUCTION_ONLY' and a['analytical_models_authorized']
    assert not a['plant_authorized'] and not (O/'RESULT.json').exists()
    assert a['source_identity_sha256']==sha(O/'SOURCE_IDENTITY.json')
    assert all(sha(R/n)==h for n,h in identity['files'].items())
    assert os.environ['PHASE_REPO']==str(R) and sorted(os.sched_getaffinity(0))==[2]
    assert not(R/'REVIEW_PENDING').exists()
    assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    with(O/'TARGET_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
    lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    def clock(*_):raise TimeoutError('ANALYTICAL_QUALIFICATION_DUAL_CLOCK')
    signal.signal(signal.SIGALRM,clock);signal.signal(signal.SIGTERM,clock)
    signal.setitimer(signal.ITIMER_REAL,max(.01,min(w['normal_stop_unix']-time.time(),w['normal_stop_monotonic']-time.monotonic())))
    result=dict(passed=False,closed=False,scope=a['scope'],physical_native=0,own_replay_native=0,
                canonical_factory_attempts=0,CPP_simulations=0,first_error=None,profiles=[],
                total_modelwork=None,internal_Allocator_constructions=None,production_admitted=False)
    ledger=None;start=time.monotonic()
    sys.path.insert(0,str(R/'experiments/v1863_remaining_routes_dwa'))
    quota_module=load('real_rebuild_qualified_single_writer_quota',R/'experiments/v1863_remaining_routes_dwa/quota.py')
    quota=quota_module.EvidenceQuota(O,read(O/'inputs/LIMITS_DRAFT.json'))
    quota.bind_external_names([]);quota.write_enforcement_active=True
    io=load('real_rebuild_original_io',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
    emitted=[0]
    def charge(path,n):
        assert emitted[0]+n<=16*1024**2,'QUALIFICATION_STAGE_WRITE_CAP'
        quota.charge_write(path,n);emitted[0]+=n
    quota.prepare_grant(8*1024**2,phase='STOPPED_EVENT_PREPARATION',valid_for_s=480,external_writers=[])
    try:
        # Install our non-model scope guard before the exact legacy guard hook.
        def no_process(event,args):
            if event in {'subprocess.Popen','os.system','os.posix_spawn'}:
                # Original quota uses read-only du; no other child is permitted.
                if event=='subprocess.Popen' and Path(str(args[0])).name=='du':return
                raise AssertionError('QUALIFICATION_NO_EXTERNAL_MODEL_OR_COMPILER')
        sys.addaudithook(no_process)
        caches=load('real_rebuild_cache',R/'experiments/v1447_full_module_guard_identity/task_cache.py')
        guards=load('real_rebuild_guard',R/'experiments/v1447_full_module_guard_identity/guard_binding.py')
        with io.OutputBoundary(O,charge),caches.TaskLocalCaches(O),guards.bind_original_guard(O):
            sys.path.insert(0,str(R/'experiments/v1180_fresh_recovery_chain'))
            import chain_tools
            q=chain_tools.q;np=q.np
            assert Path(q.model.Predictor.step.__code__.co_filename).resolve()==R/'experiments/v1159_bounded_steering_load/model.py'
            work=load('real_rebuild_original_work',R/'experiments/v1863_remaining_routes_dwa/work.py')
            ledger=work.ModelWork(dict(python_native_cap=19860,cpp_native_cap=1),w['normal_stop_unix']);ledger.bind(q)
            from rebuild import bind
            fn,proof=bind((R/'experiments/v1863_remaining_routes_dwa/response.py').read_text(),dict(sys=sys))
            result['loop_identity']=proof
            setup=read(O/'inputs/SETUP.json')
            recipe=load('real_rebuild_recipe',R/'experiments/v1907_dwa_reconstruction_contract/recipe.py')
            inputs=read(O/'INPUTS.json')
            for row in inputs['profiles']:
                assert min(w['normal_stop_unix']-time.time(),w['normal_stop_monotonic']-time.monotonic())>0
                p=O/'inputs'/row['json'];proof=read(p)
                with np.load(O/'inputs'/row['npz'],allow_pickle=False)as z:arrays={k:z[k]for k in z.files}
                rec=recipe.build(proof,arrays,inputs['binding'])
                begin=time.monotonic()
                def callback(packet,requests):return fn(q,setup,packet,requests,None,None)
                actual=recipe.regenerate(rec,proof,inputs['binding'],callback)
                elapsed=time.monotonic()-begin
                assert all(actual[k].tobytes()==arrays[k].tobytes()for k in arrays)
                result['profiles'].append(dict(input=row,byte_exact=True,native=proof['native'],wall_s=elapsed))
            counts=ledger.snapshot();assert counts['python_completed_native']==19860 and counts['python_constructor_returns']==9
            assert counts['cpp_completed_native']==0 and counts['inflight']is None
            result.update(passed=True,real_regeneration_arrays_byte_equal=36,model_work=counts)
    except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        if ledger is not None:result['model_work']=ledger.snapshot()
        result.update(closed=True,wall_s=time.monotonic()-start)
        # Only a bounded result is emitted after no further model work is possible.
        raw=(json.dumps(result,indent=2,allow_nan=False)+'\n').encode();assert len(raw)<65536
        quota.retire_grant()
        with io.OutputBoundary(O,charge):(O/'RESULT.json').write_bytes(raw)
        quota.write_enforcement_active=False
        lock.close()
    print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1

if __name__=='__main__':raise SystemExit(main())
