"""Offline-safe zero-model closure, single bounded optional remote delivery."""
import fcntl,shutil,subprocess
from kernel import *
D=R/'records/nav2_v1055_20261111';RAW=R/'runs/v858_nav2_verified/v1055';TAG='phase-atomic-execution-v1055-20261111';GH=R/'tools/phase_storage_20261107/vendor/gh';arc=load('v1050_stream_archive',C/'archive.py')
def cmd(args,timeout=30):
 p=subprocess.run([str(a)for a in args],cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1500:])
 return p.stdout

def main():
 assert not(O/'CLOSE_CLAIM.json').exists(),'NO_CLOSURE_RETRY';dump(O/'CLOSE_CLAIM.json',dict(at=time.time(),models=0));D.mkdir(exist_ok=True);lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')==sha(O/'GUARD.bin');done=json.loads((O/'COMPLETION.json').read_text());assert done['closed']and not json.loads((O/'APPROVAL.json').read_text())['models_authorized'];freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());source_ok=all(sha(R/p)==h for p,h in freeze['files'].items());audit=dict(source_freeze_all_sha_verified=source_ok,all_counts_known=not done['unknown_counts'],guard_original=done['guard_original'],execution_lock_idle=True,scientific_goal_passed=done['goal_continuation_and_repeat_passed'],models=0);audit['integrity_passed']=source_ok and audit['all_counts_known']and audit['guard_original'];dump(D/'FINAL_INDEPENDENT_AUDIT.json',audit);dump(D/'FINAL_SUMMARY.json',{k:v for k,v in done.items()if k not in ['rows']})
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n\n- FINAL V1055离线日间接力，固定20:30/1794400200截止；原WE保存态继续主及重复通过='+str(done['goal_continuation_and_repeat_passed'])+'，复用原三反向短响应资格='+str(done['reverse_qualified'])+'，准确分账='+json.dumps(done['counts'])+'，未知='+json.dumps(done['unknown_counts'])+'，原24未执行，旧失败不升级。来源/归档/同步以records/nav2_v1055_20261111为准；闭批恢复REVIEW_PENDING，不自动延时/重启。\n')
 files={R/'docs/RPCCR_GLOBAL_METHOD_REVIEW_20261111.md',R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'docs/RPCCR_ATOMIC_EXECUTION_V1055_REPORT.md'}
 snap=O/'closure_snapshots';snap.mkdir(exist_ok=True)
 for name in ['driver.console','watchdog.console']:
  if (O/name).exists():shutil.copyfile(O/name,snap/name)
 for root in [C,O,RAW,D,R/'experiments/v1049_interval_corridor',R/'runs/v1049_interval_corridor']:files.update(p for p in arc.walk(root)if p.suffix not in ['.pyc','.so','.lock']and p.name not in ['driver.console','watchdog.console','close.console','CLOSE_CLAIM.json'])
 record,inventory=arc.package(R,files,O/'cloud','v1055-atomic-execution-evidence',lambda:sum(p.stat().st_size for p in arc.walk(O))+sum(p.stat().st_size for p in arc.walk(RAW))<2*1024**3);dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag=TAG,archives=[record],restoration='tools/phase_storage_20261107/restore.py'));dump(O/'FINALIZED.json',dict(closed_with_verified_archive=True,scientific_goal_passed=done['goal_continuation_and_repeat_passed'],source_and_decompressed_sha_verified=True,integrity_passed=audit['integrity_passed'],models=0));dump(D/'FINALIZED.json',json.loads((O/'FINALIZED.json').read_text()));paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_ATOMIC_EXECUTION_V1055_REPORT.md','experiments/v1055_atomic_publication_execution','experiments/v1049_interval_corridor','docs/RPCCR_GLOBAL_METHOD_REVIEW_20261111.md',str(D.relative_to(R))];cmd(['git','add','--',*paths]);cmd(['git','diff','--cached','--check','--',*paths]);cmd(['git','commit','--only','-m','Close bounded offline day relay with exact native accounting and original outcomes','--',*paths]);head=cmd(['git','rev-parse','HEAD']).strip();assert not(O/'GIT_SYNC_CLAIM.json').exists();dump(O/'GIT_SYNC_CLAIM.json',dict(commit=head,one_push=True,one_head_read=True));sync=dict(commit=head,push_succeeded=False,remote_head_verified=False)
 try:cmd(['git','push','origin','HEAD:main'],30);sync['push_succeeded']=True
 except BaseException as e:sync['push_error']=repr(e)
 try:sync['remote_head']=cmd(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except BaseException as e:sync['head_verification_error']=repr(e)
 dump(D/'GIT_SYNC_RESULT.json',sync)
 try:
  assert sync['push_succeeded']or sync['remote_head_verified'],'OFFLINE_OR_UNCONFIRMED_SOURCE_RAW_RETAINED'
  from delivery import deliver
  verified,post,upload=deliver(record,inventory,O/'cloud',D,TAG,head,'Original saved-state task main+repeat passed='+str(done['goal_continuation_and_repeat_passed'])+'. Parked causal refresh with retained moving suffix; no new24/training/real-time or recursive-safety claim. Source '+head);dump(D/'REMOTE_VERIFIED.json',verified)
  mapping={x['path']:x for x in inventory};deleted=[]
  for root in [RAW,O/'inputs']:
   for p in list(arc.walk(root)):
    row=mapping[str(p.relative_to(R))];assert arc.sha(p)==row['sha256']and p.stat().st_size==row['bytes'];deleted.append(dict(path=row['path'],bytes=row['bytes']));p.unlink()
  for base,dirs,names in os.walk(RAW,followlinks=False):
   for n in dirs+names:
    p=Path(base,n)
    if p.is_symlink():p.unlink()
  dump(D/'CLEANUP.json',dict(passed=True,deleted_bytes=sum(x['bytes']for x in deleted),manifest=deleted,old_unverified_raw_untouched=True));[post(upload+'?name='+p.name,p.read_bytes(),'application/octet-stream')for p in [D/'REMOTE_VERIFIED.json',D/'CLEANUP.json']];shutil.rmtree(O/'cloud')
 except BaseException as e:dump(D/'REMOTE_PENDING.json',dict(error=repr(e),raw_retained=True,no_automatic_retry=True,models=0))
 cmd(['git','add','--',str(D.relative_to(R))]);cmd(['git','commit','--only','-m','Keep offline relay delivery receipt without repeating push','--',str(D.relative_to(R))]);dump(O/'CLOSED.json',dict(closed=True,models_authorized=False,remote_verified=(D/'REMOTE_VERIFIED.json').exists(),no_retry=True))
if __name__=='__main__':main()
