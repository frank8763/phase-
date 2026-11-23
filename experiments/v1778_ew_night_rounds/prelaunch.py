"""Read-only frozen formal-source and prior-closure admission census."""
import argparse,fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1643_formal_parent_metadata';SOURCE=R/'runs/v1776_ew_worker_import';BASE=R/'runs/v1778_ew_night_rounds'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});a=argparse.ArgumentParser();a.add_argument('--assignment',required=True);args=a.parse_args();assert args.assignment in [a['assignment_id']for row in read(ROOT/'TASKS_LOCKED.json')['tasks']if row['task']['case_id']=='EAST_WEST'for a in row['assignments']];D=BASE/args.assignment;D.mkdir(exist_ok=True)
 O=ROOT/'rounds'/args.assignment;assert not any((O/n).exists()for n in ['ROUND_ONCE_CLAIM.json','ROUND_WINDOW.json','COMPLETION.json','actual'])
 prior=R/'runs/v1643_formal_parent_metadata/rounds/phase_08__full/POST_ROUND_STORAGE_BARRIER.json';b=read(prior);assert b['passed']and all(sha(R/k)==h for k,h in {b['closed_result_path']:b['closed_result_sha256'],b['remote_proof_path']:b['remote_proof_sha256'],b['cleanup_proof_path']:b['cleanup_proof_sha256']}.items())
 new_source_barrier=read(SOURCE/'POST_SOURCE_STORAGE_BARRIER.json');assert new_source_barrier['passed']and all(sha(R/k)==h for k,h in new_source_barrier['proof_paths_SHA256'].items())
 current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and not current['models_now_authorized']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for p in [R/'runs/v648_static_unknown/execution.lock',ROOT/'OWNER.lock']:
  with p.open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 frozen=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 recovery=read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
 assert sha(R/recovery['index_path'])==recovery['index_sha256']and sha(R/recovery['full_remote_proof_path'])==recovery['full_remote_proof_sha256']
 order=[x['assignment_id']for x in read(ROOT/'FORMAL_LEDGER.json')['rows']]
 for previous in order[:order.index(args.assignment)]:
  b=read(ROOT/'rounds'/previous/'POST_ROUND_STORAGE_BARRIER.json');assert b['passed']
  for k,h in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/b[k])==b[h]
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);peak=used+1015*1024**2;assert peak<15*1024**3
 precharge=4*len(json.dumps(current,sort_keys=True,separators=(',',':')).encode())+256*1024;assert precharge<2*1024**2
 path=D/(args.assignment+'_PRELAUNCH.json');assert not path.exists();path.write_text(json.dumps(dict(passed=True,assignment=args.assignment,source_members=len(frozen),source_freeze_sha256=sha(SOURCE/'SOURCE_FREEZE.json'),all_source_SHA_verified=True,source_recovery_verified=True,all_predecessors_closed_remote_cleaned=True,prior_phase08_barrier_sha256=sha(prior),once_unclaimed=True,review_original=True,execution_and_owner_locks_idle=True,allruns_bytes=used,full_peak_bytes=peak,parent_precharge_bytes=precharge,models_created=0,unix=time.time()),indent=2)+'\n');print(path.read_text())
if __name__=='__main__':main()
