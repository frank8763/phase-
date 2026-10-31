"""One bounded fresh static confirmation; no tuning or automatic new windows."""
import datetime, fcntl, hashlib, json, os, signal, subprocess, time, traceback
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np

repo = Path(__file__).resolve().parents[2]
src = Path(__file__).parent
parent = repo/'experiments/v651_static_progress'
root = repo/'runs/v652_static_confirmation'
root.mkdir(exist_ok=True)
lock = (root/'window.lock').open('a+')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

def read(p):
    return json.loads(p.read_text()) if p.exists() else None

def dump(p, j):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp = p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
    tmp.replace(p)

baseline_tasks = [(93000074,'legacy_two'),(93000045,'single_event'),(91000002,'single_event')]
for seed, scene in baseline_tasks:
    base = repo/'runs/v651_static_progress'/f'dev29_seed{seed}_{scene}'/'paired'
    audit = read(base/'DEVELOPMENT_AUDIT.json')
    assert audit and audit['strict_safe_arrival'] and audit['checks_passed'], 'DEVELOPMENT_PREREQUISITE_NOT_MET'
registered_parent = read(parent/'CANDIDATE_29.json')['source_sha256']
equivalent = {}
for name, digest in registered_parent.items():
    assert hashlib.sha256((parent/name).read_bytes()).hexdigest() == digest
    original, copied = (parent/name).read_text(), (src/name).read_text()
    if name == 'run_static.py':
        copied = copied.replace("/'v652_static_confirmation'/a.name", "/'v651_static_progress'/a.name")
    equivalent[name] = copied == original
assert all(equivalent.values()), 'COPIED_DECISION_SOURCE_MISMATCH'
window = root/'confirmation_window01'
window.mkdir()
start = time.monotonic()
started_unix = time.time()
hard_deadline = datetime.datetime(2026,10,31,23,45,tzinfo=ZoneInfo('Asia/Shanghai')).timestamp()
limit = min(14400, hard_deadline-started_unix)
assert limit > 960, 'TOO_LATE_FOR_BOUNDED_CONFIRMATION'
freeze = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(src.glob('*.py'))}
protocol_hash = hashlib.sha256((src/'PROTOCOL.md').read_bytes()).hexdigest()
dump(window/'WINDOW.json', {'started_unix':started_unix,'started_local':datetime.datetime.fromtimestamp(started_unix,ZoneInfo('Asia/Shanghai')).isoformat(),'limit_s':limit,'absolute_deadline_unix':started_unix+limit,'pid':os.getpid(),'separate_from_original_v650_v651_window':True,'authorization':'latest user instruction to analyze, solve and continue static stability; no training/dynamics','dynamic_requires_user_review':True})
dump(window/'SOURCE_FREEZE.json',freeze)
dump(window/'DECISION_EQUIVALENCE.json',{'parent':'V651 revision29','files':equivalent,'only_normalization':'runner output root v652 -> v651','parent_registered_hashes':registered_parent})
(window/'PROTOCOL.md').write_bytes((src/'PROTOCOL.md').read_bytes())
(window/'PRE_NAVIGATION_SCREENING_AMENDMENT.md').write_bytes((src/'PRE_NAVIGATION_SCREENING_AMENDMENT.md').read_bytes())
(window/'CANDIDATE_FREEZE.json').write_bytes((src/'CANDIDATE_FREEZE.json').read_bytes())
ledger, outcomes, physical, repeats = [], [], [], []

def remaining():
    return limit-(time.monotonic()-start)

def frozen():
    assert hashlib.sha256((src/'PROTOCOL.md').read_bytes()).hexdigest() == protocol_hash
    assert all(hashlib.sha256((src/name).read_bytes()).hexdigest() == digest for name,digest in freeze.items()), 'SOURCE_CHANGED'

def execute(cmd, log, seconds):
    with log.open('w') as stream:
        proc = subprocess.Popen(cmd,cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            return proc.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL); proc.wait()
            return 124
        except BaseException:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM)
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL); proc.wait()
            raise

def run(name, seed, scene, feasibility=False):
    frozen()
    if remaining() < (46 if feasibility else 960):
        return None
    dump(window/'ACTIVE.json',{'name':name,'seed':seed,'scene':scene,'feasibility_only':feasibility,'started_unix':time.time()})
    cmd = [str(repo/'run_phase.sh'),str(src.relative_to(repo)/'run_static.py'),'--name',name,'--seed',str(seed),'--scene',scene,'--conditions','geometry_memory','--wall-seconds',str(40 if feasibility else 900),'--max-steps','1200']
    if feasibility: cmd += ['--feasibility-only']
    begin = time.monotonic()
    code = execute(cmd,window/(name+'.console'),45 if feasibility else 905)
    pair = root/name/'paired'
    row = {'name':name,'seed':seed,'scene':scene,'feasibility_only':feasibility,'returncode':code,'wall_s':time.monotonic()-begin,'completion':read(pair/'completion.json'),'preflight':read(pair/'PREFLIGHT.json'),'feasibility':read(pair/'TASK_FEASIBILITY.json'),'protocol':read(pair/'STATIC_PROTOCOL.json'),'interrupted':read(pair/'geometry_memory/interrupted.json')}
    ledger.append(row)
    dump(window/'LEDGER.json',ledger)
    dump(window/'ACTIVE.json',{'status':'IDLE','last_completed':name})
    print(name,'code',code,'eligible',None if row['feasibility'] is None else row['feasibility']['eligible'],'remaining_s',round(remaining(),1),flush=True)
    return row

