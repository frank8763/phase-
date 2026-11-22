"""Current2200 reserve authority and source-origin proof; no numerical imports."""
import copy
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
MODEL='V1159_BOUNDED_STEERING_LOAD_OVER_V1114'
FEEDBACK='CURRENT_BRANCH_SCALAR_AFTER_MEASURED_ORIGIN'
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

class SourceRefusal(RuntimeError):
    def __init__(self,first,proof,secondary=None):
        super().__init__(first);self.proof=proof;self.secondary=secondary

def source_proof(method,packet,memory,gear,*,save_proof,source_role):
    """Save malformed/current-source refusal before raising; no model rights."""
    proof=dict(passed=False,physical_permission=False,models_authorized=False,first_error=None,
        source_role=source_role,checks={},method_memory_is_not_sensor=True)
    first=None
    try:
        clean=copy.deepcopy(method);identity=clean.pop('response_method_sha256')
        assert digest(clean)==identity
        base=method['base_method'];origin=base['fixed_origin_native'];native=packet['native_tick']
        def check(k,value):
            proof['checks'][k]=bool(value)
            assert value,k
        check('declared_revision10_model',method['scientific_integration_revision']==10 and method['model_variant']==MODEL)
        check('fixed_fullperiod_geometry',method['geometry_kind']=='FULL_PERIOD_DISK')
        check('registered_source_role',source_role=='SAVED_CURRENT_SOURCE_ONLY')
        check('fixed_clock',type(native)is int and origin<=native<=origin+13600 and abs(packet['sim_time']-(base['fixed_origin_sim_time']+.01*(native-origin)))<=1e-8)
        check('explicit_current_epoch',memory['epoch_native']==origin and memory['covered_native']==native and type(memory['steering_load_episode'])is bool)
        check('method_not_sensor',memory['actual_sensor_claim']is False and memory['response_method_sha256']==identity)
        check('method_coverage',memory['complete_applied_receipt_coverage']is True and isinstance(memory['chain_sha256'],str)and len(memory['chain_sha256'])==64)
        check('no_entry_epoch_reset',native!=origin or memory['steering_load_episode']is False and memory['chain_sha256']=='0'*64)
        check('current_gear_clock',gear['last_tick']==native-1 and type(gear['gear'])is int and gear['gear']in(-1,0,1))
        check('current_gear_brake',gear['brake_start']is None or type(gear['brake_start'])is int and 0<=gear['brake_start']<native)
        values=[*packet['body'],packet['body_lateral'],*packet['steering']['position'],*packet['steering']['velocity'],*packet['controller_memory']['last_ctrl'],packet['controller_memory']['integral']]
        check('measured_values_finite',len(packet['body'])==5 and len(packet['steering']['position'])==len(packet['steering']['velocity'])==2 and len(packet['controller_memory']['last_ctrl'])==4 and all(type(v)in(int,float)and math.isfinite(v)for v in values))
        check('measured_source_metadata',packet['steering']['native_tick']==native and packet['steering']['measured_at']==packet['body_measured_at'])
        check('current_mode_explicit',type(packet['coupled_episode'])is bool and type(packet['steering_motion_active'])is bool and (not packet['steering_motion_active']or packet['coupled_episode']) and (packet['parked_target']is not None)==packet['steering_motion_active'])
        proof.update(passed=True,source_packet_sha256=digest(packet),method_memory_sha256=digest(memory),gear_memory_sha256=digest(gear),
            complete_source=copy.deepcopy(packet),current_method_memory=copy.deepcopy(memory),current_gear_memory=copy.deepcopy(gear),
            response_method_sha256=identity,model_variant=MODEL,feedback=FEEDBACK,native=native)
    except BaseException as error:
        first='CURRENT2200_ORIGIN_SOURCE_REFUSED:'+repr(error);proof.update(passed=False,first_error=first)
    secondary=None
    try:save_proof(proof)
    except BaseException as error:secondary=repr(error)
    if first or secondary:raise SourceRefusal(first or 'CURRENT2200_ORIGIN_PROOF_SAVE_FAILED',proof,secondary)
    return proof

