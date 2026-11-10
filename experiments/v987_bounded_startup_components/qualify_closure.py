"""Real owned-process failure injection and bounded root-cutoff checks; zero models."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

C = Path(__file__).parent
R = C.resolve().parents[1]
O = R/'runs/v987_bounded_startup_components'
sys.path.insert(0, str(C))
from closure import accounting_receipt, request_stop, stop_requested, supervise_workers
from types import SimpleNamespace as S


def exercise(name, hung=False, root_timeout=False, initial_failure=False):
    out = O/name
    out.mkdir()
    jobs = []
    try:
        wrapper = subprocess.Popen([sys.executable, str(C/'process_fixture.py'), 'wrapper_hung' if hung else 'wrapper', str(out)], start_new_session=True)
        jobs.append(wrapper)
        until = time.monotonic()+3
        while not (out/'READY').exists():
            assert wrapper.poll() is None and time.monotonic() < until
            time.sleep(.005)
        if not root_timeout and not initial_failure:
            jobs.append(subprocess.Popen([sys.executable, str(C/'process_fixture.py'), 'ros_failure', str(out)], start_new_session=True))
        start = time.monotonic()
        root = time.time()+(1.35 if root_timeout else 10.)
        proof = supervise_workers(jobs, out, name, start+5., root,
                                  closure_grace_s=.3 if hung else 2.,
                                  initial_failure=dict(reason='FIXTURE_PARENT_EXCEPTION') if initial_failure else None)
        elapsed = time.monotonic()-start
        saved = (out/'NATIVE_SAVED.json').exists()
        assert not proof['passed'] and all(p.poll() is not None for p in jobs)
        assert proof['closed_monotonic'] <= proof['hard_stop_monotonic']+.2
        if hung:
            assert not saved and proof['forced_process_groups'] and elapsed < 2.
        elif root_timeout:
            assert proof['failure']['reason'] == 'TASK_OR_ROOT_DEADLINE' and elapsed < 1.
        else:
            assert saved and not proof['forced_process_groups']
        return dict(name=name, passed=True, saved_native_fixture=saved, elapsed_s=elapsed, proof=proof)
    finally:
        for p in jobs:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait(timeout=2)


def main():
    cases = [exercise('ros_failure_preserves_native'), exercise('parent_exception_preserves_native', initial_failure=True),
             exercise('hung_worker_bounded', hung=True), exercise('root_deadline_not_extended', hung=True, root_timeout=True)]
    checks = dict(real_owned_wrapper_child_tests=all(row['passed'] for row in cases))
    task = dict(origin_native_tick=6083)
    n = accounting_receipt(S(count=6199), S(native_completed=116, native_integration_uncertain=False), task,
                           dict(environment_initialization_completed=True), 'FAILED')
    checks['known_historical_and_new_counts_separate'] = n['actual_native_exact'] == 6199 and n['new_branch_native_exact'] == 116 and n['historical_restore_native'] == 6083
    unknown = accounting_receipt(S(count=6199), S(native_completed=116, native_integration_uncertain=True), task, {}, 'FAILED')
    checks['interrupted_integration_total_unknown'] = unknown['actual_native_exact'] is None and unknown['new_branch_native_exact'] is None and unknown['new_branch_native_observed_lower_bound'] == 116
    mismatch = accounting_receipt(S(count=6200), S(native_completed=116), task, {}, 'FAILED')
    checks['mismatched_return_and_recorded_count_unknown'] = mismatch['actual_native_exact'] is None and mismatch['count_status'] == 'RETURN_AND_RECORDED_COUNT_MISMATCH'
    checks['replay_not_inferred_zero'] = all(x['own_full_trace_replay_native_exact'] is None for x in [n,unknown,mismatch])
    negative = O/'foreign_stop'
    negative.mkdir()
    request_stop(negative, 'one', 'FIXTURE')
    try:
        stop_requested(negative, 'two')
    except AssertionError as e:
        checks['foreign_run_stop_rejected'] = str(e) == 'FOREIGN_PARENT_STOP_REQUEST'
    else:
        checks['foreign_run_stop_rejected'] = False
    result = dict(passed=all(checks.values()), checks=checks, cases=cases,
                  known_accounting=n, interrupted_accounting=unknown, mismatch_accounting=mismatch,
                  models=0, integrations=0, fixtures_not_physical_evidence=True)
    (O/'CLOSURE_QUALIFICATION.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    assert result['passed']


if __name__ == '__main__':
    main()
