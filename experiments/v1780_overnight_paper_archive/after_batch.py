"""Wait for the fixed batch process to finish, then preserve saved paper outputs."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,traceback,fcntl
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;NIGHT=R/'runs/v1769_overnight_phase_campaign'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});auth=read(NIGHT/'AUTHORIZATION.json');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();identity=read(R/'runs/v1778_ew_night_rounds/BACKGROUND_CHAIN_LAUNCH.json');started=time.monotonic();last=0
 with(D/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),pid=os.getpid(),metadata_only=True,no_chat_supervision=True),f)
 result=dict(passed=False,closed=False,models=0,physical_native=0)
 try:
  while True:
   p=Path('/proc',str(identity['pid']),'stat');alive=identity['boot_id']==boot and p.exists()and p.read_text().split()[21]==identity['start_ticks']
   if not alive:break
   assert time.time()<auth['absolute_stop_unix']and time.monotonic()<started+43200 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot
   if time.monotonic()-last>30:put(D/'CHECKPOINT.json',dict(unix=time.time(),waiting_on_existing_batch_identity=identity,concrete_work='passive dependency until closed saved outputs; no agent wakeup or duplicate model'));last=time.monotonic()
   time.sleep(1)
  assert read(R/'runs/v1778_ew_night_rounds/CHAIN_RESULT.json')['closed']
  # Saved-data report can be regenerated only if it failed to materialize, no model work.
  if not(NIGHT/'paper/SUMMARY.json').exists():subprocess.run(['taskset','-c','4',sys.executable,str(R/'experiments/v1778_ew_night_rounds/paper.py')],cwd=R,check=True,timeout=180)
  assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  for path in [R/'runs/v648_static_unknown/execution.lock',R/'runs/v1643_formal_parent_metadata/OWNER.lock']:
   with path.open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for name,args,timeout in [('archive',[],180),('source_proof',['--source-sync'],30),('deliver',[],650)]:
   code='finalize.py'if name=='archive'else'deliver.py'
   with(D/(name+'.console')).open('xb')as f:answer=subprocess.run([sys.executable,str(C/code),*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
   assert answer.returncode==0,'FINAL_PAPER_ARCHIVE_STAGE_FAILED:'+name
  remote=read(D/'FULL_REMOTE_VERIFIED.json');cleanup=read(D/'TRANSPORT_CLEANUP.json');assert remote['passed']and cleanup['passed']
  result.update(passed=True,paper_summary=read(NIGHT/'paper/SUMMARY.json'),full_remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),full_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),cleanup_proof_sha256=sha(D/'TRANSPORT_CLEANUP.json'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc(),all_originals_retained=True)
 finally:
  result.update(closed=True,closed_unix=time.time(),wall_s=time.monotonic()-started);put(D/'RESULT.json',result);put(NIGHT/'FINAL_REPORT_INDEX.json',dict(closed=True,paper_result_path=str((D/'RESULT.json').relative_to(R)),paper_result_sha256=sha(D/'RESULT.json'),paper_directory=str((NIGHT/'paper').relative_to(R)),scientific_batch_result='runs/v1778_ew_night_rounds/CHAIN_RESULT.json',no_chat_supervision=True))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
