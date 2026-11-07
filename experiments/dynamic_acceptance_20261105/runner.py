"""Sequential frozen workers with immutable absolute budgets and no repair loop."""
import fcntl
import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path
from evidence_rules import AUDITS, FUNCTIONAL_CHECKS, dump, main_gate, read, repeat_check, sha


def run(own):
    repo = own.parents[1]
    config = read(own/'BATCH.json')
    root = repo/config['output']
    root.mkdir(parents=True, exist_ok=True)
    master_lock = (root/'driver.lock').open('a+')
    fcntl.flock(master_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (root/'ROUND_WINDOW.json').exists(), 'BATCH_ALREADY_STARTED_NO_RETRY'
    freeze_hash = sha(own/'CANDIDATE_FREEZE.json')
    freeze = read(own/'CANDIDATE_FREEZE.json')
    def unchanged():
        assert sha(own/'CANDIDATE_FREEZE.json') == freeze_hash
        assert all(sha(repo/n) == h for n,h in freeze['files'].items()), 'FROZEN_SOURCE_CHANGED'
    unchanged()
    assert (repo/'REVIEW_PENDING').exists(), 'PREVIOUS_BATCH_NOT_CLOSED'
    previous = read(repo/config['dependency']/'FINALIZED.json')
    assert previous['development_passed'], 'DEVELOPMENT_DEPENDENCY_NOT_PASSED'
    if config['confirmation']:
        assert previous['combined_three_route_development_passed'], 'ALL_THREE_ROUTES_REQUIRED'
    assert read(repo/'runs/v820_tracked_norm_global/FINALIZED.json')['development_passed']
    execution_lock = repo/'runs/v648_static_unknown/execution.lock'
    with execution_lock.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.time()
    deadline = min(config['absolute_deadline_unix'], started+config['batch_cap_s'])
    assert deadline-started >= config['minimum_start_budget_s'], 'INSUFFICIENT_UNCHANGED_ABSOLUTE_BUDGET'
    guard = (repo/'REVIEW_PENDING').read_bytes()
    (root/'REVIEW_PENDING.before').write_bytes(guard)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    tasks = read(own/'TASK_LIST.json')
    window = root/config['window']
    window.mkdir(exist_ok=False)
    rows, preflights = [], []
    ledger = dict(started_unix=started, absolute_deadline_unix=deadline, campaign_deadline_unix=config['absolute_deadline_unix'],
                  round_closed=False, pid=os.getpid(), attempted_navigation=0, training_updates=0, stage_access=0,
                  real_robot=0, tasks=tasks, source_freeze_sha256=freeze_hash)
    dump(root/'ROUND_WINDOW.json', ledger)
    dump(window/'LOCKED_TASK_LIST.json', tasks)
    dump(window/'SOURCE_FREEZE.json', {p.name: sha(p) for p in own.glob('*.py')})
    dump(window/'DOCUMENT_FREEZE.json', {p.name: sha(p) for p in own.glob('*.md')})
    model = repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'
    env = os.environ.copy()
    env.update(PHASE_RECOVERY_ABLATION='FULL', PHASE_PROPOSAL_MODEL=str(model),
               OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    process = None
    def execute(script, args, log, cap):
        nonlocal process
        unchanged()
        assert time.time()+cap+3 < deadline, 'ABSOLUTE_BUDGET_INSUFFICIENT'
        args = list(map(str, args))
        dump(window/'ACTIVE.json', dict(script=script,args=args,started_unix=time.time(),cap_s=cap,deadline=deadline))
        stage_lock = None
        try:
            if script != 'run_static.py':
                stage_lock = execution_lock.open('rb')
                fcntl.flock(stage_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with log.open('x') as stream:
                process = subprocess.Popen([str(repo/'run_phase.sh'), str(own.relative_to(repo)/script), *args],
                    cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                try:
                    return process.wait(timeout=min(cap,deadline-time.time()))
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid,signal.SIGTERM)
                        try: process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid,signal.SIGKILL)
                            process.wait()
                    process = None
        finally:
            if stage_lock is not None: stage_lock.close()
    def set_task(t):
        env.update(PHASE_COURSE_DISTANCE=str(t['course_distance_m']), PHASE_FIELD_CASE=t['case_id'], PHASE_COURSE_PHASE=str(t['phase']))
    status = 'RUNNING'
    signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(TimeoutError('OUTER_TERMINATED')))
    try:
        (repo/'REVIEW_PENDING').unlink()
        for t in tasks:
            set_task(t)
            name = f"t0_slot{t['slot']:02d}"
            pair = root/name/'paired'
            assert execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',120,'--max-steps',1200,'--initial-observation-steps',0,'--feasibility-only'],window/(name+'.console'),125) == 0, 'T0_INITIALIZATION_FAILED'
            assert execute('audit_field_discovery.py',[pair,'--preflight','--output-dir',pair/'field_preflight'],window/(name+'_audit.console'),90) == 0, 'T0_CAUSAL_AUDIT_FAILED'
            preflights.append(dict(task=t,run=str(pair.relative_to(repo)),causal_audit=str((pair/'field_preflight/INITIAL_UNSEEN_AUDIT_V699.json').relative_to(repo))))
            dump(window/'PREFLIGHTS.json',preflights)
        assert execute('audit_field_preflight.py',[window],window/'noise_audit.console',60) == 0, 'T0_SENSOR_NOISE_FAILED'
        for role in ['MAIN','REPEAT']:
            if role == 'REPEAT':
                assert main_gate(tasks,rows,config['confirmation'])['passed'], 'MAIN_DENOMINATOR_GATE_FAILED'
            chosen = tasks if role == 'MAIN' else [t for t in tasks if t['slot'] in config['repeat_slots']]
            for t in chosen:
                if role == 'REPEAT':
                    base_record = next(x for x in rows if x['role']=='MAIN' and x['task']['slot']==t['slot'])
                    assert base_record['functional_passed'], 'FIXED_REPEAT_BASE_NOT_SUCCESSFUL_NO_REPLACEMENT'
                set_task(t)
                name = ('main' if role=='MAIN' else 'repeat')+f"_slot{t['slot']:02d}"
                pair = root/name/'paired'
                row = dict(name=name,task=t,role=role,run=str(pair.relative_to(repo)),physical_passed=False,functional_passed=False,audits={})
                rows.append(row)
                ledger['attempted_navigation'] += 1
                dump(root/'ROUND_WINDOW.json',ledger)
                dump(window/'RESULTS.json',rows)
                code = execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',1500,'--max-steps',1200,'--initial-observation-steps',0],window/(name+'.console'),1505)
                row['runner_exit'] = code
                row['result'] = read(pair/'geometry_memory/result.json') if (pair/'geometry_memory/result.json').exists() else None
                row['interrupted'] = read(pair/'geometry_memory/interrupted.json') if (pair/'geometry_memory/interrupted.json').exists() else None
                dump(window/'RESULTS.json',rows)
                if row['result'] is not None or (row['interrupted'] or {}).get('public_steps',0)>0:
                    row['replay_exit'] = execute('replay_native_audit.py',[pair],pair/'replay.console',60)
                    dump(window/'RESULTS.json',rows)
                assert code==0 and row['result'] is not None, 'NAVIGATION_INCOMPLETE'
                assert row.get('replay_exit')==0, 'NATIVE_REPLAY_FAILED'
                for script,_,cap in AUDITS:
                    args = [pair]
                    if script=='audit_run.py': args += ['--window',window]
                    if script=='audit_projection_learning.py': args += ['--model',model]
                    code = execute(script,args,pair/(script+'.console'),cap)
                    row['audits'][script] = code
                    dump(window/'RESULTS.json',rows)
                    assert code==0, script+'_FAILED'
                code = execute('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],pair/'discovery_audit.console',240)
                chain = read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')
                failed = [k for k,v in chain['checks'].items() if not v]
                assert not (set(failed)-FUNCTIONAL_CHECKS), 'CAUSAL_EVIDENCE_ANOMALY'
                assert (code==0)==(chain['status']=='PASS'), 'DISCOVERY_AUDIT_EXIT_INCONSISTENT'
                row.update(physical_passed=True,functional_passed=bool(chain['status']=='PASS' and row['result']['strict_safe_arrival']),functional_failed_checks=failed)
                dump(window/'RESULTS.json',rows)
                if role=='REPEAT':
                    assert row['functional_passed'], 'REPEAT_FUNCTIONAL_FAILURE'
                    sys.path.insert(0,str(own))
                    from contact_fingerprint import compare_contacts
                    exact = repeat_check(repo/base_record['run'],pair,base_record['result'],row['result'],compare_contacts)
                    dump(pair/'EXACT_REPEAT_AUDIT.json',exact)
                    assert exact['passed'], 'EXACT_REPEAT_ANOMALY'
                elif not row['functional_passed']:
                    failures = sum(x['role']=='MAIN' and x.get('physical_passed') and not x['functional_passed'] for x in rows)
                    if not config['confirmation'] or failures >= 2:
                        status = 'FUNCTIONAL_NOT_PASSED_STOP'
                        raise StopIteration(status)
        unchanged()
        status = 'FROZEN_TASKS_AND_REPEATS_COMPLETED'
    except StopIteration:
        pass
    except BaseException as error:
        status = 'STOPPED_EXCEPTION'
        dump(window/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
    finally:
        (repo/'REVIEW_PENDING').write_bytes(guard)
        ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started)
        dump(root/'ROUND_WINDOW.json',ledger)
        dump(window/'COMPLETION.json',dict(status=status,records=rows,automatic_additional_navigation=False))
        dump(window/'ACTIVE.json',dict(status=status,completed=True))
    with (root/'finalize.console').open('x') as stream:
        p = subprocess.run([sys.executable,'-B',str(own/'finalize.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
    assert p.returncode==0, 'ZERO_MODEL_FINALIZER_FAILED'
    return read(root/'FINALIZED.json')