def audit_run(name, result):
    pair = root/name/'paired'
    if result is None or remaining() < 50: return False
    frozen()
    code = execute([str(repo/'run_phase.sh'),str(src.relative_to(repo)/'replay_native_audit.py'),str(pair)],pair/'native_replay.console',35)
    replay = read(pair/'NATIVE_REPLAY_AUDIT.json')
    integrity_code = execute(['python',str(repo/'experiments/v648_static_unknown/audit_results.py'),str(pair)],pair/'integrity.console',15)
    cell = pair/'geometry_memory'
    admission = [json.loads(s) for s in (cell/'model_admission.jsonl').read_text().splitlines()]
    plans = {int(f.stem.split('_')[-1]) for f in cell.glob('planning_*.json')}
    transition = cell/'gear_transitions.jsonl'
    switches = {json.loads(s)['step'] for s in transition.read_text().splitlines()} if transition.exists() else set()
    bypasses = [x['step'] for previous,x in zip(admission[:-1],admission[1:]) if x['active_gear'] != previous['active_gear'] and x['step'] not in plans and x['step'] not in switches]
    passed = bool(code == 0 and integrity_code == 0 and replay and replay['status'] == 'MATCHED_RECORDED_PUBLIC_STATES' and replay['maximum_full_public_qpos_error'] <= 1e-8 and replay['maximum_full_public_qvel_error'] <= 1e-8 and replay['minimum_reconstructed_native_actual_axis_AABB_clearance_m'] >= .15-1e-8 and replay['reconstructed_native_states_below_015'] == 0 and replay['replay_obstacle_contact_records'] == 0 and not bypasses and result['minimum_actual_self_domain_margin_m'] >= 0 and result['self_geometry_checked_native_ticks'] == result['physics_steps'] and result['static_obstacle_pose_unchanged'] and result['root_mutations_outside_mjstep'] == 0 and all(result['contacts'][k] == 0 for k in ['robot_obstacle_contact_records','robot_obstacle_penetration_records','unknown_contact_records']))
    physical.append({'name':name,'passed':passed,'replay':replay,'integrity_passed':integrity_code == 0,'unchecked_cusp_switch_steps':bypasses})
    dump(root/'FINAL_PHYSICAL_AUDITS.json',physical)
    return passed

status = 'PREFLIGHT_RUNNING'
selected = []
def stop_signal(*_):
    raise RuntimeError('BOUNDARY_OR_USER_STOP_SIGNAL')
