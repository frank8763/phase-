"""New formal-case metadata review/ledger and remote barrier, no numerics."""
import argparse,fcntl,hashlib,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1643_formal_parent_metadata';SOURCE=R/'runs/v1797_auditor_regression_syntax'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v,*,new=True):
 assert not new or not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});a=argparse.ArgumentParser();a.add_argument('--assignment',required=True);a.add_argument('--barrier-session');args=a.parse_args()
 assert args.assignment in [a['assignment_id']for row in read(ROOT/'TASKS_LOCKED.json')['tasks']if row['task']['case_id']=='EAST_WEST'for a in row['assignments']]
 O=ROOT/'rounds'/args.assignment;D=R/'runs/v1801_phase10_full_runtime_recovery'/args.assignment
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
 raise AssertionError('CLOSED_SCIENCE_REVIEW_ALREADY_EXISTS_NO_REPEAT')
if __name__=='__main__':main()
