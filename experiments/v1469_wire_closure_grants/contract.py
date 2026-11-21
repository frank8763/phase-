"""A distinct partial-navigation capability; never a whole-route COMPLETE."""
import hashlib
import json
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
SCOPE='LIVE_FIRST_EVENT_RUNTIME_QUALIFICATION'
GATES={'exact_current_source_and_task_binding','real_native_and_ROS_scope_refusal','first_event_stop_no_tick_anchor','state_first_and_error_save_paths','original_science_and_postcertificate_freshness_unchanged','four_writer_source_proofs','actual_initializer_tail_allocator_replay_evidence','accurate_shared_clocks_counts_and_storage','once_supervisor_and_missing_remote_recovery_refusal'}
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class NotAdmitted(RuntimeError):pass

def verify_source_recovery(source_hashes):
 recovery=read(O/'SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']
 proof=read(R/recovery['full_remote_verification_path']);assert proof['passed']and proof['every_asset_actual_download_SHA']and proof['every_member_SHA_and_link_text']and proof['whole_archive_SHA']and proof['recovery_index_download_SHA']
 members={row['path']:row for row in read(R/recovery['archive_index_path'])['files']}
 current={name:digest for name,digest in source_hashes.items()if name.startswith('experiments/v1469_wire_closure_grants/')}
 assert current and all(name in members and members[name]['sha256']==digest for name,digest in current.items()),'LIVE_EVENT_NEW_SOURCE_NOT_REMOTELY_RECOVERED'
 return recovery

def prepare_admission():
 path=O/'LIVE_FIRST_EVENT_ONLY_ADMISSION.json';assert not path.exists()
 q=read(O/'SCOPE_QUALIFICATION.json');assert q['passed']and q['models']==q['physical_native']==q['allocator_recomputations']==q['actual_replay_native']==0
 assert set(q['entry_gates'])==GATES and all(q['entry_gates'].values())
 frozen=read(O/'SOURCE_FREEZE.json')['files'];assert frozen==q['source_hashes']and all(sha(R/name)==h for name,h in frozen.items())
 recovery=verify_source_recovery(frozen)
 value=dict(scope=SCOPE,live_first_event_only=True,whole_route_admission=False,live_event_runtime_passed=False,entry_gates=q['entry_gates'],entry_qualification_sha256=sha(O/'SCOPE_QUALIFICATION.json'),tested_source_hashes=frozen,limits=read(C/'LIMITS.json'),tasks_sha256=sha(C/'TASKS.json'),external_writer_hook_qualification=q['external_writer_hook_qualification'],source_remote_recovery=recovery,actual_source_remote_recovery_verified=True)
 text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
 with path.open('x')as stream:stream.write(text)
 return value

def complete_narrow_admission():
 path=O/'LIVE_FIRST_EVENT_ONLY_ADMISSION.json'
 if not path.is_file():raise NotAdmitted('LIVE_FIRST_EVENT_ENTRY_PREREQUISITES_MISSING_NO_MODELS')
 q=read(path);assert q['scope']==SCOPE and q['live_first_event_only']is True and q['whole_route_admission']is False
 assert set(q['entry_gates'])==GATES and all(q['entry_gates'].values())
 assert q['limits']==read(C/'LIMITS.json')and q['tasks_sha256']==sha(C/'TASKS.json')
 assert q['tested_source_hashes']and all(sha(R/p)==h for p,h in q['tested_source_hashes'].items())
 assert q['actual_source_remote_recovery_verified']is True and verify_source_recovery(q['tested_source_hashes'])==q['source_remote_recovery']
 return q

def clocks(window,parent,*,reserve_s):
 assert window['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert 0<window['absolute_deadline_unix']-window['started_unix']<=5400 and window['absolute_deadline_unix']<=1795395600
 assert window['hard_stop_monotonic']<=parent['hard_stop_monotonic']
 assert abs(window['absolute_deadline_unix']-window['started_unix']-(window['hard_stop_monotonic']-window['started_monotonic']))<1e-5
 assert min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())>reserve_s

def authorize(task,window,*,native):
 q=complete_narrow_admission();approval=read(O/'APPROVAL.json');parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
 assert approval['scope']==SCOPE and approval['models_authorized']is True and approval['whole_route_admission']is False
 assert approval['qualification_sha256']==sha(O/'LIVE_FIRST_EVENT_ONLY_ADMISSION.json')
 assert approval['round_id']==parent['active_round']==C.name+'_first_event'and parent['models_now_authorized']
 assert task in read(C/'TASKS.json')and task['role']==task['task_id']=='first_event'
 assert task['case_id']=='WEST_EAST'and task['seed']==10060001 and task['controller_plugin']=='RPP'
 assert Path(task['output'])==O/'first_event'and Path(task['run_root'])==O
 assert window==read(O/'ROUND_WINDOW.json')
 clocks(window,parent,reserve_s=q['limits']['finalization_reserve_s'])
 if native:
  assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and os.environ.get('CUDA_VISIBLE_DEVICES')==''
  assert not(R/'REVIEW_PENDING').exists()
 return q
