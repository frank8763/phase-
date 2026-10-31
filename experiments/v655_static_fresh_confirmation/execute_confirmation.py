"""Fresh frozen confirmation after an offline provenance-validator repair."""
import datetime
import hashlib
from pathlib import Path
import signal
import time
import traceback
from bounded_execution import Window, read, dump, digest

src = Path(__file__).resolve().parent; repo = src.parents[1]
dev = read(repo/'runs/v654_static_overnight/development01/COMPLETION.json',{})
assert dev.get('development_passed'), 'VALIDATOR_DEVELOPMENT_PREREQUISITE_NOT_MET'
assert read(repo/'runs/v654_static_overnight/CONTACT_PATH_DIAGNOSIS.json')['passed']
assert read(repo/'runs/v654_static_overnight/ZERO_STEP_CONTACT_REGRESSION.json')['passed']
proof = read(src/'DECISION_EQUIVALENCE.json'); assert proof['equivalent']
parent = repo/'experiments/v653_static_log_recovery'
parent_freeze = read(parent/'SOURCE_FREEZE.json')
for name in proof['files']:
    assert digest(parent/name)==parent_freeze[name]
    text = (src/name).read_text()
    if name=='run_static.py':
        text=text.replace("/'v655_static_fresh_confirmation'/a.name","/'v653_static_log_recovery'/a.name")
    assert hashlib.sha256(text.encode()).hexdigest()==parent_freeze[name], 'ONLINE_DECISION_CHANGED'
registered = read(src/'CANDIDATE_FREEZE.json')
assert all(digest(src/n)==h for n,h in registered['source_sha256'].items())
assert digest(src/'PROTOCOL.md')==registered['protocol_sha256']
# Inspect only Phase trial ledgers; no unrelated home-directory/process access.
for ledger in (repo/'runs').glob('**/LEDGER.json'):
    for row in read(ledger,[]):
        assert not 95000001<=row.get('seed',0)<=95000600, 'FRESH_POOL_ALREADY_USED'
deadline = datetime.datetime.fromisoformat('2026-11-01T08:00:00+08:00').timestamp()
window = Window(src,'v655_static_fresh_confirmation','confirmation01',18000,deadline)
dump(window.path/'CANDIDATE_FREEZE.json',registered)
dump(window.path/'DECISION_EQUIVALENCE.json',proof)
outcomes, selected, repeats = [], [], []
status='PREFLIGHT_RUNNING'
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
try:
    for seed in range(95000001,95000601):
        scene='single_event'if seed%2 else'legacy_two'
        row=window.run(f'preflight_{seed}_{scene}',seed,scene,True)
        if row is None:
            status='PREFLIGHT_BUDGET_INCOMPLETE';break
        eligible={s:sum(x['scene']==s and bool(x['feasibility']and x['feasibility']['eligible'])
                        for x in window.ledger)for s in ['single_event','legacy_two']}
        if all(n>=12 for n in eligible.values()):
            status='SCREENING_QUOTAS_REACHED';break
    else:
        status='SCREENING_POOL_EXHAUSTED'
    if status in ['SCREENING_QUOTAS_REACHED','SCREENING_POOL_EXHAUSTED']:
        for scene in ['single_event','legacy_two']:
            selected += [x for x in window.ledger if x['scene']==scene and x['feasibility']and x['feasibility']['eligible']][:12]
        selected.sort(key=lambda x:x['seed'])
        dump(window.path/'SELECTION_FREEZE.json',{'status':'LOCKED_BEFORE_NAVIGATION',
             'locked_unix':time.time(),'screened':len(window.ledger),'candidate_pool_maximum':600,
             'unscreened_candidates_not_counted':600-len(window.ledger),
             'tasks':[{'seed':x['seed'],'scene':x['scene'],'preflight_name':x['name'],
                       'scene_model_sha256':x['protocol']['full_model_sha256']}for x in selected],
             'eligible_counts':{s:sum(x['scene']==s and bool(x['feasibility']and x['feasibility']['eligible'])
                                    for x in window.ledger)for s in ['single_event','legacy_two']}})
        status='CONFIRMATION_RUNNING'if len(selected)==24 else'INSUFFICIENT_ELIGIBLE_TASKS'
    if status=='CONFIRMATION_RUNNING':
        for task in selected:
            row=window.run(f'confirm_{task["seed"]}_{task["scene"]}',task['seed'],task['scene'])
            if row is None:
                status='CONFIRMATION_BUDGET_INCOMPLETE';break
            result=window.result(row);safe=window.audit(row)
            same=bool(row['protocol']and row['protocol']['full_model_sha256']==task['protocol']['full_model_sha256'])
            good=bool(result and result['strict_safe_arrival']and result['goal_distance_m']<=.45 and safe and same)
            outcomes.append({'name':row['name'],'seed':row['seed'],'scene':row['scene'],
                             'result':result,'strict_success':good,'physical_audit_passed':safe,
                             'scene_matches_preflight':same,'run_root':str(window.root.relative_to(repo))})
            dump(window.path/'CONFIRMATION_RESULTS.json',outcomes)
            print('CONFIRMATION',len(outcomes),'strict',sum(x['strict_success']for x in outcomes),flush=True)
            if not safe or not same:
                status='GATE_FAILED_PHYSICAL_SOURCE_OR_MODEL_AUDIT';break
            if sum(not x['strict_success']for x in outcomes)>=2:
                status='GATE_FAILED_TWO_NON_SUCCESSES';break
        else:
            status='NAVIGATION_GATE_PASSED_PENDING_REPEATS'
    if status=='NAVIGATION_GATE_PASSED_PENDING_REPEATS':
        for seed,scene in [(93000074,'legacy_two'),(93000045,'single_event'),(91000002,'single_event')]:
            row=window.run(f'repeat_{seed}_{scene}',seed,scene)
            if row is None:
                status='REPEAT_BUDGET_INCOMPLETE';break
            base=repo/'runs/v651_static_progress'/f'dev29_seed{seed}_{scene}/paired'
            record=window.repeat(row,base);repeats.append(record)
            dump(window.path/'REPEAT_AUDIT.json',repeats)
            if not record['matched']:
                status='GATE_FAILED_REPEAT';break
        else:
            status='ALL_TASKS_AND_REPEATS_AUDITED'
