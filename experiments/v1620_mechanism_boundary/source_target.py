"""One new source/selection/denominator target, NOT a runtime qualification."""
import ast
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback
from spec import C, O, R, STOP, digest, encoded, manifest


def put(name, value):
    raw = encoded(value)
    assert len(raw) <= 2*1024**2
    path=O/name; temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_bytes(raw); temp.replace(path)


def main():
    os.environ.update(MUJOCO_GL='osmesa', CUDA_VISIBLE_DEVICES='',
                      PYOPENGL_PLATFORM='osmesa', OMP_NUM_THREADS='1',
                      OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    assert os.environ['PHASE_REPO'] == str(R) and sorted(os.sched_getaffinity(0)) == [2]
    sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
    import resource_policy
    resource_policy.apply()
    p=R/'experiments/v1504_priest_namespace_worker/common.py'
    s=importlib.util.spec_from_file_location('v1620_immutable_guard',p)
    common=importlib.util.module_from_spec(s);s.loader.exec_module(common);common.guard(O)
    class Ban(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0] in {'numpy','mujoco','torch','jax','rclpy','kernel','runtime','factory','vehicle'}:
                raise AssertionError('MECHANISM_SOURCE_ONLY:'+name)
    sys.meta_path.insert(0,Ban())
    start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SOURCE_120S')));signal.alarm(120)
    lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with (O/'SOURCE_ONCE_CLAIM.json').open('xb') as f:f.write(encoded(dict(unix=time.time(),models_authorized=False)))
    result=dict(passed=False,closed=False,models=0,native=0,FFI=0,physical_native=0,replay_native=0,
                complete_runtime_qualified=False,physical_admission=False)
    try:
        from policies import select_time,select_refuge
        from transforms import transformed,TIMING,ONWARD
        from analyze import summarize
        locked=json.loads((O/'TASKS_LOCKED.json').read_text());assert locked==manifest()
        assert locked['assignment_count']==20 and len({t['task']['phase'] for t in locked['tasks']})==12
        # Check source against its historical immutable manifest without import.
        frozen=json.loads((R/'experiments/v1281_partial_reconnection_fixed24/WORKER_FREEZE.json').read_text())['files']
        frozen.update(json.loads((R/'experiments/v1218_fixed24_current/PACKAGE_FREEZE.json').read_text())['files'])
        bindings=[]
        for relative,kind,variant in [(TIMING,'time','no_time'),(ONWARD,'onward','no_onward')]:
            path=R/relative;identity=hashlib.sha256(path.read_bytes()).hexdigest();assert frozen[relative]==identity
            tree,proof=transformed(path.read_text(),kind,variant);compile(tree,str(C/('generated_'+kind+'.py')),'exec')
            bindings.append(dict(path=relative,proof=proof))
        # New decision fixtures exercise only the introduced selection semantics.
        records=[dict(wait_native=i,passed=i in [0,50],selection_slack_m=.1 if i==50 else .01)for i in range(0,2000,50)]
        assert select_time(records,'full')['selected']['wait_native']==50
        assert select_time(records,'no_time')['selected']['wait_native']==0
        records[0]['passed']=False;assert select_time(records,'no_time')['selected']is None
        cs=[dict(id=i,guide_score=i,safe_prefix=True,prefix_feedback_stop_passed=True,onward_passed=i==1)for i in range(2)]
        assert select_refuge(cs,'full')['selected']['id']==1 and select_refuge(cs,'no_onward')['selected']['id']==0
        cs[0]['prefix_feedback_stop_passed']=False
        assert select_refuge(cs,'no_onward')['selected']['id']==1
        negatives=[]
        def refuse(name,fn):
            try:fn()
            except (AssertionError,ValueError,PermissionError,KeyError):negatives.append(name)
            else:raise AssertionError('SOURCE_NEGATIVE_ACCEPTED:'+name)
        refuse('missing_wait',lambda:select_time(records[:-1],'full'))
        bad=copy.deepcopy(records);bad[0]['selection_slack_m']=float('nan');refuse('nonfinite_slack',lambda:select_time(bad,'full'))
        refuse('unknown_variant',lambda:select_refuge(cs,'no_safety'))
        empty=summarize(locked,[]);assert len(empty['unexecuted_assignments'])==20 and empty['whole_successes']==0
        assignment=locked['tasks'][0]['assignments'][0]
        fake=dict(assignment_id=assignment['assignment_id'],variant=assignment['variant'],outcome='arrival',whole_passed=True,whole_audit_verified=False)
        refuse('unverified_arrival',lambda:summarize(locked,[fake]))
        row=dict(assignment_id=assignment['assignment_id'],variant=assignment['variant'],outcome='timeout',whole_passed=False)
        refuse('duplicate_outcome',lambda:summarize(locked,[row,row]))
        refuse('runtime_admission_absent',lambda:__import__('spec').authority('MODEL'))
        result.update(passed=True,negative_cases=negatives,source_bindings=bindings,
                      locked_task_sha256=digest(locked),new_tasks=12,assignments=20,
                      selection_tests_are_software_only=True,
                      original_source_imports=0,original_model_calls=0,
                      source_API_only=True,all_formal_runs_unexecuted=True)
        put('EMPTY_RESULTS.json',empty)
        files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in C.iterdir()if p.is_file()}
        files[str((O/'TASKS_LOCKED.json').relative_to(R))]=hashlib.sha256((O/'TASKS_LOCKED.json').read_bytes()).hexdigest()
        put('SOURCE_FREEZE.json',dict(files=files,models_authorized=False,physical_admission=False,source_API_only=True))
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);result.update(closed=True,wall_s=time.monotonic()-start);put('SOURCE_RESULT.json',result);lock.close()
    print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','physical_admission','models']}))
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
