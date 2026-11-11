"""Offline zero-model closure. Optional one-shot sync; retain unverified raw."""
import sys,fcntl,json,time,subprocess,shutil,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from resource_policy import apply
apply()
from authority import R,O,HARD_END,sha
from archive import walk,package,verify
RAW=R/'runs/v858_nav2_verified/v1065';D=R/'records/nav2_v1065_20261112';TAG='phase-preflight-entry-v1065-20261112'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def cmd(args,timeout=30):
 p=subprocess.run([str(x)for x in args],cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1000:])
 return p.stdout

def main():
 try:
  with(O/'FINALIZE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
 except FileExistsError:return
 D.mkdir(exist_ok=True)
 try:
  lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert not json.loads((O/'APPROVAL.json').read_text())['models_authorized'];frozen=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(sha(R/p)==h for p,h in frozen['files'].items())
  if not(O/'COMPLETION.json').exists():
   attempts=json.loads((O/'ATTEMPTS.json').read_text())if(O/'ATTEMPTS.json').exists()else[];counts={k:0 for k in ['model_initializations','navigation_native','historical_replay_native','own_replay_native','private_mujoco_native']};unknown=[]
   for task in attempts:
    p=Path(task['output'])/'RESULT.json';row=json.loads(p.read_text())if p.exists()else{}
    for k in counts:
     value=row.get(k)
     if value is None:counts[k]=None;unknown.append(dict(task=task['task_id'],field=k))
     elif counts[k]is not None:counts[k]+=value
   dump(O/'COMPLETION.json',dict(closed=True,driver_disappeared=True,combined_three_route_development_passed=False,confirmation_passed=False,counts=counts,unknown_counts=unknown,error='REGISTERED_DRIVER_DISAPPEARED_NO_MODEL_RESTART',attempted_task_ids=[t['task_id']for t in attempts],deadline_unix=HARD_END))
  done=json.loads((O/'COMPLETION.json').read_text());dump(D/'FINAL_SUMMARY.json',done)
  for name in ['AUTHORIZATION.json','ROUND_WINDOW.json','START_RECEIPT.json','QUALIFICATION.json','THREE_ROUTE_GATE.json','CANDIDATE_RESULTS.json','CONFIRMATION_REPEATS.json','REPEAT_COMPARISONS']:
   p=O/name
   if p.is_file():shutil.copyfile(p,D/name)
   elif p.is_dir():shutil.copytree(p,D/name)
  audit=dict(source_sha_verified=True,execution_lock_idle=True,guard_original=True,driver_completed=not done.get('driver_disappeared',False),counts_known=not done.get('unknown_counts'),combined_three_route_development_passed=done.get('combined_three_route_development_passed',False),confirmation_passed=done.get('confirmation_passed',False),raw_retained=True,models=0);dump(D/'FINAL_INDEPENDENT_AUDIT.json',audit)
  report=R/'docs/RPCCR_THREE_ROUTE_NIGHT_V1065_ENTRY_REPORT.md'
  if not report.exists():report.write_text('# V1062 通宵异常封账\n\n'+json.dumps(done,ensure_ascii=False,indent=2)+'\n\n没有重启模型；未知账目保持未知，必要原始证据保留。\n')
  with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n\n- FINAL V1062通宵固定2026-11-12 09:00截止，新EW北移0.10m课程；同候选三路线通过='+str(done.get('combined_three_route_development_passed',False))+'，新24确认通过='+str(done.get('confirmation_passed',False))+'，准确或未知分账='+json.dumps(done['counts'])+'，未知='+json.dumps(done.get('unknown_counts',[]))+'。四固定信息接近支线、功能安全分层接力；实际与未执行分母见docs/RPCCR_THREE_ROUTE_NIGHT_V1065_ENTRY_REPORT.md；CPU2最低优先级/GPU禁用/Stage完全隔离，guard恢复，无模型重启。\n')
  cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True);cur['v1065_preflight_metadata_continuation_closed']=done;dump(R/'CURRENT_EXPERIMENT.json',cur)
  sources={R/p for p in frozen['files']};sources.update(walk(C));sources.update(walk(RAW));sources.update(p for p in walk(O)if p.name not in ['driver.console','watchdog.console','finalize.console','watchdog_finalize.console','FINALIZE_CLAIM.json']);sources.update(walk(D));sources.update([R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',report]);total=lambda:sum(p.stat().st_size for root in [RAW,O]for p in walk(root));assert total()<6*1024**3,'OFFLINE_RAW_RETAINED_ARCHIVE_RESERVE_INSUFFICIENT'
  archive,inventory=package(R,sources,O/'cloud','v1062-night-evidence',lambda:total()<8*1024**3);dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag=TAG,archives=[archive]));dump(D/'FINALIZED.json',dict(passed=True,scope='EVIDENCE_CLOSURE_NOT_FUNCTIONAL_PASS',local_source_decompression_SHA_verified=True,source_files=len(inventory),remote_pending=True,models=0));paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',str(report.relative_to(R)),str(C.relative_to(R)),str(D.relative_to(R))];cmd(['git','add','--',*paths]);cmd(['git','diff','--cached','--check','--',*paths]);cmd(['git','commit','--only','-m','Close fixed offline three-route night with exact outcomes and accounting','--',*paths]);head=cmd(['git','rev-parse','HEAD'],5).strip();assert not(O/'GIT_SYNC_CLAIM.json').exists();dump(O/'GIT_SYNC_CLAIM.json',dict(commit=head,one_push=True));sync=dict(commit=head,push_succeeded=False,remote_head_verified=False)
  try:cmd(['git','push','origin','HEAD:main'],30);sync['push_succeeded']=True
  except BaseException as e:sync['push_error']=repr(e)
  try:sync['remote_head']=cmd(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
  except BaseException as e:sync['head_error']=repr(e)
  dump(D/'GIT_SYNC_RESULT.json',sync);assert sync['remote_head_verified'],'NETWORK_UNAVAILABLE_RAW_AND_LOCAL_ARCHIVE_RETAINED'
  # The existing bounded delivery implements authenticated no-redirect uploads
  # and streaming part plus every-member readback. It imports no physical model.
  import importlib.util
  spec=importlib.util.spec_from_file_location('v1062_old_delivery',C/'delivery.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);verified,post,upload=module.deliver(archive,inventory,O/'cloud',D,TAG,head,'V1062 fixed offline night; three-route='+str(audit['combined_three_route_development_passed'])+', new24='+str(audit['confirmation_passed'])+'. New EW north0.10m declared course; exact failures retained; no real-time or recursive guarantee.');dump(D/'REMOTE_VERIFIED.json',verified)
  removed=[]
  for row in inventory:
   p=R/row['path']
   if not(p.is_relative_to(RAW)or p.is_relative_to(O))or p.stat().st_size<1048576:continue
   assert p.is_file()and not p.is_symlink()and sha(p)==row['sha256'];p.unlink();removed.append(dict(path=row['path'],bytes=row['bytes']))
  dump(D/'CLEANUP.json',dict(passed=True,removed_logical_bytes=sum(x['bytes']for x in removed),files=removed,old_unverified_raw_untouched=True));shutil.rmtree(O/'cloud')
  for p in [D/'REMOTE_VERIFIED.json',D/'CLEANUP.json']:post(upload+'?name='+p.name,p.read_bytes(),'application/octet-stream')
 except BaseException as e:dump(D/'PENDING.json',dict(error=repr(e),traceback=traceback.format_exc(),no_automatic_retry=True,models=0,required_unverified_raw_preserved=True))
if __name__=='__main__':main()
