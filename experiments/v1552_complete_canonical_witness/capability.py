"""Explicit nonzero-private capability: absent admission refuses before imports.

No owner/admission is supplied by this preparation. Metadata cannot grant it.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name
SCOPE = 'FIXED_CATALOGUE0_CANONICAL_GEAR_SCALAR_COMPLETE_WITNESSES'
NATIVE_CAP = 1263600


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Guard:
    def __init__(self, *, lock, method_input_sha256, prepared_sources):
        path = O / 'NONZERO_PRIVATE_ADMISSION.json'
        assert path.is_file(), 'CANONICAL_NONZERO_PRIVATE_NOT_ADMITTED'
        self.path = path
        self.authority = read(path)
        self.authority_sha = sha(path)
        self.lock = lock
        self.input_sha = method_input_sha256
        self.source = prepared_sources.copy()
        self.audit_dependency = False
        self.account = {stage:dict(native=0,inflight_unknown=False,Predictor=0,
                                  Engine=0,copy=0,construction_inflight=None)
                        for stage in ('PYTHON_GENERATION', 'CPP_AUDIT')}
        self.check()
        freeze = O / 'SOURCE_FREEZE.json'
        recovery = read(O / 'CURRENT_SOURCE_REMOTE_RECOVERY.json')
        assert read(freeze)['files'] == self.source
        assert self.authority['source_freeze_sha256'] == sha(freeze) == recovery['source_freeze_sha256']
        assert recovery['passed'] and recovery['all_frozen_members_remote_chain_covered']
        assert recovery['uncovered_members'] == []
        assert read(O / 'ENTRY_QUALIFICATION.json')['passed']
        assert (O / 'NUMERIC_ONCE_CLAIM.json').is_file()
        assert all(sha(R/name) == value for name,value in self.source.items())
        parent = read(R / 'runs/v1382_weekend_campaign/LEDGER.json')
        assert parent['active_round'] == C.name and parent['active_math_round'] is None
        assert parent['models_now_authorized'] and parent['scientific_revisions'] == 10

    def check(self):
        a = self.authority
        assert a['scope'] == SCOPE and a['round_id'] == C.name and a['scientific_revision'] == 10
        assert a['models_authorized'] is True and a['physical_authorized'] is False
        assert a['optimizer_authorized'] is False and a['replay_authorized'] is False
        assert a['current_input_sha256'] == self.input_sha
        assert a['generation_native_cap'] == a['success_only_CPP_audit_cap'] == NATIVE_CAP
        assert a['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        assert time.time() < a['absolute_deadline_unix'] <= 1795395600
        assert time.monotonic() < a['hard_stop_monotonic']
        assert sha(self.path) == self.authority_sha, 'NONZERO_PRIVATE_AUTHORITY_CHANGED'
        assert sorted(os.sched_getaffinity(0)) == [2] and os.environ.get('PHASE_REPO') == str(R)
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == '' and os.environ.get('MUJOCO_GL') == 'osmesa'
        assert all(os.environ.get(k) == '1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
        assert Path('/proc/self/fd/'+str(self.lock.fileno())).resolve() == R/'runs/v648_static_unknown/execution.lock'
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def begin(self, stage, kind):
        self.check()
        assert stage in self.account and kind in {'native','Predictor','Engine','copy'}
        if stage == 'CPP_AUDIT':
            assert self.audit_dependency is True, 'NONZERO_SUCCESS_ONLY_AUDIT_NOT_ARMED'
        value = self.account[stage]
        assert not value['inflight_unknown'] and value['construction_inflight'] is None
        if kind == 'native':
            assert value['native'] < NATIVE_CAP, 'NONZERO_PRIVATE_NATIVE_BUDGET'
            value['inflight_unknown'] = True
        else:
            cap = 562 if kind == 'copy' else int((stage,kind) in {('PYTHON_GENERATION','Predictor'),('CPP_AUDIT','Engine')})
            assert value[kind] < cap, 'NONZERO_PRIVATE_CONSTRUCTION_BUDGET'
            value['construction_inflight'] = kind

    def completed(self, stage, kind):
        value = self.account[stage]
        if kind == 'native':
            assert value['inflight_unknown']
            value['native'] += 1
            value['inflight_unknown'] = False
        else:
            assert value['construction_inflight'] == kind
            value[kind] += 1
            value['construction_inflight'] = None

    def counts(self):
        return dict(stages={key:value.copy() for key,value in self.account.items()},
                    internal_Allocator_constructors=None,physical_native=0,replay_native=0,
                    optimizer_calls=0,navigation=False)

    def allow_saved_success_audit(self, path, expected_sha256):
        self.check()
        assert path.resolve() == O/'model/GENERATION.json'
        assert sha(path) == expected_sha256
        result = read(path)
        assert result['passed'] is True and result['closed'] is True
        assert result['first_error'] is None and result['secondary_errors'] == []
        assert result['complete_nominal_native'] == 13600
        assert result['complete_current_prospective_pairs'] == 281
        assert result['all_arrays_saved_before_gates'] is True
        assert result['response_method_sha256'] == self.input_sha
        count = self.account['PYTHON_GENERATION']
        assert result['analytical_native'] == count['native'] == NATIVE_CAP
        assert count['inflight_unknown'] is False and count['construction_inflight'] is None
        assert count['Predictor'] == 1 and count['copy'] == 562
        self.audit_dependency = True
