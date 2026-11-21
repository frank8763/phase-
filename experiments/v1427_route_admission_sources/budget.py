"""Exact bounded-route limits/dual clock/all-runs peak check; no model calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def limits_check(limits):
 assert limits==read(C/'LIMITS.json'),'FROZEN_ROUTE_LIMITS_CHANGED'
 assert limits['maximum_actual_native']==40000 and limits['normal_action_native_cap_before_final200']==39800
 w=limits['witness'];assert w['maximum_events']==8 and w['maximum_nominal_native']==5000 and w['maximum_generation_per_event']==w['maximum_audit_per_event']==201*w['maximum_nominal_native']
 assert w['maximum_generation_native']==w['maximum_audit_native']==w['maximum_events']*w['maximum_generation_per_event']
 assert limits['current_reserve']['maximum_analytical_native']==200*limits['maximum_actual_native']
 assert limits['current_reserve']['maximum_predictor_constructions']==limits['maximum_actual_native']
 assert limits['maximum_allocator_recomputations']==limits['maximum_own_replay_native']==limits['maximum_pair_state_comparisons_per_trace']==limits['maximum_actual_native']
 assert limits['maximum_task_wall_s']==5400 and limits['finalization_reserve_s']>=600
 assert limits['storage_limit_bytes']==10*1024**3 and limits['root_reserve_bytes']==512*1024**2
 assert limits['remaining_archive_download_reserve_bytes']==limits['archive_reserve_bytes']+limits['download_reserve_bytes']
 return True

def clocks(window,parent,*,reserve_s):
 assert window['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert window['absolute_deadline_unix']<=1795395600 and window['hard_stop_monotonic']<=parent['hard_stop_monotonic']
 assert 0<window['absolute_deadline_unix']-window['started_unix']<=5400
 assert abs((window['hard_stop_monotonic']-window['started_monotonic'])-(window['absolute_deadline_unix']-window['started_unix']))<=1e-5
 assert min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())>reserve_s,'ROUTE_DUAL_CLOCK_RESERVE_EXHAUSTED'

def allocated(path):return int(subprocess.check_output(['du','-sx','-B1',str(path)],text=True).split()[0])
def storage_preflight(limits):
 limits_check(limits);used=allocated(R/'runs');peak=used+limits['maximum_task_evidence_bytes']+limits['archive_reserve_bytes']+limits['download_reserve_bytes']+limits['root_reserve_bytes']
 assert peak<limits['storage_limit_bytes'],'ALL_RUNS_NEXT_EVIDENCE_ARCHIVE_DOWNLOAD_ROOT_PEAK_EXCEEDS_LIMIT'
 return dict(passed=True,allocated_all_runs_bytes=used,new_evidence_cap_bytes=limits['maximum_task_evidence_bytes'],archive_bytes=limits['archive_reserve_bytes'],download_bytes=limits['download_reserve_bytes'],root_reserve_bytes=limits['root_reserve_bytes'],estimated_cap_peak_bytes=peak,limit_bytes=limits['storage_limit_bytes'],inode_counted_by_du=True,models=0)

def complete_admission():
 path=O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json'
 if not path.exists():raise RuntimeError('NO_COMPLETE_ROUTE_ADMISSION_MODELS_AND_VEHICLES_FORBIDDEN')
 q=read(path);assert q['passed']is True and q['physical_admission']is True
 required=['exact_source_and_dependency_identity','real_native_ROS_CLI_guard_and_JSON','actual_RPC_source_freshness_and_retirement','current_reserve_complete_before_gate','cross_mode_source_and_gear','recorded_event_certificate_reserve_reference_array_audit','allocator_control_audit_source','fullstate_own_replay_and_pair_source','accurate_stage_counts_and_dualclock','full10GiB_storage_peak']
 assert set(q['admission_gates'])==set(required)and all(q['admission_gates'][k]is True for k in required),'INCOMPLETE_ROUTE_QUALIFICATION_GATES'
 assert q['limits']==read(C/'LIMITS.json')and q['tasks_sha256']==sha(C/'TASKS.json')
 assert q['tested_source_hashes']and all(sha(R/p)==h for p,h in q['tested_source_hashes'].items())
 return q
