"""New formal-case metadata review/ledger and remote barrier, no numerics."""
import argparse,fcntl,hashlib,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1643_formal_parent_metadata';SOURCE=R/'runs/v1765_ns_formal_binding'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v,*,new=True):
 assert not new or not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});a=argparse.ArgumentParser();a.add_argument('--assignment',required=True);a.add_argument('--barrier-session');args=a.parse_args()
 assert args.assignment in {'phase_05__full','phase_05__full'}
 O=ROOT/'rounds'/args.assignment;D=R/'runs/v1767_ns_phase05_single'/args.assignment
 completion=read(O/'COMPLETION.json');assert completion['closed']and completion['review_restored']and completion['lock_idle']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 identity=read(O/'OWNED_CHILD.json');p=Path('/proc',str(identity['pid']),'stat')
 if p.exists():assert p.read_text().split(') ',1)[1].split()[19]!=identity['start_ticks']
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if args.barrier_session:
  remote=read(D/'FULL_REMOTE_VERIFIED.json');assert remote['passed']and all(remote[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])and read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/FINALIZED.json')['passed']
  assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
  put(D/'DELIVERY_WORKER_EXIT.json',dict(passed=True,worker_process_identity=args.barrier_session,returncode=0,worker_gone=True,late_outside_archive=True))
  put(O/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,round_id=args.assignment,closed_result_path=str((O/'COMPLETION.json').relative_to(R)),closed_result_sha256=sha(O/'COMPLETION.json'),remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),cleanup_proof_path=str((D/'TRANSPORT_CLEANUP.json').relative_to(R)),cleanup_proof_sha256=sha(D/'TRANSPORT_CLEANUP.json'),every_block_member_whole_index_SHA_verified=True,all_originals_retained=True,scientific_passed=completion['passed'],formal_denominator_retained=True,actual_native=completion['actual_native'],own_replay_native=completion['own_replay_native'],models_authorized=False,recorded_unix=time.time()))
  put(O/'REMOTE_RECOVERY_SUPPLEMENT.json',dict(passed=True,full_remote=remote,barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'),late_outside_archive=True))
  ledger=read(ROOT/'FORMAL_LEDGER.json');row=next(x for x in ledger['rows']if x['assignment_id']==args.assignment);row.update(status='CLOSED_PASS_REMOTE_VERIFIED'if completion['passed']else'CLOSED_NON_SUCCESS_REMOTE_VERIFIED',post_round_barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'));put(ROOT/'FORMAL_LEDGER.json',ledger,new=False)
  print(json.dumps(dict(remote_closed=True,assignment=args.assignment,scientific_passed=completion['passed'])));return
 admission=read(O/'FORMAL_ADMISSION.json');assert admission['source_version_root']==str(SOURCE.relative_to(R))and admission['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')
 frozen=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 out=O/'actual';machine=read(out/'RESULT.json');assert machine['closed']and sha(out/'RESULT.json')==completion['machine_result_sha256']
 journal=read(out/'APPLIED_JOURNAL.json');applied=sum(bool(x['applied'])for x in journal);assert applied==completion['actual_native']==machine['new_actual_native']
 task=read(O/'FORMAL_TASK.json');full=machine.get('independent_audit')or{};prefix=machine.get('independent_prefix_audit')or{};replay=machine.get('replay')or{}
 proof=dict(closed=True,passed=bool(completion['passed']and machine['passed']),formal_assignment_id=args.assignment,formal_assignment_retained_in_denominator=True,mechanism_variant=task['mechanism_variant'],phase=task['phase'],sensor_seed=task['seed'],source_version_root=str(SOURCE.relative_to(R)),original_contract=True,canonical_initializations=machine.get('canonical_vehicle_initializations'),internal_factory_model_constructions=None,actual_native=machine.get('new_actual_native'),own_replay_native=machine.get('own_replay_native'),replay=replay,physical_telemetry=machine.get('physical'),first_error=machine.get('first_error'),secondary_errors=machine.get('secondary_errors'),outer_first_error=completion.get('first_error'),actual_original_goal_reached=machine.get('actual_original_goal_reached',False),audit_scope=machine.get('audit_scope'),independent_full_goal_audit=full,independent_prefix_safety_audit=prefix,prefix_audit_not_arrival=True,tracked_q1159_recovery_subset=machine.get('model_work'),full_modelwork_total=None,internal_Allocator_constructions=None,fully_recorded_native=machine.get('fully_recorded_native'),model_native_inflight_unknown=machine.get('model_native_inflight_unknown'),journal_rows=len(journal),journal_applied_rows=applied,source_members=len(frozen),all_source_SHA_verified_after_child_exit=True,review_original=True,execution_idle=True,owned_child_gone=True,no_parameter_or_seed_tuning=True,remote_runtime_recovery_pending=True,recorded_unix=time.time())
 proof['source_result_paths_SHA256']={str(p.relative_to(R)):sha(p)for p in [O/'COMPLETION.json',O/'FORMAL_ADMISSION.json',O/'FORMAL_TASK.json',out/'RESULT.json',out/'APPLIED_JOURNAL.json']}
 put(O/'RUNTIME_CLOSED_REVIEW.json',proof)
 ledger=read(ROOT/'FORMAL_LEDGER.json');row=next(x for x in ledger['rows']if x['assignment_id']==args.assignment)
 row.update(registered=True,closed=True,status='CLOSED_PASS_RECOVERY_PENDING'if proof['passed']else'CLOSED_NON_SUCCESS_RECOVERY_PENDING',model_result=machine['passed'],owner_passed=completion['passed'],actual_native=proof['actual_native'],own_replay_native=proof['own_replay_native'],completion_path=str((O/'COMPLETION.json').relative_to(R)),completion_sha256=sha(O/'COMPLETION.json'),source_version_root=str(SOURCE.relative_to(R)),functional_result=None if not proof['first_error']else proof['first_error']['error'],independent_full_goal_audit_passed=bool(full.get('passed')),independent_prefix_safety_audit_passed=bool(prefix.get('passed')))
 # Earlier closed outcomes are unchanged; only a stale transport status is updated.
 for old in ledger['rows']:
  p=ROOT/'rounds'/old['assignment_id']/'POST_ROUND_STORAGE_BARRIER.json'
  if old.get('closed')and p.exists()and read(p)['passed']:old['status']='CLOSED_PASS_REMOTE_VERIFIED'if old.get('model_result')else'CLOSED_NON_SUCCESS_REMOTE_VERIFIED';old['post_round_barrier_sha256']=sha(p)
 ledger.update(recorded_unix=time.time(),registered_assignments=sum(bool(x.get('registered'))for x in ledger['rows']),closed_assignments=sum(bool(x.get('closed'))for x in ledger['rows']))
 ledger['unexecuted_assignments']=20-ledger['registered_assignments'];put(ROOT/'FORMAL_LEDGER.json',ledger,new=False)
 print(json.dumps({k:proof[k]for k in ['formal_assignment_id','passed','actual_native','own_replay_native','audit_scope','first_error']}))
if __name__=='__main__':main()
