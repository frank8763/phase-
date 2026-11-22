"""One current event's exact private-work authority. No admission creator here.

Full hashes are checked at preparation/closure; the frozen source view and
small authority identities are checked in the callback. No du, source-tree walk
or source-clock reset is added to a fresh command path.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import time
from types import MappingProxyType
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
STAGES=('PYTHON_GENERATION','CPP_AUDIT','CURRENT_CPP_RESERVE')


class EventCapability:
    def __init__(self,*,output,lock,method,prepared_sources,canonical_owner):
        self.root=Path(output).resolve();assert self.root.is_relative_to(R/'runs')
        self.path=self.root/'CURRENT_EVENT_RUNTIME_ADMISSION.json'
        assert self.path.is_file(),'CURRENT_EVENT_RUNTIME_NOT_ADMITTED'
        self.authority=read(self.path);self.identity=sha(self.path)
        a=self.authority
        assert a['scope']=='REVISION11_ORIGINAL_WE_FIRST_CUSP_METHOD_RUNTIME'
        assert a['scientific_revision']==11 and a['maximum_events']==1 and a['event_index']==0
        assert a['models_authorized']is True and a['optimizer_authorized']is False
        assert a['whole_route_admission']is False
        parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent=read(parent_path)
        assert parent['active_round']==a['round_id']and parent['active_math_round']is None
        assert parent['models_now_authorized']is True and parent['scientific_revisions']==11
        assert a['boot_id']==parent['boot_id']
        assert a['hard_stop_monotonic']<=parent['hard_stop_monotonic']
        assert 0<a['absolute_deadline_unix']-a['started_unix']<=5400
        assert abs((a['hard_stop_monotonic']-a['started_monotonic'])-(a['absolute_deadline_unix']-a['started_unix']))<=1e-5
        assert a['generation_native_cap']==a['audit_native_cap']==1263600
        self.parent_path=parent_path
        st=parent_path.stat();self.parent_stat=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
        freeze=R/a['source_freeze_path'];recovery=R/a['source_recovery_path']
        assert sha(freeze)==a['source_freeze_sha256']
        assert read(freeze)['files']==prepared_sources
        remote=read(recovery)
        assert remote['passed']and remote['all_frozen_members_remote_chain_covered']and not remote['uncovered_members']
        assert remote['source_freeze_sha256']==sha(freeze)
        qualification=read(R/a['source_qualification_path'])
        assert qualification['passed']and qualification['closed']and qualification['models']==0
        assert all(qualification['source_gates'][key]for key in ('candidate_and_model_binding',
            'complete_witness_error_paths','current_CPP_reserve_API','actual_receipt_reference_guard','actual_lifecycle_binding'))
        assert all(sha(R/n)==h for n,h in prepared_sources.items())
        self.source=MappingProxyType(dict(prepared_sources));self.lock=lock
        self.method=copy.deepcopy(method);self.input_sha=method['response_method_sha256']
        self.owner=canonical_owner
        assert Path(type(canonical_owner).on_cusp.__code__.co_filename).resolve()==C/'canonical_owner.py'
        self.active_phase=None;self.phases_started=[];self.audit_dependency=False;self.live_dependency=False
        self.phase_deadline=None
        self.account={stage:dict(native=0,nominal_native=0,witness_native=0,bucket=None,
            inflight_unknown=False,inflight_claimed_native=0,inflight_bucket=None,
            Predictor=0,Engine=0,copy=0,construction_inflight=None,batch_calls=0,batch_native=0)
            for stage in STAGES}
        self.current_calls=0
        self.check();self.require_current_event_input(method)

    def check(self):
        a=self.authority
        assert sha(self.path)==self.identity,'CURRENT_RUNTIME_AUTHORITY_CHANGED'
        st=self.parent_path.stat()
        assert (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==self.parent_stat,'ACTIVE_PARENT_CHANGED_DURING_OWNED_METHOD'
        assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        assert time.time()<a['absolute_deadline_unix']<=1795395600
        assert time.monotonic()<a['hard_stop_monotonic']
        if self.phase_deadline is not None:
            assert time.time()<self.phase_deadline[0]and time.monotonic()<self.phase_deadline[1]
        assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
        assert os.environ.get('MUJOCO_GL')=='osmesa'and os.environ.get('CUDA_VISIBLE_DEVICES')==''
        assert all(os.environ.get(k)=='1'for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
        assert Path('/proc/self/fd/%d'%self.lock.fileno()).resolve()==R/'runs/v648_static_unknown/execution.lock'
        rows=Path('/proc/self/fdinfo/%d'%self.lock.fileno()).read_text().splitlines()
        assert any(line.startswith('lock:')and 'FLOCK'in line and 'WRITE'in line and str(os.getpid())in line.split()for line in rows)

    def require_current_event_input(self,method):
        self.check();clean=copy.deepcopy(method);identity=clean.pop('response_method_sha256')
        assert digest(clean)==identity==self.input_sha and method==self.method
        assert method['scientific_integration_revision']==11
        assert method['base_method']['kind']=='REVISION11_CURRENT_EVENT_RESPONSE_INPUT'
        base=method['base_method'];source=base['physical_source']
        assert source['source_role']=='CURRENT_EVENT_SOURCE_AWAITING_RUNTIME_RESOLVER'
        n=self.owner.native
        assert n.vehicle.count==n.applied==base['fixed_origin_native']
        assert n.mode_memory.snapshot(n.applied)==source['mode_history']
        assert dict(gear=n.gear.gear,last_tick=n.gear.last_tick,brake_start=n.gear.brake_start)==source['gear_memory']
        values=dict(time=float(n.vehicle.d.time),**{k:getattr(n.vehicle.d,k).tolist()for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')})
        assert values==source['fullstate'],'ACTUAL_OWNER_CHANGED_DURING_CERTIFICATE'

    def start_phase(self,stage):
        self.check();assert self.active_phase is None and stage in STAGES
        if stage=='PYTHON_GENERATION':assert not self.phases_started
        elif stage=='CPP_AUDIT':assert self.phases_started==['PYTHON_GENERATION']and self.audit_dependency
        else:assert self.phases_started==['PYTHON_GENERATION','CPP_AUDIT']and self.live_dependency
        self.active_phase=stage;self.phases_started.append(stage)
        seconds=self.authority['phase_seconds'][stage]
        assert 0<seconds<=2300 if stage!='CURRENT_CPP_RESERVE'else 0<seconds<=5400
        self.phase_deadline=(min(time.time()+seconds,self.authority['absolute_deadline_unix']),
                             min(time.monotonic()+seconds,self.authority['hard_stop_monotonic']))

    def finish_phase(self,stage):
        self.check();assert self.active_phase==stage
        self.active_phase=None;self.phase_deadline=None

    def set_bucket(self,stage,bucket):
        self.check();assert self.active_phase==stage and bucket in ('nominal','witness')
        v=self.account[stage];assert not v['inflight_unknown']and v['construction_inflight']is None
        v['bucket']=bucket

    def begin(self,stage,kind):
        self.check();assert self.active_phase==stage
        v=self.account[stage];assert not v['inflight_unknown']and v['construction_inflight']is None
        if kind=='native':self._claim(stage,1,False)
        else:
            assert kind in ('Predictor','Engine','copy')
            cap=562 if kind=='copy'and stage!='CURRENT_CPP_RESERVE'else int((stage,kind)in {
                ('PYTHON_GENERATION','Predictor'),('CPP_AUDIT','Engine'),('CURRENT_CPP_RESERVE','Engine')})
            assert v[kind]<cap
            v['construction_inflight']=kind

    def completed(self,stage,kind):
        assert self.active_phase==stage
        if kind=='native':self._ack(stage,1,False)
        else:
            v=self.account[stage];assert v['construction_inflight']==kind
            v[kind]+=1;v['construction_inflight']=None

    def _claim(self,stage,count,batch):
        self.check();v=self.account[stage]
        assert type(count)is int and count==(2199 if batch else 1)
        assert not v['inflight_unknown']and v['construction_inflight']is None
        bucket=v['bucket'];assert bucket in ('nominal','witness')and (not batch or bucket=='witness')
        total=1263600 if stage!='CURRENT_CPP_RESERVE'else 2200*self.authority['maximum_current_reserve_calls']
        assert 0<self.authority['maximum_current_reserve_calls']<=13800
        assert v['native']+count<=total
        cap=(13600 if bucket=='nominal'else 1250000)if stage!='CURRENT_CPP_RESERVE'else total
        assert v[bucket+'_native']+count<=cap
        v.update(inflight_unknown=True,inflight_claimed_native=count,inflight_bucket=bucket)

    def _ack(self,stage,count,batch):
        v=self.account[stage];assert v['inflight_unknown']and v['inflight_claimed_native']==count
        v['native']+=count;v[v['inflight_bucket']+'_native']+=count
        if batch:v['batch_calls']+=1;v['batch_native']+=count
        v.update(inflight_unknown=False,inflight_claimed_native=0,inflight_bucket=None)

    def require_exact_zero_tail_batch_capability(self,method,*,native_tail):
        self.check();assert native_tail==2200 and self.active_phase in ('CPP_AUDIT','CURRENT_CPP_RESERVE')
        assert method is None or method==self.method
        if self.active_phase=='CPP_AUDIT':assert self.audit_dependency
        else:assert self.live_dependency

    def begin_batch(self,stage,kind,count):
        self.require_exact_zero_tail_batch_capability(None,native_tail=2200)
        assert stage==self.active_phase and kind=='native';self._claim(stage,count,True)

    def completed_batch(self,stage,kind,count):
        assert stage==self.active_phase and kind=='native';self._ack(stage,count,True)

    def allow_saved_success_audit(self,path,expected_sha256):
        self.require_current_event_input(self.method)
        assert sha(path)==expected_sha256
        result=read(path);v=self.account['PYTHON_GENERATION']
        assert result['passed']and result['closed']and result['first_error']is None and not result['secondary_errors']
        assert result['response_method_sha256']==self.input_sha
        assert result['analytical_native']==v['native']==1263600
        assert result['complete_nominal_native']==13600 and result['complete_current_prospective_pairs']==281
        assert v['Predictor']==1 and v['copy']==562 and not v['inflight_unknown']and v['construction_inflight']is None
        self.generation_result_sha256=expected_sha256
        self.audit_dependency=True

    def arm_current_runtime(self,*,audit_path,audit_sha256,certificate_path,certificate_sha256):
        self.require_current_event_input(self.method)
        assert self.phases_started==['PYTHON_GENERATION','CPP_AUDIT']and self.active_phase is None
        assert sha(audit_path)==audit_sha256 and sha(certificate_path)==certificate_sha256
        result=read(audit_path);certificate=read(certificate_path);v=self.account['CPP_AUDIT']
        assert result['passed']and result['closed']and not result['first_error']and not result['secondary_errors']
        assert result['response_method_sha256']==self.input_sha==certificate['response_method_sha256']
        assert result['analytical_native']==v['native']==1263600 and v['Engine']==1 and v['copy']==562
        assert result['complete_nominal_native']==13600 and result['complete_current_prospective_pairs']==281
        assert v['batch_calls']==562 and v['batch_native']==1235838
        assert not v['inflight_unknown']and v['construction_inflight']is None
        assert certificate['generation_result_sha256']==self.generation_result_sha256
        assert certificate['audit_result_sha256']==audit_sha256
        assert certificate['complete_streams_verified_before_current_execution']is True
        assert certificate['original_segment_endpoint_passed']is True
        self.certificate_sha256=certificate_sha256;self.live_dependency=True

    def require_current_reserve_source(self,packet,memory,gear):
        self.check();assert self.active_phase=='CURRENT_CPP_RESERVE'and self.live_dependency
        base=self.method['base_method'];tick=packet['native_tick'];n=self.owner.native
        assert n.applied==n.vehicle.count==tick and not n.in_step
        assert memory['epoch_native']==base['fixed_origin_native']<=tick<=base['fixed_origin_native']+13800
        assert memory['covered_native']==tick and memory['response_method_sha256']==self.input_sha
        assert memory['actual_sensor_claim']is False and type(memory['steering_load_episode'])is bool
        assert memory['complete_applied_receipt_coverage']is True
        assert gear==dict(gear=n.gear.gear,last_tick=n.gear.last_tick,brake_start=n.gear.brake_start)
        assert gear['last_tick']==tick-1
        modes=n.mode_memory.snapshot(tick)
        assert all(packet[key]==modes[key]for key in ('coupled_episode','steering_motion_active','parked_target'))
        assert packet['steering']['native_tick']==tick and packet['steering']['measured_at']==packet['body_measured_at']
        assert abs(packet['sim_time']-(base['fixed_origin_sim_time']+.01*(tick-base['fixed_origin_native'])))<=1e-8
        assert self.current_calls<self.authority['maximum_current_reserve_calls']
        self.current_calls+=1
        self.set_bucket('CURRENT_CPP_RESERVE','witness')

    def counts(self):
        return dict(stages=copy.deepcopy(self.account),active_phase=self.active_phase,
            phases_started=list(self.phases_started),current_calls=self.current_calls,
            internal_Allocator_constructors=None,physical_native=0,replay_native=0,optimizer_calls=0)
