"""Absent admission refuses before original carrier/Engine numerical binding.

No admission creator exists in this preparation. A future complete scope is a
new CPP development comparison to the savedV1563 Python stream, not another
generation, current live reserve, physical launch or independent navigation.
"""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
SCOPE='SAVED_V1563_REFERENCE_FULL_NONZERO_CPP_BATCH_WITNESS'
REFERENCE=R/'runs/v1563_lzma_lossless_witness/model/generation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())


class Guard:
    def __init__(self,*,lock,method,prepared_sources):
        path=O/'FULL_CPP_BATCH_ADMISSION.json'
        assert path.is_file(),'FULL_CPP_BATCH_NOT_ADMITTED'
        self.path=path;self.identity=sha(path);self.authority=read(path)
        self.method=method.copy();self.input_sha=method['response_method_sha256']
        self.source=prepared_sources.copy();self.lock=lock
        self.active_phase=None;self.phases_started=[];self.audit_dependency=False
        self.check()
        frozen=O/'SOURCE_FREEZE.json';recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
        assert read(frozen)['files']==self.source
        assert self.authority['source_freeze_sha256']==sha(frozen)==recovery['source_freeze_sha256']
        assert recovery['all_frozen_members_remote_chain_covered']and recovery['uncovered_members']==[]
        assert read(O/'ENTRY_QUALIFICATION.json')['passed']and (O/'NUMERIC_ONCE_CLAIM.json').is_file()
        assert all(sha(R/n)==h for n,h in self.source.items())
        self.reference=REFERENCE
        for name in ['GENERATION.json','STREAM_SEAL.json','WITNESSES.bin']:
            assert sha(REFERENCE/name)==self.authority['saved_reference_sha256'][name]
        result=read(REFERENCE/'GENERATION.json');seal=read(REFERENCE/'STREAM_SEAL.json')
        assert result['passed']and result['closed']and result['first_error']is None and not result['secondary_errors']
        assert result['response_method_sha256']==self.input_sha
        assert result['analytical_native']==1263600 and result['complete_current_prospective_pairs']==281
        assert result['complete_nominal_native']==13600 and result['all_arrays_saved_before_gates']
        assert seal['storage_complete']and seal['data_records']==seal['proof_records']==563
        assert seal['generation_result_sha256']==sha(REFERENCE/'GENERATION.json')
        assert seal['binding']['stage']=='PYTHON_GENERATION'and seal['binding']['response_method_sha256']==self.input_sha
        # Full stream chain/NPZ/13array validation additionally occurs in the
        # existingReader before Engine construction in witness.run.
        self.audit_dependency=True
        p=C/'batch_account.py';assert sha(p)==self.source[str(p.relative_to(R))]
        spec=importlib.util.spec_from_file_location('v1569_batch_account',p)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.ledger=m.WorkLedger();self.account={'CPP_AUDIT':self.ledger.value}

    def check(self):
        a=self.authority
        assert a['scope']==SCOPE and a['round_id']==C.name and a['scientific_revision']==10
        assert a['models_authorized']is True and all(a[k]is False for k in ('physical_authorized','optimizer_authorized','replay_authorized','generation_authorized','live_reserve_authorized'))
        assert a['current_input_sha256']==self.input_sha and a['CPP_native_cap']==1263600
        assert a['maximum_batch_calls']==562 and a['exact_zero_batch_native']==2199
        assert sha(self.path)==self.identity
        parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
        assert parent['active_round']==C.name and parent['active_math_round']is None and parent['models_now_authorized']and parent['scientific_revisions']==10
        assert a['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        assert time.time()<a['absolute_deadline_unix']<=1795395600
        assert time.monotonic()<a['hard_stop_monotonic']<=parent['hard_stop_monotonic']
        if self.active_phase is not None:
            assert time.time()<a['audit_deadline_unix']and time.monotonic()<a['audit_deadline_monotonic']
        assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
        assert os.environ.get('CUDA_VISIBLE_DEVICES')==''and os.environ.get('MUJOCO_GL')=='osmesa'
        assert all(os.environ.get(k)=='1'for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
        assert Path('/proc/self/fd/'+str(self.lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock'
        fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)

    def start_phase(self,stage):
        self.check();assert stage=='CPP_AUDIT'and self.active_phase is None and not self.phases_started and self.audit_dependency
        self.active_phase=stage;self.phases_started.append(stage)

    def set_bucket(self,stage,bucket):
        self.check();assert self.active_phase==stage=='CPP_AUDIT';self.ledger.bucket(bucket)

    def begin(self,stage,kind):
        self.check();assert self.active_phase==stage=='CPP_AUDIT'and self.audit_dependency
        if kind=='native':self.ledger.claim(1)
        else:self.ledger.construct(kind)

    def completed(self,stage,kind):
        assert self.active_phase==stage=='CPP_AUDIT'
        if kind=='native':self.ledger.acknowledge(1)
        else:self.ledger.constructed(kind)

    def require_exact_zero_tail_batch_capability(self,method,*,native_tail):
        self.check();assert self.active_phase=='CPP_AUDIT'and self.audit_dependency and native_tail==2200
        assert method is None or method==self.method
        assert self.ledger.value['batch_calls']<562

    def begin_batch(self,stage,kind,count):
        self.require_exact_zero_tail_batch_capability(None,native_tail=2200)
        assert stage==self.active_phase=='CPP_AUDIT'and kind=='native'
        self.ledger.claim(count,batch=True)

    def completed_batch(self,stage,kind,count):
        assert stage==self.active_phase=='CPP_AUDIT'and kind=='native'
        self.ledger.acknowledge(count,batch=True)

    def counts(self):
        return dict(stages={'CPP_AUDIT':self.ledger.counts()},active_phase=self.active_phase,
            phases_started=self.phases_started.copy(),internal_Allocator_constructors=None,
            physical_native=0,replay_native=0,optimizer_calls=0,
            saved_reference_is_development_input=True,new_generation_native=0,navigation=False)
