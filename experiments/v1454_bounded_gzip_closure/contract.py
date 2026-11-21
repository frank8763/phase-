"""A distinct zero200 qualification admits no route, scan or private model."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
GATES={'no_admission_before_physical_import','original_zero_tail_seam_exact','bootstrap_stage_and_native_caps','compute_stage_and_private_model_refusal','first_error_unknown_and_secondary_saves','bounded_shared_dual_clock','canonical_source_and_storage','once_claim_before_factory'}
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def prerequisite_hashes():
 paths=['runs/v1447_full_module_guard_identity/COMPLETION.json','runs/v1447_full_module_guard_identity/CLOSED_REVIEW.json','runs/v1447_full_module_guard_identity/FULL_REMOTE_VERIFIED.json','runs/v1449_route_initializer_binding/BINDING_QUALIFICATION.json']
 for p in paths:
  v=read(R/p);assert v.get('passed',v.get('passed_initializer_scope'))is True,'ZERO200_PREREQUISITE_NOT_PASSED:'+p
 assert read(R/paths[0])['native']['actual_native']==0
 return {p:sha(R/p)for p in paths}
def storage_preflight():
 limits=read(C/'LIMITS.json');used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],text=True,timeout=10).split()[0])
 future=sum(limits[k]for k in ['maximum_task_evidence_bytes','archive_reserve_bytes','download_reserve_bytes','root_reserve_bytes'])+4*1024**2
 assert used+future<limits['storage_limit_bytes'],'ZERO200_ALL_RUNS_PEAK_REFUSED'
 return dict(allocated_all_runs_bytes=used,estimated_peak_bytes=used+future,limit_bytes=limits['storage_limit_bytes'],parent_console_hold_bytes=4*1024**2,inode_accounted=True)
def check_window(w,parent):
 assert w['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert 0<w['absolute_deadline_unix']-w['started_unix']<=600
 assert w['absolute_deadline_unix']<=1795395600 and w['hard_stop_monotonic']<=parent['hard_stop_monotonic']
 assert abs((w['hard_stop_monotonic']-w['started_monotonic'])-(w['absolute_deadline_unix']-w['started_unix']))<1e-5
 assert min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())>30

def admit(task,approval,window):
 path=O/'ZERO200_ONLY_ADMISSION.json'
 if not path.is_file():raise RuntimeError('ZERO200_PREMODEL_ENTRY_ADMISSION_MISSING')
 q=read(path);assert q['zero200_only_admission']is True and q['physical_route_admission']is False
 assert set(q['entry_gates'])==GATES and all(q['entry_gates'].values())
 assert q['limits']==read(C/'LIMITS.json')and q['prerequisite_hashes']==prerequisite_hashes()
 assert q['source_hashes']and all(sha(R/p)==h for p,h in q['source_hashes'].items())
 assert approval['scope']==q['limits']['scope']and approval['models_authorized']is True and approval['qualification_sha256']==sha(path)
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']==approval['round_id']==C.name+'_zero200'and parent['models_now_authorized']
 check_window(window,parent)
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 assert not(R/'REVIEW_PENDING').exists()
 original=read(R/'experiments/v1439_actual_ros_startup_close/TASKS.json')[0];remap={'task_id','role','run_id','output','run_root','depends_on'}
 assert {k:v for k,v in task.items()if k not in remap}=={k:v for k,v in original.items()if k not in remap}
 assert Path(task['output'])==O/'zero200'and task['seed']==10060001 and task['case_id']=='WEST_EAST'
 return q