except BaseException as error:
    status='STOPPED_EXCEPTION'
    dump(window.path/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
    classes={s:sum(x['strict_success']for x in outcomes if x['scene']==s)for s in ['single_event','legacy_two']}
    checks={'24_locked_distinct_tasks':len(selected)==24 and len({x['seed']for x in selected})==24,
            'all_24_attempts':len(outcomes)==24,'at_least23_strict_arrivals':sum(x['strict_success']for x in outcomes)>=23,
            'single_at_least11':classes['single_event']>=11,'two_at_least11':classes['legacy_two']>=11,
            'all27_physical_audits':len(window.physical)==27 and all(x['passed']for x in window.physical),
            'three_full_state_contact_repeats':len(repeats)==3 and all(x['matched']for x in repeats),
            'budget_respected':window.remaining()>=0,
            'all_source_and_protocol_frozen':all(digest(src/n)==h for n,h in window.sources.items())
                and all(digest(src/n)==h for n,h in window.documents.items())}
    dump(window.path/'COMPLETION.json',{'status':status,'static_engineering_acceptance_passed':all(checks.values()),
         'elapsed_s':time.monotonic()-window.started,'limit_s':window.limit,'checks':checks,
         'selected_tasks':len(selected),'completed_confirmation_attempts':len(outcomes),
         'strict_arrivals':sum(x['strict_success']for x in outcomes),'class_successes':classes,
         'remaining_selected_unattempted':[{'seed':x['seed'],'scene':x['scene']}for x in selected[len(outcomes):]],
         'repeats_attempted':len(repeats),'dynamic_started':False,'training_updates':0,
         'contact_comparison_scope':'all raw digests verified; all events exact after only preregistered XML path+verified bytes normalization',
         'scope':'fresh selected finite static cylinder benchmark; independent audit and user review required before dynamics'})
    dump(window.path/'ACTIVE.json',{'status':status,'completed':True})
    print('CONFIRMATION_COMPLETE',status,'accepted',all(checks.values()),flush=True)
