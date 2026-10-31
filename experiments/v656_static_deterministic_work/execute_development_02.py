"""Three new-version development baselines and exact same-version repeats."""
import datetime
from pathlib import Path
import signal
import time
import traceback
from bounded_execution import Window,read,dump,digest

src=Path(__file__).resolve().parent;repo=src.parents[1]
assert read(repo/'runs/v654_static_overnight/development01/COMPLETION.json')['status']=='DEVELOPMENT_REPEAT_FAILED'
assert read(repo/'runs/v656_static_deterministic_work/FIXED_WORK_ZERO_SIM_REPLAY.json')['passed']
deadline=datetime.datetime.fromisoformat('2026-11-01T08:00:00+08:00').timestamp()
window=Window(src,'v656_static_deterministic_work','development02',5400,deadline)
tasks=[(93000074,'legacy_two'),(93000045,'single_event'),(91000002,'single_event')]
baselines=[];repeats=[];status='DEVELOPMENT_BASELINES_RUNNING'
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
try:
    for seed,scene in tasks:
        row=window.run(f'dev30_seed{seed}_{scene}',seed,scene)
        if row is None:status='BASELINE_BUDGET_INCOMPLETE';break
        result=window.result(row);safe=window.audit(row)
        old=repo/'runs/v651_static_progress'/f'dev29_seed{seed}_{scene}/paired'
        prior=read(old/'geometry_memory/result.json')
        same=bool(result and result['normalized_initial_state_hash']==prior['normalized_initial_state_hash']
                  and row['protocol']['full_model_sha256']==read(old/'STATIC_PROTOCOL.json')['full_model_sha256'])
        good=bool(result and result['strict_safe_arrival']and safe and same)
        baselines.append({'name':row['name'],'seed':seed,'scene':scene,'passed':good,'physical_audit_passed':safe,
                          'same_initial_state_and_model_as_v651':same,'result':result})
        dump(window.path/'BASELINES.json',baselines)
        if not good:status='BASELINE_FAILED';break
    else:status='BASELINES_PASSED_PENDING_REPEATS'
    if status=='BASELINES_PASSED_PENDING_REPEATS':
        for seed,scene in tasks:
            row=window.run(f'dev30_repeat{seed}_{scene}',seed,scene)
            if row is None:status='REPEAT_BUDGET_INCOMPLETE';break
            base=window.root/f'dev30_seed{seed}_{scene}/paired'
            record=window.repeat(row,base);repeats.append(record)
            dump(window.path/'REPEAT_AUDIT.json',repeats)
            if not record['matched']:status='DEVELOPMENT_REPEAT_FAILED';break
        else:status='THREE_BASELINES_AND_FULL_STATE_REPEATS_PASSED'
except BaseException as error:
    status='STOPPED_EXCEPTION'
    dump(window.path/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
    passed=status=='THREE_BASELINES_AND_FULL_STATE_REPEATS_PASSED' and window.remaining()>=0
    dump(window.path/'COMPLETION.json',{'status':status,'development_passed':passed,'static_acceptance_passed':False,
         'elapsed_s':time.monotonic()-window.started,'limit_s':window.limit,'baselines_attempted':len(baselines),
         'repeats_attempted':len(repeats),'source_revision':'progress_30_fixed_search_work',
         'dynamic_started':False,'training_updates':0})
    dump(window.path/'ACTIVE.json',{'status':status,'completed':True})
    print('DEVELOPMENT_COMPLETE',status,flush=True)
