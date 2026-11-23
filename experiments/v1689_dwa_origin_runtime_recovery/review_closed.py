"""Once source/result/journal closure review; never imports a numerical module."""
import fcntl,hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
O=R/'runs/v1690_dwa_origin_source_checks'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 assert not(O/'RUNTIME_CLOSED_REVIEW.json').exists()
 owner=read(O/'COMPLETION.json');assert owner['closed']and owner['review_restored']and owner['lock_idle']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 identity=read(O/'OWNED_CHILD.json');proc=Path('/proc')/str(identity['pid'])/'stat'
 if proc.exists():assert proc.read_text().split(') ',1)[1].split()[19]!=identity['start_ticks'],'OWNED_CHILD_STILL_LIVE'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 frozen=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 out=O/'actual';result=read(out/'RESULT.json');assert result['closed']
 assert sha(out/'RESULT.json')==owner['machine_result_sha256']
 rows=read(out/'APPLIED_JOURNAL.json');applied=sum(r['applied']for r in rows)
 assert result['new_actual_native']==owner['actual_native']==applied
 origin=read(out/'CURRENT_MEASURED_ORIGIN.json')if(out/'CURRENT_MEASURED_ORIGIN.json').exists()else None
 audit=result.get('independent_audit')or{}
 proof=dict(closed=True,reviewed_unix=time.time(),scope='ONE_NEW_EXPOSED_DWA_MEASURED_ORIGIN_COMPONENT_NOT_WHOLE_BENCHMARK',
  passed=bool(owner['passed']and result['passed']),scientific_navigation_passed=False,whole_navigation_passed=False,
  actual_canonical_initializations=result.get('canonical_vehicle_initializations'),internal_factory_model_constructions=None,
  actual_native=result.get('new_actual_native'),own_replay_native=result.get('own_replay_native'),
  component_execution_passed=bool((result.get('component')or{}).get('passed')),
  independent_full_audit_passed=bool(audit.get('passed')),
  actual_query_counts=(result.get('component')or{}).get('reference_counts'),
  tracked_recovery_subset=result.get('model_work'),all_modelwork_total=None,internal_Allocator_constructions=None,
  first_error=result.get('first_error'),secondary_errors=result.get('secondary_errors'),outer_first_error=owner.get('first_error'),
  saved_independent_audit=audit,original_goal_distance_m=(result.get('component')or{}).get('original_task_goal_distance_m'),
  physical=result.get('physical'),own_replay=result.get('replay'),
  journal_rows=len(rows),journal_applied_rows=applied,terminal2200_zero_requests=(len(rows)>=2200 and all(r['request']==[0.,0.,False]for r in rows[-2200:])),
  origin_receipt_present=origin is not None,origin_packet_sha256=origin.get('packet_sha256')if origin else None,
  source_SHA_all_verified_after_child_exit=True,source_members=len(frozen),review_original=True,execution_lock_idle=True,owned_child_gone=True,
  formal_assignment_increment=0,new_independent_task_increment=0,old_V1683_case_not_reaudited_or_rerun=True,
  remote_runtime_recovery_pending=True,closure_review_models=0,closure_review_numerical_calls=0)
 proof['source_result_paths_SHA256']={str(p.relative_to(R)):sha(p)for p in [O/'COMPLETION.json',O/'SOURCE_FREEZE.json',out/'RESULT.json',out/'APPLIED_JOURNAL.json']}
 if origin:proof['source_result_paths_SHA256'][str((out/'CURRENT_MEASURED_ORIGIN.json').relative_to(R))]=sha(out/'CURRENT_MEASURED_ORIGIN.json')
 (O/'RUNTIME_CLOSED_REVIEW.json').write_text(json.dumps(proof,indent=2,allow_nan=False)+'\n')
 print(json.dumps({k:proof[k]for k in ['passed','actual_native','own_replay_native','component_execution_passed','independent_full_audit_passed','first_error','whole_navigation_passed']}))

if __name__=='__main__':main()