signal.signal(signal.SIGTERM,stop_signal)
try:
    for seed in range(94000001,94000361):
        scene = 'single_event' if seed%2 else 'legacy_two'
        if run(f'preflight_{seed}_{scene}',seed,scene,True) is None:
            status = 'PREFLIGHT_BUDGET_INCOMPLETE'; break
        eligible = {kind:sum(x['scene'] == kind and bool(x['feasibility'] and x['feasibility']['eligible']) for x in ledger) for kind in ['single_event','legacy_two']}
        if all(count >= 12 for count in eligible.values()):
            status = 'SCREENING_QUOTAS_REACHED'; break
    else:
        status = 'SCREENING_POOL_EXHAUSTED'
    if status in ['SCREENING_QUOTAS_REACHED','SCREENING_POOL_EXHAUSTED']:
        for scene in ['single_event','legacy_two']:
            candidates = [x for x in ledger if x['scene'] == scene and x['feasibility'] and x['feasibility']['eligible']]
            selected += candidates[:12]
        selected.sort(key=lambda x:x['seed'])
        dump(window/'SELECTION_FREEZE.json',{'status':'LOCKED_BEFORE_NAVIGATION','screened':len(ledger),'candidate_pool_maximum':360,'unscreened_candidates_not_counted':360-len(ledger),'tasks':[{'seed':x['seed'],'scene':x['scene'],'preflight_name':x['name'],'scene_model_sha256':x['protocol']['full_model_sha256']} for x in selected],'eligible_counts':{scene:sum(x['scene'] == scene and bool(x['feasibility'] and x['feasibility']['eligible']) for x in ledger) for scene in ['single_event','legacy_two']},'scope':'joint-limit-consistent geometric-reference-selected static cylinder tasks; not unfiltered random population'})
        status = 'CONFIRMATION_RUNNING' if len(selected) == 24 else 'INSUFFICIENT_ELIGIBLE_TASKS'
    if status == 'CONFIRMATION_RUNNING':
        for task in selected:
            row = run(f'confirm_{task["seed"]}_{task["scene"]}',task['seed'],task['scene'])
            if row is None: status = 'CONFIRMATION_BUDGET_INCOMPLETE'; break
            result = (row['completion'] or {}).get('results',[])
            result = result[0] if result else None
            same = bool(row['protocol'] and row['protocol']['full_model_sha256'] == task['protocol']['full_model_sha256'])
            safe = audit_run(row['name'],result)
            good = bool(result and result['strict_safe_arrival'] and same and safe)
            outcomes.append({'name':row['name'],'seed':row['seed'],'scene':row['scene'],'result':result,'strict_success':good,'scene_matches_preflight':same,'physical_audit_passed':safe})
            dump(window/'CONFIRMATION_RESULTS.json',outcomes)
            print('CONFIRMATION',len(outcomes),'arrivals',sum(x['strict_success'] for x in outcomes),flush=True)
            if not safe or not same: status = 'GATE_FAILED_PHYSICAL_SOURCE_OR_SCENE_AUDIT'; break
            if sum(not x['strict_success'] for x in outcomes) >= 2: status = 'GATE_FAILED_TWO_NON_SUCCESSES'; break
        else: status = 'NAVIGATION_GATE_PASSED_PENDING_REPEATS'
    if status == 'NAVIGATION_GATE_PASSED_PENDING_REPEATS':
        for seed, scene in baseline_tasks:
            row = run(f'repeat_{seed}_{scene}',seed,scene)
            if row is None: status = 'REPEATS_BUDGET_INCOMPLETE'; break
            result = (row['completion'] or {}).get('results',[])
            result = result[0] if result else None
            safe = audit_run(row['name'],result)
            base = repo/'runs/v651_static_progress'/f'dev29_seed{seed}_{scene}/paired'
            other = root/row['name']/'paired'
            old_result = read(base/'geometry_memory/result.json')
            old_rows = [json.loads(s) for s in (base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
            new_log = other/'geometry_memory/v648_execution.jsonl'
            new_rows = [json.loads(s) for s in new_log.read_text().splitlines()] if new_log.exists() else []
            errors = {key:max((float(np.max(np.abs(np.array(a[key])-np.array(b[key])))) for a,b in zip(old_rows,new_rows)),default=float('inf')) for key in ['qpos_full','qvel_full','ctrl']}
            matched = bool(safe and result and result['strict_safe_arrival'] and len(old_rows) == len(new_rows) and max(errors.values()) <= 1e-8 and result['normalized_initial_state_hash'] == old_result['normalized_initial_state_hash'] and result['contacts']['contact_log_content_sha256'] == old_result['contacts']['contact_log_content_sha256'] and read(base/'STATIC_PROTOCOL.json')['full_model_sha256'] == read(other/'STATIC_PROTOCOL.json')['full_model_sha256'])
            repeats.append({'name':row['name'],'seed':seed,'scene':scene,'matched':matched,'full_public_maximum_errors':{k:(v if np.isfinite(v) else None) for k,v in errors.items()},'original_public_steps':len(old_rows),'repeat_public_steps':len(new_rows)})
            dump(window/'REPEAT_AUDIT.json',repeats)
            if not matched: status = 'GATE_FAILED_REPEAT'; break
        else: status = 'ALL_TASKS_AND_REPEATS_AUDITED'
except BaseException as error:
    status = 'STOPPED_EXCEPTION'
    dump(window/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
    classes = {s:sum(x['strict_success'] for x in outcomes if x['scene'] == s) for s in ['single_event','legacy_two']}
    checks = {'24_fixed_distinct_tasks':len(selected) == 24 and len({x['seed'] for x in selected}) == 24,'all_24_completed':len(outcomes) == 24,'at_least_23_strict_arrivals':sum(x['strict_success'] for x in outcomes) >= 23,'single_at_least_11':classes['single_event'] >= 11,'two_at_least_11':classes['legacy_two'] >= 11,'all_27_physical_audits':len(physical) == 27 and all(x['passed'] for x in physical),'three_matching_cross_scene_repeats':len(repeats) == 3 and all(x['matched'] for x in repeats),'bounded_window_respected':remaining() >= 0,'source_and_protocol_unchanged':all(hashlib.sha256((src/n).read_bytes()).hexdigest() == h for n,h in freeze.items()) and hashlib.sha256((src/'PROTOCOL.md').read_bytes()).hexdigest() == protocol_hash}
    dump(window/'COMPLETION.json',{'status':status,'elapsed_s':time.monotonic()-start,'limit_s':limit,'selected_tasks':len(selected),'completed_confirmation_attempts':len(outcomes),'strict_arrivals':sum(x['strict_success'] for x in outcomes),'class_successes':classes,'repeats_attempted':len(repeats),'remaining_selected_unattempted':[{'seed':x['seed'],'scene':x['scene']} for x in selected[len(outcomes):]],'static_engineering_acceptance_passed':all(checks.values()),'checks':checks,'dynamic_started':False,'training_updates':0,'scope':'finite geometric-reference-eligible static cylinder benchmark; user review required before dynamics'})
    dump(window/'ACTIVE.json',{'status':status,'completed':True})
    print('WINDOW_COMPLETE',status,'accepted',all(checks.values()),flush=True)
