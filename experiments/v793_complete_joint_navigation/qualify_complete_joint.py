"""Saved actual-contract selection qualification; no simulator or new forecasts."""
import ast
import hashlib
import json
import signal
import sys
import time
from pathlib import Path
from types import SimpleNamespace
import numpy as np

repo = Path(__file__).resolve().parents[2]
own = Path(__file__).parent
root = repo / 'runs/v793_complete_joint_navigation/pre_navigation'
root.mkdir(parents=True, exist_ok=False)
started = time.time()
deadline = min(started + 300, json.loads((repo / 'RPCCR_GLOBAL_METHOD_REVIEW_AUTHORIZATION_20261104.json').read_text())['absolute_deadline_unix'])
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('QUALIFICATION_ABSOLUTE_STOP')))
signal.setitimer(signal.ITIMER_REAL, deadline - time.time())
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
freeze = read(own / 'CANDIDATE_FREEZE.json')
assert all(sha(repo / p) == h for p, h in freeze['files'].items())
assert read(repo / 'runs/v792_complete_joint_qualification/FINALIZED.json')['evidence_complete']
sys.path.insert(0, str(own))
from joint_admission import admit_ranked
rawroot = repo / 'runs/v792_complete_joint_qualification'
raw = read(rawroot / 'RESULT.json')['records']
cell = repo / 'runs/v791_coherent_global_reference/main_slot01/paired/geometry_memory'
nom = next(json.loads(s) for s in (cell / 'control_decisions.jsonl').read_text().splitlines()
           if json.loads(s)['step'] == 248 and json.loads(s)['candidate_role'] == 'ORDINARY'
           and json.loads(s)['stage'] == 'NOMINAL')
reference = next(json.loads(s) for s in (cell / 'route_revalidation.jsonl').read_text().splitlines()
                 if json.loads(s)['step'] == 248)
path, index = np.asarray(reference['reference_path']), reference['index']
ranked = []
for r in raw:
    c = r['ordinary_candidate']
    trajectory = np.load(rawroot / (r['label'] + '_ORDINARY.npz'))['poses']
    ranked.append((c['score'], np.asarray(c['first_command']), trajectory,
                   c['minimum_clearance_m'], c['self_domain_margin_m']))
cases = []
for mode, expected in [('ACTUAL_RECORDS', 3), ('ALL_REJECT', None), ('LAST_ACTUAL_ACCEPT_ONLY', 12)]:
    class Reserved:
        def __init__(self): self.calls = []
        def admit_nominal(self, real, command, field, state, step):
            i = next(i for i, x in enumerate(ranked) if np.array_equal(x[1], command))
            self.calls.append(i)
            actual = raw[i]
            accept = actual['append_summary'] is not None and mode != 'ALL_REJECT'
            if mode == 'LAST_ACTUAL_ACCEPT_ONLY': accept = accept and i == 12
            self.last_attempt = actual['detail'] if accept or actual['append_summary'] is None else dict(status='NO_APPENDABLE_BACKUP')
            return actual['append_summary'] if accept else None
    reserved = Reserved()
    predictor = SimpleNamespace(ranked_safe_candidates=ranked)
    out = root / mode
    out.mkdir()
    command, gate, summary = admit_ranked(reserved, predictor, None, ranked[0][1].copy(),
                                         nom['summary'], None, None, 248, path, index, out)
    assert reserved.calls == list(range(13 if expected is None else expected + 1))
    assert (summary is None) == (expected is None)
    if expected is not None:
        assert np.array_equal(command, ranked[expected][1])
        assert gate['joint_admission_distinct_command_rank'] == expected
        assert gate['joint_admission_maximum_commands'] == 13
    cases.append(dict(mode=mode, expected_rank=expected, checked_ranks=reserved.calls, passed=True))
reserved = Reserved()
try:
    admit_ranked(reserved, predictor, None, ranked[1][1], nom['summary'], None, None, 248, path, index, out)
except AssertionError:
    assert not reserved.calls
else:
    raise AssertionError('WRONG_TOP_INPUT_WAS_NOT_REJECTED')
skip = root / 'NO_NOMINAL'
skip.mkdir()
assert admit_ranked(reserved, predictor, None, None, {}, None, None, 248, path, index, skip)[2] is None
old = repo / 'experiments/v791_coherent_global_reference'
cores = ['motion_tracker.py', 'geometry_predictor.py', 'reserved_recovery.py', 'discovery_brake.py',
         'retained_reentry.py', 'recovery_supervisor.py', 'future_guide.py', 'control_contract.py',
         'recursive_domain.py', 'risk_domain.py', 'persistent_norm.py', 'renewal_state.py',
         'free_certificate.py', 'self_geometry.py', 'serial_predictor.py']
assert all(sha(own / n) == sha(old / n) for n in cores)
expected = (old / 'joint_admission.py').read_text().replace(
    "assert unique and np.array_equal(unique[0][1],proposal),'RANKING_CHANGED_ORIGINAL_MAXIMUM'",
    "assert unique and len(unique)<=25 and np.array_equal(unique[0][1],proposal),'RANKING_CHANGED_ORIGINAL_MAXIMUM'").replace(
    'enumerate(unique[:3])', 'enumerate(unique)').replace('joint_admission_maximum_commands=3',
                                                       'joint_admission_maximum_commands=len(unique)')
assert (own / 'joint_admission.py').read_text() == expected
assert ast.dump(ast.parse((own / 'run_static.py').read_text())) == ast.dump(ast.parse(
    (old / 'run_static.py').read_text().replace('v791_coherent_global_reference', 'v793_complete_joint_navigation').replace(
        'V791_COHERENT_GLOBAL_REFERENCE', 'V793_COMPLETE_JOINT_ADMISSION')))
assert all(sha(repo / p) == h for p, h in freeze['files'].items())
result = dict(status='COMPLETE_JOINT_SAVED_QUALIFICATION_PASS', cases=cases,
              wrong_top_rejected=True, no_nominal_skip_passed=True, physical_cores_identical=15,
              actual_record_first_joint_rank=3, new_models=0, new_predictions=0, new_integrations=0,
              elapsed_s=time.time()-started)
(root / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
signal.alarm(0)
print(json.dumps(result, indent=2))
