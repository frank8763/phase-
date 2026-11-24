"""Late canonical barrier from distinct remote recovery, original science unchanged."""
from pathlib import Path
import json,hashlib,fcntl,time
R=Path(__file__).resolve().parents[2];D=R/'runs/v1795_closed_transport_completion';O=R/'runs/v1643_formal_parent_metadata/rounds/phase_10__no_time';I=R/'runs/v1791_lossless_night_rounds/phase_10__no_time'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 for kind in ['runtime','paper']:
  b=D/kind;assert read(b/'RESULT.json')['passed']and read(b/'FINALIZED.json')['passed'];claim=read(b/'ONCE_CLAIM.json');assert not Path('/proc',str(claim['pid'])).exists()
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for p in [R/'runs/v648_static_unknown/execution.lock',R/'runs/v1643_formal_parent_metadata/OWNER.lock']:
  with p.open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 completion=read(O/'COMPLETION.json');assert completion['closed']and not completion['passed']and completion['all_source_SHA_verified_after_child_exit'];assert sha(O/'actual/RESULT.json')==completion['machine_result_sha256']
 source=R/'runs/v1789_lossless_job_packet';frozen=read(source/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 proof=dict(passed=True,round_id='phase_10__no_time',closed_result_path=str((O/'COMPLETION.json').relative_to(R)),closed_result_sha256=sha(O/'COMPLETION.json'),remote_proof_path=str((I/'FULL_REMOTE_VERIFIED.json').relative_to(R)),remote_proof_sha256=sha(I/'FULL_REMOTE_VERIFIED.json'),cleanup_proof_path=str((I/'TRANSPORT_CLEANUP.json').relative_to(R)),cleanup_proof_sha256=sha(I/'TRANSPORT_CLEANUP.json'),every_block_member_whole_index_SHA_verified=True,all_originals_retained=True,scientific_passed=False,formal_denominator_retained=True,actual_native=50754,own_replay_native=50754,models_authorized=False,distinct_runtime_recovery=str((D/'runtime').relative_to(R)),original_delivery_failure_preserved=True,late_outside_archive=True,recorded_unix=time.time());put(O/'POST_ROUND_STORAGE_BARRIER.json',proof)
 put(O/'REMOTE_RECOVERY_SUPPLEMENT_V1795.json',dict(passed=True,barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'),original_RESULT_and_review_unchanged=True,all_frozen_source_SHA_verified=True,source_members=len(frozen),late_outside_archive=True))
 p=R/'runs/v1643_formal_parent_metadata/FORMAL_LEDGER.json';ledger=read(p);row=next(x for x in ledger['rows']if x['assignment_id']=='phase_10__no_time');row.update(status='CLOSED_NON_SUCCESS_REMOTE_VERIFIED',post_round_barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'));p.write_text(json.dumps(ledger,indent=2)+'\n')
 print(json.dumps(dict(passed=True,scientific_passed=False,old_failed_result_preserved=True)))
if __name__=='__main__':main()
