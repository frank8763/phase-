"""Finite dependency chain after current owner; no agent/heartbeat or repairs."""
from pathlib import Path
import json,os,sys,time,subprocess,traceback,hashlib,fcntl,signal
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});identity=read(R/'runs/v1813_rpccr_common_single/BACKGROUND_LAUNCH.json');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot==identity['boot_id'];start=time.monotonic();wall=time.time();limit=wall+32400
 with(D/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),boot=boot,started_unix=wall,dependency=identity,models_authorized=False),f)
 result=dict(passed=False,closed=False,no_chat_supervision=True);last=0
 def stage(name,argv,timeout):
  assert time.time()<limit and time.monotonic()<start+32400 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot
  with(D/(name+'.console')).open('xb')as f:p=subprocess.run(argv,cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  put(D/(name+'_EXIT.json'),dict(returncode=p.returncode,unix=time.time()));assert p.returncode==0,'STAGE_FAILED:'+name
 try:
  while True:
   p=Path('/proc',str(identity['pid']),'stat');alive=p.exists()and p.read_text().split()[21]==identity['start_ticks']
   if not alive:break
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<wall+7200 and time.monotonic()<start+7200
   if time.monotonic()-last>=30:put(D/'CHECKPOINT.json',dict(unix=time.time(),stage='waiting_existing_common_RPCCR_owner_and_evidence_closure',no_new_model_or_source_started=True,dependency_identity=identity));last=time.monotonic()
   time.sleep(1)
  base=R/'runs/v1810_rpccr_common_phase';assert read(R/'runs/v1813_rpccr_common_single/BACKGROUND_RESULT.json')['pipeline_passed']and read(base/'POST_ROUND_STORAGE_BARRIER.json')['passed']
  closed=read(base/'COMPLETION.json');assert closed['closed']and closed['review_restored']and closed['lock_idle']and closed['all_source_SHA_verified_after_child_exit']
  # Any unresolved evidence error blocks automatic actual continuation.
  machine=read(base/'actual/RESULT.json');assert not machine['secondary_errors']and machine['evidence_saved']and(machine.get('replay')or{}).get('passed')
  assert machine['first_error']is None or(machine.get('independent_prefix_audit')or{}).get('passed'),'COMMON_COUNTERPART_EVIDENCE_GAP'
  assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  for p in [R/'runs/v648_static_unknown/execution.lock',R/'runs/v1643_formal_parent_metadata/OWNER.lock']:
   with p.open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  stage('source',[sys.executable,str(R/'experiments/v1814_early_discovery_prefix_scope/source_owner.py')],180)
  q=read(R/'runs/v1814_early_discovery_prefix_scope/SOURCE_QUALIFICATION.json');assert q['passed']and q['models']==q['physical_native']==q['analytical_native']==q['replay_native']==0
  report=R/'docs/EW_PREFIX_SCOPE_V1814_REPORT.md'
  with report.open('a')as f:f.write('\nSOURCE一次CLOSED PASS，冻结'+str(q['source_members'])+'成员/'+str(q['negative_cases'])+'newnegative，原数值/安全门不变；0model/FFI/physics/replay。原phase11no_time不补审。\n')
  stage('archive',[sys.executable,str(R/'experiments/v1815_prefix_scope_source_recovery/finalize.py')],180)
  paths=['experiments/v1814_early_discovery_prefix_scope','experiments/v1815_prefix_scope_source_recovery','experiments/v1816_final_three_ablation_rounds','experiments/v1813_rpccr_common_single','experiments/v1817_bounded_completion_handoff','docs/EW_PREFIX_SCOPE_V1814_REPORT.md','docs/MULTI_ALGORITHM_PROGRESS_20261124.md']
  stage('git_add',['git','add','--',*paths],30)
  stage('git_commit',['git','commit','-m','Scope early discovery refusal audit to the recorded execution stage'],30)
  stage('source_sync',[sys.executable,str(R/'experiments/v1815_prefix_scope_source_recovery/deliver.py'),'--source-sync'],40)
  stage('deliver',[sys.executable,str(R/'experiments/v1815_prefix_scope_source_recovery/deliver.py')],650)
  stage('source_chain',[sys.executable,str(R/'experiments/v1815_prefix_scope_source_recovery/chain.py')],60)
  # This parent never repairs frozen formal code. Remaining3 order is registered.
  stage('remaining3',[sys.executable,str(R/'experiments/v1816_final_three_ablation_rounds/chain.py')],min(21600,limit-time.time()))
  result['passed']=True
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc(),further_models_stopped=True,no_retry_or_source_repair=True)
 finally:result.update(closed=True,closed_unix=time.time(),wall_s=time.monotonic()-start);put(D/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
