"""Narrow stop-only private authority; no nominal/actual/optimizer capability."""
import fcntl
import importlib.util
import os
from pathlib import Path
import time
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1532_contract_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def validate(authority,*,parent,limits,boot,now_unix,now_mono,source_identity,input_sha):
    assert authority['scope']==limits['scope']and authority['models_authorized']is True,'STOP_COMPONENT_SCOPE'
    assert authority['physical_authorized']is False and authority['optimizer_authorized']is False
    assert authority['round_id']==parent['active_round']==C.name and parent['models_now_authorized']is True
    assert parent.get('active_math_round')is None and parent['scientific_revisions']==authority['scientific_revision']==9
    assert authority['boot_id']==boot and authority['source_manifest_sha256']==source_identity and authority['current_input_sha256']==input_sha
    assert now_unix<authority['absolute_deadline_unix']<=limits['root_deadline_unix']and now_mono<authority['hard_stop_monotonic']<=parent['hard_stop_monotonic']
    for key in ['generation_native','success_only_audit_native','maximum_nominal_native','model_writer_bytes','parent_writer_bytes']:
        assert authority[key]==limits[key],'STOP_COMPONENT_LIMIT_CHANGED'
    return True
def admit(lock):
    path=c.O/'STOP_COMPONENT_ADMISSION.json';assert path.is_file(),'CURRENT_ORIGIN_STOP_COMPONENT_NOT_ADMITTED'
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)and os.environ.get('CUDA_VISIBLE_DEVICES')==''
    assert all(os.environ.get(k)=='1'for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
    assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==c.R/'runs/v648_static_unknown/execution.lock';fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    source=c.sources();current,setup=c.inputs();authority=c.read(path)
    validate(authority,parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json'),limits=c.limits(),boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),now_unix=time.time(),now_mono=time.monotonic(),source_identity=c.digest(source),input_sha=current['method_input_sha256'])
    recovery=c.read(c.O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and recovery['uncovered_members']==[]
    assert recovery['source_freeze_sha256']==c.sha(c.O/'SOURCE_FREEZE.json')and(c.O/'NUMERIC_ONCE_CLAIM.json').is_file()
    assert c.read(c.O/'ENTRY_QUALIFICATION.json')['passed']and c.read(c.O/'SOURCE_FREEZE.json')['entry_passed']
    return authority,source,current,setup
def audit_allowed(result,receipt):
    return bool(result['passed']and result['closed']and result['analytical_native']==2200
                and not result['analytical_inflight_unknown']and receipt['complete']and receipt['native']==2200)
def runtime_guard(method,authority,lock,*,phase,completed):
    """Check the actual registered admission at each exposed numerical seam."""
    assert phase in {'CPP_GENERATION','PYTHON_AUDIT'}
    assert type(completed)is int and 0<=completed<2200
    if phase=='CPP_GENERATION':assert completed==0
    assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
    assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==c.R/'runs/v648_static_unknown/execution.lock'
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert c.read(c.O/'STOP_COMPONENT_ADMISSION.json')==authority,'STOP_COMPONENT_AUTHORITY_CHANGED'
    parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
    validate(authority,parent=parent,limits=c.limits(),boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             now_unix=time.time(),now_mono=time.monotonic(),source_identity=authority['source_manifest_sha256'],input_sha=method['method_input_sha256'])
    return True
