"""One background assignment plus same-round evidence closure; never dispatch a successor."""
import fcntl,hashlib,json,os,selectors,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;ROOT=R/'runs/v1643_formal_parent_metadata';PARSER=__import__('argparse').ArgumentParser();PARSER.add_argument('--assignment',required=True);AID=PARSER.parse_args().assignment;assert AID in [a['assignment_id']for row in json.loads((ROOT/'TASKS_LOCKED.json').read_text())['tasks']if row['task']['case_id']=='EAST_WEST'for a in row['assignments']];D=D/AID;O=ROOT/'rounds'/AID;BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip();START=time.monotonic()
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def alive(i):
 p=Path('/proc')/str(i['pid'])/'stat'
 return Path('/proc/sys/kernel/random/boot_id').read_text().strip()==i['boot_id']and p.exists()and p.read_text().split()[21]==i['start_ticks']
def stop(i):
 if alive(i):
  os.killpg(i['pgid'],signal.SIGTERM);end=time.monotonic()+8
  while alive(i)and time.monotonic()<end:time.sleep(.05)
  if alive(i):os.killpg(i['pgid'],signal.SIGKILL)
def stage(name,args,timeout,allow_failure=False):
 assert time.monotonic()<START+7200 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT
 live=D/'live_io';live.mkdir(exist_ok=True);start=time.monotonic();wall=time.time();data=bytearray();last_checkpoint=0.
 p=subprocess.Popen([sys.executable,*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
 identity=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split()[21],boot_id=BOOT,command=args,timeout_s=timeout);put(live/(name+'_OWNED.json'),identity)
 print(json.dumps(dict(stage=name,started=True,pid=p.pid)),flush=True)
 try:
  selector=selectors.DefaultSelector();selector.register(p.stdout,selectors.EVENT_READ)
  while selector.get_map():
   assert time.monotonic()<start+timeout and time.time()<wall+timeout and time.monotonic()<START+7200 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT,'BACKGROUND_STAGE_DUAL_CLOCK_STOP'
   if time.monotonic()-last_checkpoint>10:
    progress=None
    if(O/'actual/ACTUAL_PROGRESS.json').exists():
     item=read(O/'actual/ACTUAL_PROGRESS.json');progress={k:item.get(k)for k in ['native','phase']}
    put(live/'BACKGROUND_PROGRESS.json',dict(unix=time.time(),stage=name,stage_elapsed_s=time.monotonic()-start,owned_process_identity=identity,actual_progress=progress,partial_not_scientific_pass=True));last_checkpoint=time.monotonic()
    if name=='owner'and(O/'ROUND_ONCE_CLAIM.json').exists():
     path=ROOT/'FORMAL_LEDGER.json';ledger=read(path);row=next(x for x in ledger['rows']if x['assignment_id']==AID)
     if not row.get('registered'):
      row.update(registered=True,closed=False,status='ACTIVE_REGISTERED_SINGLE_BACKGROUND',source_version_root='runs/v1781_ew_charged_job_files',actual_native=None,own_replay_native=None);ledger.update(registered_assignments=sum(bool(x.get('registered'))for x in ledger['rows']),closed_assignments=sum(bool(x.get('closed'))for x in ledger['rows']),unexecuted_assignments=20-sum(bool(x.get('registered'))for x in ledger['rows']),recorded_unix=time.time());put(path,ledger)
   for key,_ in selector.select(.2):
    block=os.read(key.fileobj.fileno(),16384)
    if not block:selector.unregister(key.fileobj);continue
    assert len(data)+len(block)<=1024**2,'BACKGROUND_CONSOLE_1MIB';data.extend(block)
  p.wait(timeout=5)
 finally:
  if p.poll()is None:
   if name=='owner'and(O/'OWNED_CHILD.json').exists():stop(read(O/'OWNED_CHILD.json'))
   stop(identity)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:pass
  (live/(name+'.console')).write_bytes(data)
  put(live/(name+'_EXIT.json'),dict(returncode=p.poll(),wall_s=time.monotonic()-start,pid=p.pid,stage=name))
 assert allow_failure or p.returncode==0,'BACKGROUND_STAGE_FAILED:'+name
 return identity

def main():
 os.sched_setaffinity(0,{5});authorization=read(R/'runs/v1769_overnight_phase_campaign/AUTHORIZATION.json');assert authorization['overnight_authorized']and authorization['automatic_successor_authorized']and time.time()<authorization['no_new_model_launch_after_unix']
 assert read(D/'USER_SINGLE_ROUND_COMMAND.json')['assignment']==AID
 assert not(D/'BACKGROUND_ONCE_CLAIM.json').exists()and not(O/'ROUND_ONCE_CLAIM.json').exists()and not(O/'COMPLETION.json').exists()
 pre=read(D/(AID+'_PRELAUNCH.json'));assert pre['passed']and pre['all_source_SHA_verified']and time.time()-pre['unix']<180
 current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and current['active_math']is None and not current['models_now_authorized']and current['tonight_overnight_authorized']
 original=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(original).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 put(D/'BACKGROUND_ONCE_CLAIM.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],boot_id=BOOT,started_unix=time.time(),assignment=AID,one_assignment_only=True,next_round_requires_user_command=False,source_version='v1781_ew_charged_job_files',source_freeze_sha256=pre['source_freeze_sha256'],helper_source_paths_SHA256={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()}))
 result=dict(closed=False,pipeline_passed=False,scientific_passed=None,assignment=AID,automatic_next_round=False,next_round_requires_user_command=False)
 try:
  stage('owner',[str(R/'experiments/v1781_ew_charged_job_files/owner.py'),'--assignment',AID],5500,allow_failure=True)
  assert read(O/'COMPLETION.json')['closed']
  stage('review',[str(C/'finish.py'),'--assignment',AID],150)
  result['scientific_passed']=read(O/'RUNTIME_CLOSED_REVIEW.json')['passed']
  stage('archive',[str(C/'finalize.py'),'--assignment',AID],180)
  stage('source_ref',[str(C/'deliver.py'),'--assignment',AID,'--sync'],30)
  delivery=stage('deliver',[str(C/'deliver.py'),'--assignment',AID],650)
  stage('barrier',[str(C/'close.py'),'--assignment',AID,'--barrier-session','background deliver pid='+str(delivery['pid'])],30)
  assert read(O/'POST_ROUND_STORAGE_BARRIER.json')['passed'];result['pipeline_passed']=True
  with(R/('docs/EW_'+AID+'_V1783_REPORT.md')).open('a')as f:f.write('\n同轮远端block/member/whole/indexSHA及精确运输清理已完成，原数据保留，POST_ROUND_STORAGE_BARRIER已保存。本闭环补充晚于首次封档；科学结果以上述原machine/独立审核为准。本子helper停止，由通宵父controller审核后继准入。\n')
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc(),evidence_or_transport_closure_incomplete=True)
 finally:
  idle=False
  try:
   with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);idle=True
   if(O/'OWNED_CHILD.json').exists():assert not alive(read(O/'OWNED_CHILD.json')),'OWNED_MODEL_STILL_ALIVE'
   (R/'REVIEW_PENDING').write_bytes(original)
  except BaseException as error:result['safe_close_error']=repr(error)
  result.update(closed=True,wall_s=time.monotonic()-START,execution_idle=idle,review_original=(R/'REVIEW_PENDING').is_file()and sha(R/'REVIEW_PENDING')==hashlib.sha256(original).hexdigest(),model_next_round_launched=False)
  put(D/'BACKGROUND_RESULT.json',result)
  report=R/('docs/EW_'+AID+'_V1783_REPORT.md')
  if report.exists():(D/'RESULT.md').write_text(report.read_text())
  else:(D/'RESULT.md').write_text('# EW phase assignment后台任务已停止\n\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n\n没有启动下一项；完整科学结果未知，查看原COMPLETION/console。\n')
  current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='OVERNIGHT_EW_ASSIGNMENT_CLOSED'if idle else'BACKGROUND_CLOSE_ANOMALY_NEEDS_REVIEW',active_background_round=None,manual_review_after_every_round=False,automatic_next_round=True,latest_background_result=str((D/'BACKGROUND_RESULT.json').relative_to(R)),next_experiment='overnight parent reviews full safety and canonical remote barrier before fixed next assignment; no helper successor')
  if idle:current.update(active_round=None,active_math=None,models_now_authorized=False)
  put(R/'CURRENT_EXPERIMENT.json',current)
  with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n单项EW phase assignment后台V1783结束：pipeline='+str(result['pipeline_passed'])+'/scientific='+str(result['scientific_passed'])+'；result='+str((D/'BACKGROUND_RESULT.json').relative_to(R))+'。按新通宵授权，父controller核安全与远端闭环后可继续固定下一项；此子helper本身不分派后继。原machine/owner/source/capture/replay/audit结果与unknown保持；晚后台结账outsidearchive明确。\n')
 print(json.dumps(result),flush=True);return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())
