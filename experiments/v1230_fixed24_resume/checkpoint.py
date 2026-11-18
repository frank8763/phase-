"""Immutable same-science checkpoint and original task identity validation."""
from worker_context import *
P=R/'runs/v1228_terminal_reserve_confirmation'
def verify_checkpoint(*,require_remote=False):
 d=read(P/'COMPLETION.json');assert d['closed']and d['stop_reason']=='INSUFFICIENT_REMAINING_FOR_COMPLETE_TASK_AUDIT'and d['source_unchanged']
 assert read(P/'FINALIZED.json')['manifest_readback']
 original=read(P/'RESULTS.json');imported=read(O/'CHECKPOINT_ROWS.json');assert len(original)==len(imported)==34
 for a,b in zip(original,imported):
  other={k:v for k,v in b.items()if k not in ['checkpoint_imported','original_batch','original_record_path']}
  assert a==other and b['checkpoint_imported']is True and b['original_batch']=='V1228','CHECKPOINT_RECORD_CHANGED'
 mains=[r for r in imported if r['role']=='main'];assert [r['slot']for r in mains]==list(range(1,7))
 assert all(r['functional_passed']and r['safety_evidence_passed']and r['result']['passed']and r['audit']['passed']for r in imported)
 assert sum(r['role']=='t0'for r in imported)==24 and sum(r['role'].startswith('development_')for r in imported)==4
 assert read(O/'CHECKPOINT_PAIRS.json')==d['development_repeats'] and len(d['development_repeats'])==2 and all(p['passed']and p['maximum_complete_state_ctrl_error']<=1e-8 for p in d['development_repeats'].values())
 assert (C/'ORIGINAL_TASK_LIST.json').read_bytes()==(R/'experiments/v1228_terminal_reserve_confirmation/ORIGINAL_TASK_LIST.json').read_bytes()
 parent=read(R/'experiments/v1228_terminal_reserve_confirmation/TASKS.json');remaining_tasks=read(C/'TASKS.json');assert len(remaining_tasks)==21
 assert [t['task_id']for t in remaining_tasks]==d['unexecuted']
 baseline=read(C/'ALL_BASELINES.json');assert len(baseline)==55
 fields=['slot','seed','phase','case_id','start_xy','start_yaw','goal_xy','dynamic','native_limit','role','task_id','scope','historical_prefix_native','initial_axis_motion_direction']
 for b in baseline:
  old=next(t for t in parent if t['task_id']==b['task_id']);assert all(b[k]==old[k]for k in fields),'ORIGINAL_TASK_IDENTITY_CHANGED'
 for task in remaining_tasks:task_contract(task)
 assert next(t for t in baseline if t['task_id']=='main_slot01')['output']==str(R/'runs/v858_nav2_verified/v1228/main_slot01')
 for slot in [9,17]:assert next(t for t in baseline if t['task_id']=='main_slot'+str(slot).zfill(2))['output']==str(RAW/('main_slot'+str(slot).zfill(2)))
 # Verify every retained source byte. Science+model dependencies cannot be cleaned.
 for n,h in read(R/'experiments/v1228_terminal_reserve_confirmation/SOURCE_FREEZE.json')['files'].items():assert sha(R/n)==h,'PARENT_FROZEN_SOURCE_CHANGED '+n
 if require_remote:
  rec=read(R/'records/nav2_v1228_checkpoint_20261116/REMOTE_VERIFIED.json');assert rec['passed']and rec['all_bytes_and_sha_and_decompressed_members_verified']
  cleanup=read(R/'records/nav2_v1228_checkpoint_20261116/CLEANUP.json');assert cleanup['passed']and cleanup['all_removed_files_remotely_sha_verified']
 return dict(passed=True,checkpoint_main_slots=list(range(1,7)),t0_inherited=24,NS_development_inherited_separately=4,remaining_unique_main_slots=list(range(7,25)),repeat_slots=[1,9,17],same_science=True,old_batch_not_reopened=True,parent_report_unchanged=True)