class Guard:
    """Absent new reserve admission refuses before binding any numerical code.

    This source-only target deliberately supplies no admission creator. A later
    qualified owner must bind a distinct finite numerical scope and source chain.
    SourceRole FRESH/physical remains refused by source_proof until separately
    qualified current capture and its explicit source contract exist.
    """
    def __init__(self,*,method,lock,prepared_sources,save_origin,save_proof,save_secondary):
        path=O/'CURRENT_RESERVE_ONLY_ADMISSION.json'
        assert path.is_file(),'CURRENT2200_RESERVE_NOT_ADMITTED'
        a=json.loads(path.read_text())
        assert a['scope']=='CURRENT_CANONICAL2200_RESERVE_ONLY'and a['models_authorized']is True
        assert a['physical_authorized']is False and a['optimizer_authorized']is False and a['replay_authorized']is False
        assert a['round_id']==C.name and a['response_method_sha256']==method['response_method_sha256']
        assert a['maximum_native']>=2200 and a['maximum_native']%2200==0
        assert a['maximum_predictor_constructions']*2200==a['maximum_native']
        freeze=O/'SOURCE_FREEZE.json';recovery=O/'CURRENT_SOURCE_REMOTE_RECOVERY.json'
        assert sha(freeze)==a['source_freeze_sha256']
        assert json.loads(freeze.read_text())['files']==prepared_sources
        assert json.loads(recovery.read_text())['source_freeze_sha256']==sha(freeze)
        assert json.loads(recovery.read_text())['all_frozen_members_remote_chain_covered']is True
        assert all(sha(R/n)==h for n,h in prepared_sources.items())
        self.path=path;self.identity=sha(path);self.authority=a;self.source=prepared_sources.copy();self.source_identity=digest(prepared_sources)
        self.method=copy.deepcopy(method);self.lock=lock;self.save_origin=save_origin;self.save_proof=save_proof;self.save_secondary=save_secondary
        self.work=dict(native=0,Predictor=0,native_inflight_unknown=False,construction_inflight=None,internal_Allocator_constructors=None)
        self.current=None
        self.check()

    def check(self):
        a=self.authority
        assert sha(self.path)==self.identity
        parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
        assert parent['active_round']==a['round_id']and parent['models_now_authorized']and parent['scientific_revisions']==10
        assert parent['active_math_round']is None
        assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
        assert os.environ.get('CUDA_VISIBLE_DEVICES')==''and os.environ.get('MUJOCO_GL')=='osmesa'
        assert all(os.environ.get(k)=='1'for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
        assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()==parent['boot_id']
        assert time.time()<a['absolute_deadline_unix']<=1795395600
        assert time.monotonic()<a['hard_stop_monotonic']<=parent['hard_stop_monotonic']
        assert Path('/proc/self/fd/'+str(self.lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock'
        fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert digest(self.source)==self.source_identity

    def require_current_reserve_components(self,method,*,complete_native):
        self.check();assert complete_native==2200 and digest(method)==digest(self.method)

    def require_current_reserve(self,method,packet,memory,gear,*,native_cap):
        self.require_current_reserve_components(method,complete_native=native_cap)
        assert self.work['native']+2200<=self.authority['maximum_native']
        assert self.work['Predictor']<self.authority['maximum_predictor_constructions']
        self.current=source_proof(method,packet,memory,gear,save_proof=self.save_proof,source_role=self.authority['origin_role'])
        assert self.current['source_packet_sha256']==self.authority['source_packet_sha256']
        assert self.current['method_memory_sha256']==self.authority['method_memory_sha256']

    def save_current_origin_before_construction(self,origin,packet,memory,gear):
        assert self.current is not None and digest(packet)==self.current['source_packet_sha256']
        proof=dict(source=self.current,origin={k:v.tolist()if hasattr(v,'tolist')else copy.deepcopy(v)for k,v in origin.items()},model_counts=self.counts(),construction_for_this_origin_started=False)
        self.save_origin(proof)

    def begin(self,stage,kind):
        self.check();assert stage=='CURRENT_RESERVE'and kind in ('native','Predictor')
        assert not self.work['native_inflight_unknown']and self.work['construction_inflight']is None
        if kind=='native':
            assert self.work['native']<self.authority['maximum_native'];self.work['native_inflight_unknown']=True
        else:
            assert self.work['Predictor']<self.authority['maximum_predictor_constructions'];self.work['construction_inflight']=kind

    def completed(self,stage,kind):
        assert stage=='CURRENT_RESERVE'
        if kind=='native':
            assert self.work['native_inflight_unknown'];self.work['native']+=1;self.work['native_inflight_unknown']=False
        else:
            assert kind=='Predictor'and self.work['construction_inflight']==kind
            self.work['Predictor']+=1;self.work['construction_inflight']=None

    def counts(self):return dict(self.work,physical_native=0,replay_native=0,optimizer_calls=0)
    def save_after_gate(self,proof,saved):self.save_proof(dict(proof=proof,saved_array_receipt=saved,model_counts=self.counts()))
    def save_secondary_failure(self,failure):self.save_secondary(failure)
