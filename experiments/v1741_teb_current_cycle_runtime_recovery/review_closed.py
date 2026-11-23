"""Accurate current TEB source/actual closure without rerunning any numerics."""
import fcntl,hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1739_teb_current_cycle';D=R/'runs/v1741_teb_current_cycle_runtime_recovery'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not(O/'ACTUAL_RUNTIME_CLOSED_REVIEW.json').exists()
 owner=read(O/'COMPLETION.json');assert owner['closed']and owner['review_restored']and owner['lock_idle']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 identity=read(O/'OWNED_CHILD.json');p=Path('/proc',str(identity['pid']),'stat')
 if p.exists():assert p.read_text().split(') ',1)[1].split()[19]!=identity['start_ticks']
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 frozen=read(O/'SOURCE_FREEZE.json');assert all(sha(R/n)==h for n,h in frozen['files'].items())and all(sha(Path(n))==h for n,h in frozen['external_SHA256'].items())
 out=O/'actual';result=read(out/'RESULT.json');assert result['closed']
 assert sha(out/'RESULT.json')==owner['machine_result_sha256']
 rows=read(out/'APPLIED_JOURNAL.json');applied=sum(x['applied']for x in rows);assert applied==owner['actual_native']==result['new_actual_native']
 native=read(out/'TEB_NATIVE_QUERY_RESULT.json')if(out/'TEB_NATIVE_QUERY_RESULT.json').exists()else None
 audit=result.get('independent_audit')or{};component=result.get('component')or{}
 proof=dict(closed=True,scope='EXPOSED_TEB_CURRENT_QUERY_SHORT_ACTUATOR_COMPONENT_NOT_WHOLE_BENCHMARK',passed=bool(owner['passed']and result['passed']),scientific_navigation_passed=False,whole_navigation_passed=False,new_independent_task_increment=0,formal_assignment_increment=0,actual_canonical_initializations=result.get('canonical_vehicle_initializations'),internal_factory_model_constructions=None,actual_native=result.get('new_actual_native'),own_replay_native=result.get('own_replay_native'),component_passed=bool(component.get('passed')),independent_full_actual_audit_passed=bool(audit.get('passed')),native_query=native,first_error=result.get('first_error'),secondary_errors=result.get('secondary_errors'),outer_first_error=owner.get('first_error'),physical=result.get('physical'),own_replay=result.get('replay'),component=component,independent_audit=audit,tracked_q1159_recovery_subset=result.get('model_work'),all_modelwork_total=None,internal_Allocator_constructions=None,journal_rows=len(rows),journal_applied_rows=applied,terminal2200_zero_requests=bool(len(rows)>=2200 and all(x['request']==[0.,0.,False]for x in rows[-2200:])),source_members=len(frozen['files']),all_source_SHA_verified_after_child_exit=True,review_original=True,execution_idle=True,owned_child_gone=True,remote_runtime_recovery_pending=True,reviewed_unix=time.time())
 proof['source_result_paths_SHA256']={str(p.relative_to(R)):sha(p)for p in [O/'COMPLETION.json',O/'SOURCE_FREEZE.json',out/'RESULT.json',out/'APPLIED_JOURNAL.json']}
 (O/'ACTUAL_RUNTIME_CLOSED_REVIEW.json').write_text(json.dumps(proof,indent=2,allow_nan=False)+'\n')
 (R/'docs/TEB_ACTUAL_CURRENT_CYCLE_V1739_REPORT.md').write_text('# Original TEB current cycle V1739\n\nOne exposed WE03 operational development case. Body-centre/rear-axle/footprint geometry, original HCP binary, original raw output plus explicit upstream ROS saturation port, original fullstate stop/feedback gates. No new phase, whole navigation, statistical or realtime claim. Source/interface failures and finite planner/command/safety refusals distinguished by the exact primary and secondary records below. q1159 counters are a subset, all other native/static/FFI work and internal factory/Allocator counts remain unknown. Source qualification was separate zero-model work.\n\n```json\n'+json.dumps(proof,indent=2)+'\n```\n')
 print(json.dumps({k:proof[k]for k in ['passed','actual_native','own_replay_native','component_passed','independent_full_actual_audit_passed','first_error']}))
if __name__=='__main__':main()
