"""No model imports; distinct initializer-only scope cannot admit navigation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def prerequisites():
 expected=[('v1436_pathlib_control_rename','CONTROL_QUALIFICATION.json'),('v1436_pathlib_control_rename','PEER_QUALIFICATION.json'),('v1437_shared_phase_budget','PHASE_QUALIFICATION.json'),('v1438_planner_writer_entry','PLANNER_QUALIFICATION.json'),('v1439_actual_ros_startup_close','STARTUP_QUALIFICATION.json')]
 proofs={}
 for directory,name in expected:
  path=R/'runs'/directory/name;value=read(path)
  assert value['passed']is True and value['models']==value['physical_native']==0
  proofs[str(path.relative_to(R))]=sha(path)
  for name,digest in value['source_hashes'].items():assert sha(R/name)==digest,'QUALIFIED_DEPENDENCY_SOURCE_CHANGED'
 return proofs

def storage_preflight():
 limits=read(C/'LIMITS.json');used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],text=True).split()[0])
 future=sum(limits[k]for k in ['maximum_task_evidence_bytes','archive_reserve_bytes','download_reserve_bytes','root_reserve_bytes'])
 assert used+future<limits['storage_limit_bytes'],'INITIALIZER_ALL_RUNS_PEAK_EXCEEDS_ROOT'
 return dict(allocated_all_runs_bytes=used,estimated_peak_bytes=used+future,limit_bytes=limits['storage_limit_bytes'],inode_accounted=True,models=0)

def admit(task,approval,window):
 # The missing narrow prerequisite record refuses before importing even the
 # lazy physical binding. A route COMPLETE file grants no authority here.
 path=O/'INITIALIZER_ONLY_ADMISSION.json'
 if not path.exists():raise RuntimeError('INITIALIZER_ENTRY_PREREQUISITES_MISSING_MODELS_FORBIDDEN')
 q=read(path);limits=read(C/'LIMITS.json');assert q['initializer_only_admission']is True and q['physical_route_admission']is False
 required={'actual_no_model_entry_refusal','exact_factory_and_adapter_binding','first_error_and_unknown_count_saves','forbidden_native_step_guard','native_save_size_source_and_byte_path','whole_storage_peak','bounded_dual_clock_and_once_owner'}
 assert set(q['entry_gates'])==required and all(q['entry_gates'].values()),'INITIALIZER_ENTRY_GATES_INCOMPLETE'
 assert q['limits']==limits and q['prerequisite_qualification_SHA']==prerequisites()
 assert q['source_hashes']and all(sha(R/p)==h for p,h in q['source_hashes'].items())
 assert approval['models_authorized']is True and approval['scope']==limits['scope']and approval['qualification_sha256']==sha(path)
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
 assert parent['active_round']==approval['round_id']==C.name+'_initializer_only'and parent['models_now_authorized']
 assert window['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert 0<window['absolute_deadline_unix']-window['started_unix']<=limits['maximum_wall_s']
 assert window['absolute_deadline_unix']<=1795395600 and window['hard_stop_monotonic']<=parent['hard_stop_monotonic']
 assert abs((window['hard_stop_monotonic']-window['started_monotonic'])-(window['absolute_deadline_unix']-window['started_unix']))<=1e-5
 assert min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())>30
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 assert not(R/'REVIEW_PENDING').exists()
 original=read(R/'experiments/v1439_actual_ros_startup_close/TASKS.json')[0];remap={'task_id','role','run_id','output','run_root','depends_on'}
 assert {k:v for k,v in task.items()if k not in remap}=={k:v for k,v in original.items()if k not in remap}
 assert task['case_id']=='WEST_EAST'and task['seed']==10060001 and task['controller_plugin']=='RPP'
 assert Path(task['output'])==O/'initializer_only'
 return q
