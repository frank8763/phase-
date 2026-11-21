"""Narrow once-model authority; no actual-policy or optimizer permission."""
import fcntl
import importlib.util
import os
from pathlib import Path
import time
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1509_response_contract_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def validate(authority,*,parent,limits,boot,now_unix,now_mono,source_identity,input_sha,proposal_sha):
 assert authority['scope']==limits['scope']and authority['models_authorized']is True and authority['physical_authorized']is False and authority['optimizer_authorized']is False,'RESPONSE_SCOPE_CHANGED'
 assert authority['round_id']==parent['active_round']==C.name and parent['models_now_authorized']is True and parent.get('active_math_round')is None,'RESPONSE_PARENT_NOT_ACTIVE'
 assert authority['boot_id']==boot and authority['source_manifest_sha256']==source_identity and authority['current_input_sha256']==input_sha and authority['proposal_sha256']==proposal_sha,'RESPONSE_SOURCE_BOOT_CHANGED'
 assert now_unix<authority['absolute_deadline_unix']<=limits['root_deadline_unix']and now_mono<authority['hard_stop_monotonic']<=parent['hard_stop_monotonic'],'RESPONSE_DOUBLE_CLOCK_EXPIRED'
 for key in ['maximum_nominal_native','generation_native','success_only_audit_native','model_writer_bytes','parent_writer_bytes']:
  assert authority[key]==limits[key],'RESPONSE_LIMITS_CHANGED'
 return True

def admit(lock):
 path=c.O/'RESPONSE_ONLY_ADMISSION.json';assert path.is_file(),'PRIEST_RESPONSE_ONLY_NOT_ADMITTED'
 authority=c.read(path);limits=c.limits();assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 assert all(os.environ.get(k)=='1'for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
 assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==c.R/'runs/v648_static_unknown/execution.lock';fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=c.sources();current,proposal,setup=c.inputs();validate(authority,parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json'),limits=limits,boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),now_unix=time.time(),now_mono=time.monotonic(),source_identity=c.digest(source),input_sha=current['input_sha256'],proposal_sha=proposal['proposal_sha256'])
 assert c.read(c.O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['passed']and(c.O/'NUMERIC_ONCE_CLAIM.json').is_file()
 assert c.read(c.O/'ENTRY_QUALIFICATION.json')['passed']and c.read(c.O/'SOURCE_FREEZE.json')['entry_passed']
 return authority,source,current,proposal,setup

def audit_allowed(generation,*,saved,branch_count):
 return generation.get('passed')is True and generation.get('closed')is True and generation.get('analytical_inflight_unknown')is False and saved is True and generation.get('nominal_native',-1)==branch_count and generation.get('complete_stop_branches',-1)==branch_count and generation.get('analytical_native',-1)==branch_count*201 and branch_count>=200
