"""One fresh complete repeat only; baseline main is read-only, never rerun."""
import sys, os, json, time, signal, subprocess, hashlib, fcntl, traceback
from pathlib import Path

R = Path(__file__).resolve().parents[2]
CORE = R / 'experiments/rpccr_execution_core'
sys.path.insert(0, str(CORE))
from fresh_campaign import same_complete

def dump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, allow_nan=False, indent=2)+'\n')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def temporary_bytes():
    seen = set()
    total = 0
    for base, dirs, names in os.walk(R/'runs', followlinks=False):
        dirs[:] = [d for d in dirs if not Path(base, d).is_symlink()]
        for name in names:
            p = Path(base, name)
            if p.is_symlink():
                continue
            s = p.stat()
            key = s.st_dev, s.st_ino
            if key not in seen:
                seen.add(key)
                total += s.st_size
    return total

def main():
    assert len(sys.argv) == 2 and Path(sys.argv[1]).is_absolute()
    cfg = json.loads(Path(sys.argv[1]).read_text())
    O = Path(cfg['run_root'])
    guard = (R/'REVIEW_PENDING').read_bytes()
    assert hashlib.sha256(guard).hexdigest() == '4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((O/'AUTHORIZATION.json').read_text())['models_authorized']
    assert json.loads((O/'QUALIFICATION.json').read_text())['passed']
    freeze = json.loads(Path(cfg['source_freeze']).read_text())['files']
    assert all(sha(R/p) == h for p, h in freeze.items())
    baseline_manifest = json.loads((O/'BASELINE_MANIFEST.json').read_text())
    assert all(sha(R/p) == h for p, h in baseline_manifest['files'].items())
    baseline = json.loads((O/'BASELINE_TASK.json').read_text())
    audit = json.loads(Path(cfg['baseline_audit']).read_text())
    assert audit['passed'] and all(audit['checks'].values())
    tasks = json.loads(Path(cfg['task_table']).read_text())
    assert len(tasks) == 1 and tasks[0]['kind'] == 'repeat'
    task = tasks[0]
    for key in ['case_id', 'seed', 'phase', 'dynamic', 'start_xy', 'start_yaw', 'goal_xy', 'goal_yaw', 'course_id', 'run_id', 'target', 'speed', 'stop_native', 'historical_prefix_native']:
        assert task[key] == baseline[key], key
    assert temporary_bytes()+400*1024**2 <= 2*1024**3, 'TEMPORARY_BUDGET'
    own = (O/'driver.lock').open('a+')
    fcntl.flock(own, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with (R/'runs/v648_static_unknown/execution.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (O/'ROUND_WINDOW.json').exists() and not Path(task['output']).exists()
    wall, mono = time.time(), time.monotonic()
    window = dict(started_unix=wall, started_monotonic=mono,
                  absolute_deadline_unix=wall+5400, hard_stop_monotonic=mono+5400,
                  duration_s=5400, old_windows_unchanged=True)
    dump(O/'ROUND_WINDOW.json', window)
    (O/'GUARD.bin').write_bytes(guard)
    dump(O/'APPROVAL.json', dict(models_authorized=True,
         absolute_deadline_unix=window['absolute_deadline_unix'], allowed_task_ids=[task['task_id']]))
    attempted, rows, pair, error, child = [], [], None, None, None

    def halt(*_):
        raise TimeoutError('ROOT_DEADLINE_OR_STOP')

    def remaining():
        return min(window['absolute_deadline_unix']-time.time(), window['hard_stop_monotonic']-time.monotonic())

    def stop_child():
        nonlocal child
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=3)
            except BaseException:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=3)
                except ProcessLookupError:
                    pass
        child = None

    signal.signal(signal.SIGTERM, halt)
    signal.signal(signal.SIGALRM, halt)
    signal.setitimer(signal.ITIMER_REAL, max(.001, remaining()))
    try:
        assert remaining() > 2000
        path = O/(task['task_id']+'.json')
        dump(path, task)
        attempted.append(task['task_id'])
        dump(O/'ATTEMPTS.json', attempted)
        (R/'REVIEW_PENDING').unlink()
        try:
            with (O/(task['task_id']+'.console')).open('x') as log:
                child = subprocess.Popen([str(R/'run_phase.sh'),
                    str(Path(cfg['worker_path']).relative_to(R)), str(path)],
                    cwd=R, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                dump(O/'ACTIVE.json', dict(pid=child.pid, task_id=task['task_id'], stage='navigation'))
                code = child.wait(timeout=min(905, remaining()-20))
        finally:
            stop_child()
            (R/'REVIEW_PENDING').write_bytes(guard)
        out = Path(task['output'])
        rp = out/'RESULT.json'
        if not rp.exists():
            rp = out/'physics/paired/ENTRY_FAILURE_RESULT.json'
        result = json.loads(rp.read_text()) if rp.exists() else dict(passed=False, missing_result=True)
        row = dict(task=task, result=result, returncode=code)
        rows.append(row)
        dump(O/'RESULTS.json', rows)
        assert code == 0 and result['passed'], 'FIRST_FUNCTIONAL_OR_SAFETY_FAILURE'
        dump(O/'ACTIVE.json', dict(task_id=task['task_id'], stage='zero_model_full_audit'))
        with (O/(task['task_id']+'.audit.console')).open('x') as log:
            child = subprocess.Popen([sys.executable, '-B', cfg['audit_path'], str(path)],
                cwd=R, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            dump(O/'ACTIVE.json', dict(pid=child.pid, task_id=task['task_id'], stage='zero_model_full_audit'))
            code = child.wait(timeout=min(900, remaining()-20))
        stop_child()
        assert code == 0, 'FIRST_INDEPENDENT_EVIDENCE_FAILURE'
        row['audit'] = json.loads((out/'FINAL_INDEPENDENT_AUDIT.json').read_text())
        assert row['audit']['passed']
        dump(O/'RESULTS.json', rows)
        assert all(sha(R/p) == h for p, h in baseline_manifest['files'].items())
        pair = same_complete(baseline, task)
        dump(O/'COMPLETE_REPEAT.json', pair)
        assert pair['passed']
    except BaseException as e:
        error = dict(error=repr(e), traceback=traceback.format_exc())
        dump(O/'ERROR.json', error)
    finally:
        stop_child()
        (R/'REVIEW_PENDING').write_bytes(guard)
        dump(O/'APPROVAL.json', dict(models_authorized=False, closed=True))
        dump(O/'AUTHORIZATION.json', dict(models_authorized=False, closed=True,
             original_user_authorization='很好，下一步开始，加油', no_automatic_extension=True))
        dump(O/'ACTIVE.json', dict(closed=True))
        signal.setitimer(signal.ITIMER_REAL, 0)
    passed = error is None and pair is not None and pair['passed']
    keys = ['vehicle_initializations', 'historical_replay_native', 'new_actual_native',
            'own_replay_native', 'replay_state_initializations', 'private_mujoco_native',
            'training_updates', 'analytical_prediction_native']
    counts = {k:sum(row['result'][k] for row in rows) if rows and all(row['result'].get(k) is not None for row in rows) else None for k in keys}
    summary = dict(closed=True, passed=passed, version=cfg['version'],
        scope='One fresh complete NS repeat against saved independently supplementally audited V1085_entry main',
        attempted=attempted, unexecuted=[t['task_id'] for t in tasks if t['task_id'] not in attempted],
        error=error, complete_repeat=pair, counts=counts, new_main_samples=0,
        baseline_main_reexecuted=False, baseline_original_failed_batch_preserved=True,
        source_unchanged=all(sha(R/p) == h for p, h in freeze.items()),
        guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,
        whole_route_passed=passed, new24_executed=False)
    assert summary['guard_original']
    if not summary['source_unchanged']:
        summary['passed'] = summary['whole_route_passed'] = False
        summary['source_error'] = 'SOURCE_CHANGED'
    dump(O/'COMPLETION.json', summary)
    x = json.loads((R/'CURRENT_EXPERIMENT.json').read_text())
    x.update(status='REVIEW_PENDING', active_run=None, active_window=None, active_entrypoint=None,
             next_physical_authorized=False, latest_completed=summary, latest_report=cfg['report'],
             next_scope='Review closed NS repeat and verified archive; no automatic additional model task')
    dump(R/'CURRENT_EXPERIMENT.json', x)
    (R/cfg['report']).write_text('# V1086 NS full-repeat result\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\nOld V1085 entry/audit failures preserved. No three-route/24 acceptance or real-time claim.\n')
    with (R/'RESEARCH_STATUS.md').open('a') as f:
        f.write('\n- FINAL V1086 NS完整重复：passed='+str(summary['passed'])+'；新增分账='+json.dumps(counts)+'；旧主未重跑，三路线/24未执行。见'+cfg['report']+'。\n')
    print(json.dumps(summary), flush=True)
    try:
        with (O/'closure.console').open('x') as log:
            q = subprocess.run([sys.executable, '-B', str(CORE/'close_local.py'), str(O/'CONFIG.json')],
                cwd=R, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        dump(O/'ARCHIVE_RESULT.json', dict(returncode=q.returncode, models=0, raw_retained=True))
    except BaseException as e:
        dump(O/'ARCHIVE_RESULT.json', dict(error=repr(e), models=0, raw_retained=True))

if __name__ == '__main__':
    main()
