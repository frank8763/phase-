"""Revision12 private capability; no authority or physical launch creator.

One current-origin proposal, then complete CPP generation and success-dependent
own-output Python audit. Full source checks precede fresh command acquisition.
No copied old certificate/reference grants authority to this method.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
from types import MappingProxyType
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
STAGES=('CPP_PROPOSAL','CPP_GENERATION','PYTHON_AUDIT')


class Guard:
    def __init__(self,*,output,lock,method,prepared_sources,source_owner):
        self.root=Path(output).resolve();assert self.root.is_relative_to(R/'runs')
        self.path=self.root/'GOAL_BOUND_PRIVATE_ADMISSION.json'
        assert self.path.is_file(),'GOAL_BOUND_CURRENT_EVENT_NOT_ADMITTED'
        self.authority=read(self.path);self.identity=sha(self.path);a=self.authority
        assert a['scope']=='REVISION12_SINGLE_GOAL_BOUND_CURRENT_EVENT_PRIVATE'
        assert a['scientific_revision']==12 and a['maximum_events']==1
        assert a['models_authorized']is True
        assert all(a[k]is False for k in ('physical_authorized','replay_authorized','optimizer_authorized','whole_route_admission'))
        assert 0<a['absolute_deadline_unix']-a['started_unix']<=5400
        assert abs((a['hard_stop_monotonic']-a['started_monotonic'])-(a['absolute_deadline_unix']-a['started_unix']))<=1e-5
        self.parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent=read(self.parent_path)
        assert parent['active_round']==a['round_id']and parent['active_math_round']is None
        assert parent['models_now_authorized']and parent['scientific_revisions']==12
        assert a['boot_id']==parent['boot_id']and a['hard_stop_monotonic']<=parent['hard_stop_monotonic']
        self.parent_stat=self.stat(self.parent_path)
        freeze=R/a['source_freeze_path'];recovery=read(R/a['source_recovery_path'])
        assert sha(freeze)==a['source_freeze_sha256']==recovery['source_freeze_sha256']
        assert read(freeze)['files']==prepared_sources
        assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and recovery['uncovered_members']==[]
        qualification=read(R/a['source_qualification_path'])
        assert qualification['passed']and qualification['closed']and qualification['models']==0
        assert all(qualification['source_gates'][k]for k in ('goal_bound_policy','variable_complete_witness',
            'unknown_and_first_error','current_source_runtime_binding','bounded_production_CLI'))
        assert all(sha(R/n)==h for n,h in prepared_sources.items())
        claim=self.root/'NUMERIC_ONCE_CLAIM.json'
        assert sha(claim)==a['once_claim_sha256']and read(claim)['round_id']==a['round_id']
        self.source=MappingProxyType(dict(prepared_sources));self.lock=lock
        self.method=copy.deepcopy(method);self.input_sha=method['response_method_sha256']
        self.owner=source_owner
        resolver=R/a['source_owner_path']
        assert str(resolver.relative_to(R))in self.source
        assert Path(type(source_owner).verify_stopped_source.__code__.co_filename).resolve()==resolver
        self.active_phase=None;self.phases_started=[];self.deadline=None;self.geometry=None
        self.proposal=None;self.generation_result_sha256=None
        p=C/'work.py';assert sha(p)==self.source[str(p.relative_to(R))]
        spec=importlib.util.spec_from_file_location('v1599_private_work',p)
        work=importlib.util.module_from_spec(spec);spec.loader.exec_module(work);self.Work=work.Work
        self.ledgers={'CPP_PROPOSAL':self.Work(native=8200,nominal=8200,witness=0,copies=0,engine=1,predictor=0,batch_calls=0)}
        self.check();self.require_current_event_input(method)

    @staticmethod
    def stat(path):
        s=path.stat();return s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns

    def check(self):
        a=self.authority
        assert sha(self.path)==self.identity and self.stat(self.parent_path)==self.parent_stat
        assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        assert time.time()<a['absolute_deadline_unix']<=1795395600
        assert time.monotonic()<a['hard_stop_monotonic']
        assert time.time()<a['work_deadline_unix']<=a['absolute_deadline_unix']
        assert time.monotonic()<a['work_deadline_monotonic']<=a['hard_stop_monotonic']
        if self.deadline is not None:assert time.time()<self.deadline[0]and time.monotonic()<self.deadline[1]
        assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
        assert os.environ.get('MUJOCO_GL')=='osmesa'and os.environ.get('CUDA_VISIBLE_DEVICES')==''
        assert all(os.environ.get(k)=='1'for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
        assert Path('/proc/self/fd/%d'%self.lock.fileno()).resolve()==R/'runs/v648_static_unknown/execution.lock'
        rows=Path('/proc/self/fdinfo/%d'%self.lock.fileno()).read_text().splitlines()
        assert any(line.startswith('lock:')and 'FLOCK'in line and 'WRITE'in line and str(os.getpid())in line.split()for line in rows)

    def require_current_event_input(self,method):
        self.check();v=copy.deepcopy(method);identity=v.pop('response_method_sha256')
        assert digest(v)==identity==self.input_sha and method==self.method
        assert method['scientific_integration_revision']==12
        assert method['geometry_kind']=='ORIGINAL_CAUSAL_TIME_POLYGONS'
        assert method['base_method']['kind']=='GOAL_BOUND_CURRENT_CANONICAL_EVENT_INPUT'
        # The live resolver re-reads the actual stopped plant and canonical
        # receipt/provider content; a caller-supplied boolean is insufficient.
        self.owner.verify_stopped_source(method)

    def require_timed_geometry_preparation(self):
        self.require_current_event_input(self.method)
        assert not self.phases_started and self.active_phase is None

    def start_phase(self,stage):
        self.require_current_event_input(self.method);assert self.active_phase is None
        assert stage in STAGES and list(STAGES[:len(self.phases_started)])==self.phases_started
        assert stage==STAGES[len(self.phases_started)]and self.geometry is not None
        if stage!='CPP_PROPOSAL':assert self.proposal is not None
        if stage=='PYTHON_AUDIT':assert self.generation_result_sha256 is not None
        self.active_phase=stage;self.phases_started.append(stage)
        seconds=self.authority['phase_seconds'][stage];assert 0<seconds<=2300
        self.deadline=(min(time.time()+seconds,self.authority['absolute_deadline_unix']),
            min(time.monotonic()+seconds,self.authority['hard_stop_monotonic']))

    def finish_phase(self,stage):
        self.check();assert self.active_phase==stage;self.ledgers[stage].idle()
        self.active_phase=None;self.deadline=None

    def require_nominal_proposal_once(self):
        self.check();assert self.active_phase=='CPP_PROPOSAL'
        assert self.ledgers['CPP_PROPOSAL'].value['native']==0
        self.set_bucket('CPP_PROPOSAL','nominal')

    def freeze_proposal(self,proposal,*,path):
        self.require_current_event_input(self.method)
        assert self.active_phase is None and self.phases_started==['CPP_PROPOSAL']and self.proposal is None
        assert read(path)==proposal and proposal['passed']and proposal['closed']
        assert proposal['segment_sha256']==self.method['segment_sha256']
        assert proposal['endpoint_rear_error_m']<=.12+1e-8 and proposal['endpoint_heading_error_rad']<=.20+1e-8
        n=proposal['nominal_native'];assert 2200<=n<=8200 and n%5==0 and proposal['motion_native']==n-2200
        v=self.ledgers['CPP_PROPOSAL'].value;self.ledgers['CPP_PROPOSAL'].idle()
        assert v['native']==v['nominal_native']==n and v['Engine']==1 and v['copy']==v['Predictor']==0
        b=(n-2200)//5+1;native=4400*b+2*n;witness=4400*b+n
        assert native<=self.authority['complete_phase_native_cap']<=5300800
        for stage in ('CPP_GENERATION','PYTHON_AUDIT'):
            self.ledgers[stage]=self.Work(native=native,nominal=n,witness=witness,copies=2*b,
                engine=int(stage=='CPP_GENERATION'),predictor=int(stage=='PYTHON_AUDIT'),
                batch_calls=2*b if stage=='CPP_GENERATION'else 0)
        self.proposal=copy.deepcopy(proposal);self.proposal_sha256=sha(path)

    def require_carrier(self,*,kind,stage,method):
        self.check();assert method==self.method and self.active_phase==stage
        assert (stage,kind)in (('CPP_PROPOSAL','CPP'),('CPP_GENERATION','CPP'),('PYTHON_AUDIT','PYTHON'))

    def require_live_component(self,*args,**kwargs):
        raise RuntimeError('PRIVATE_GOAL_BOUND_CAPABILITY_HAS_NO_ACTUAL_CURRENT_OR_PHYSICAL_AUTHORITY')

    def require_complete_witness(self,proposal,*,stage,kind):
        self.require_carrier(kind=kind,stage=stage,method=self.method)
        assert stage in ('CPP_GENERATION','PYTHON_AUDIT')and proposal==self.proposal

    def set_bucket(self,stage,bucket):
        self.check();assert self.active_phase==stage;self.ledgers[stage].bucket(bucket)

    def begin(self,stage,kind):
        self.check();assert self.active_phase==stage
        if kind=='native':self.ledgers[stage].claim(1)
        else:self.ledgers[stage].construct(kind)

    def completed(self,stage,kind):
        assert self.active_phase==stage
        if kind=='native':self.ledgers[stage].acknowledge(1)
        else:self.ledgers[stage].constructed(kind)

    def require_exact_zero_tail_batch_capability(self,method,*,native_tail):
        self.check();assert native_tail==2200 and self.active_phase=='CPP_GENERATION'
        assert method is None or method==self.method

    def begin_batch(self,stage,kind,count):
        self.require_exact_zero_tail_batch_capability(None,native_tail=2200)
        assert stage==self.active_phase and kind=='native';self.ledgers[stage].claim(count,batch=True)

    def completed_batch(self,stage,kind,count):
        assert stage==self.active_phase and kind=='native';self.ledgers[stage].acknowledge(count,batch=True)

    def require_complete_counts(self,stage,budget):
        self.check();assert stage==self.active_phase
        self.ledgers[stage].complete()
        assert self.ledgers[stage].value['native']==budget['full_phase_native']

    def allow_saved_success_audit(self,*,path,reader):
        self.require_current_event_input(self.method)
        assert self.active_phase is None and self.phases_started==['CPP_PROPOSAL','CPP_GENERATION']
        result=read(path);self.ledgers['CPP_GENERATION'].complete()
        assert result['passed']and result['closed']and result['first_error']is None and result['secondary_errors']==[]
        assert result['response_method_sha256']==self.input_sha
        assert reader.seal['generation_result_sha256']==sha(path)
        assert reader.seal['binding']['response_method_sha256']==self.input_sha
        assert reader.seal['binding']['proposal_sha256']==self.proposal_sha256
        assert reader.seal['binding']['stage']=='CPP_GENERATION'
        self.generation_result_sha256=sha(path)

    def counts(self):
        return dict(stages={k:v.counts()for k,v in self.ledgers.items()},active_phase=self.active_phase,
            phases_started=list(self.phases_started),internal_Allocator_constructors=None,
            physical_native=0,replay_native=0,optimizer_calls=0,whole_route_passed=False)
