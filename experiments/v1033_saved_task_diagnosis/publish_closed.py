"""One bounded zero-model publication; verified download precedes raw cleanup."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1032_speed008_qualification';D=R/'records/nav2_v1032_20261111';TAG='phase-speed-response-contract-cut-v1032-v1033-20261111';GH=R/'tools/phase_storage_20261107/vendor/gh'
spec=importlib.util.spec_from_file_location('v1033_stream_archive',R/'experiments/v1020_terminal_two_route_development/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def command(args,timeout=30):
 p=subprocess.run(list(map(str,args)),cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1500:])
 return p.stdout

def main():
 assert not (O/'PUBLICATION_CLAIM.json').exists(),'NO_PUBLICATION_RETRY';dump(O/'PUBLICATION_CLAIM.json',dict(started=time.time(),models=0))
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert json.loads((O/'COMPLETION.json').read_text())['closed']and json.loads((O/'APPROVAL.json').read_text())['models_authorized']is False
 assert arc.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 folders=[R/'experiments/v1031_timed_causal_guidance',R/'experiments/v1032_speed008_qualification',C,O,R/'runs/v1031_timed_causal_guidance',R/'runs/v1033_saved_task_diagnosis',R/'runs/v858_nav2_verified/v1032',D];files=set()
 for folder in folders:files.update(p for p in arc.walk(folder)if p.suffix not in ['.pyc','.so','.lock']and p.name!='PUBLICATION_CLAIM.json')
 files.update([R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'docs/RPCCR_SPEED_RESPONSE_V1032_REPORT.md',R/'docs/RPCCR_FULL_CYCLE_OBSTRUCTION_V1033_REPORT.md',R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json',R/'runs/v858_nav2_verified/v1024/dynamic_we/DYNAMIC_COMPLETE_PLAN.json',R/'runs/v858_nav2_verified/v1024/dynamic_we/physics/SETUP.json'])
 record,inventory=arc.package(R,files,O/'cloud','v1032-response-v1033-continuous-cut',lambda:sum(p.stat().st_size for p in arc.walk(R/'runs/v858_nav2_verified/v1032'))+sum(p.stat().st_size for p in arc.walk(O))<2*1024**3)
 dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag=TAG,archives=[record],restoration='tools/phase_storage_20261107/restore.py',original_dynamic_acceptance=False))
 paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_SPEED_RESPONSE_V1032_REPORT.md','docs/RPCCR_FULL_CYCLE_OBSTRUCTION_V1033_REPORT.md','experiments/v1031_timed_causal_guidance','experiments/v1032_speed008_qualification','experiments/v1033_saved_task_diagnosis','records/nav2_v1032_20261111']
 command(['git','add','--',*paths]);command(['git','diff','--cached','--check','--',*paths]);print(command(['git','diff','--cached','--stat','--',*paths]),flush=True)
 command(['git','commit','--only','-m','Verify speed response and prove original full-cycle spatial contract obstruction','--',*paths]);head=command(['git','rev-parse','HEAD']).strip()
 assert not (O/'SOURCE_SYNC_CLAIM.json').exists();dump(O/'SOURCE_SYNC_CLAIM.json',dict(commit=head,one_push=True,one_head_read=True));sync=dict(commit=head,push_succeeded=False,remote_head_verified=False)
 try:command(['git','push','origin','HEAD:main'],30);sync['push_succeeded']=True
 except BaseException as e:sync['push_error']=repr(e)
 try:sync['remote_head']=command(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except BaseException as e:sync['head_verification_error']=repr(e)
 dump(D/'SOURCE_SYNC_RESULT.json',sync)
 try:
  assert sync['push_succeeded']or sync['remote_head_verified'],'SOURCE_PUSH_UNCONFIRMED_RAW_RETAINED'
  def gh(args,timeout=60):return command([GH,*args,'--repo','frank8763/phase-'],timeout)
  notes=O/'RELEASE_NOTES.md';notes.write_text('Fixed speed response NOT_PASSED; original full-cycle spatial certificate obstruction proved, not impossibility of the real dynamic task. Source '+head+'; all old failures retained. Record index includes per-part and per-member SHA. No training or hardware.\n')
  gh(['release','create',TAG,'--target',head,'--title','Phase V1032 response evidence and V1033 continuous obstruction witness','--notes-file',notes,'--latest=false'],30)
  gh(['release','upload',TAG,*list((O/'cloud').iterdir()),D/'RECORD_INDEX.json',D/'FINAL_SUMMARY.json',D/'SOURCE_SYNC_RESULT.json',R/'docs/RPCCR_SPEED_RESPONSE_V1032_REPORT.md',R/'docs/RPCCR_FULL_CYCLE_OBSTRUCTION_V1033_REPORT.md'],120)
  back=O/'readback';back.mkdir(exist_ok=False)
  def provider(part):gh(['release','download',TAG,'--pattern',part['name'],'--dir',back],120);return back/part['name'],True
  arc.verify(record,inventory,provider);verified=dict(passed=True,release_url='https://github.com/frank8763/phase-/releases/tag/'+TAG,source_commit=head,source_remote_head_verified=sync['remote_head_verified'],all_remote_part_and_member_sha_verified=True,source_members=len(inventory),models=0);dump(D/'REMOTE_VERIFIED.json',verified)
  # Delete only the just-verified new native raw, and the exact archival cache.
  mapping={x['path']:x for x in inventory};deleted=[]
  for p in list(arc.walk(R/'runs/v858_nav2_verified/v1032')):
   row=mapping[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and arc.sha(p)==row['sha256'];deleted.append(dict(path=row['path'],bytes=row['bytes']));p.unlink()
  # Resource links are not followed or counted as removed external data.
  links=[]
  for base,dirs,names in os.walk(R/'runs/v858_nav2_verified/v1032',followlinks=False):
   for name in dirs+names:
    p=Path(base,name)
    if p.is_symlink():links.append(str(p.relative_to(R)));p.unlink()
  cleanup=dict(passed=True,deleted_raw_bytes=sum(x['bytes']for x in deleted),manifest=deleted,removed_resource_links_only=links,old_unverified_raw_untouched=True,models=0);dump(D/'CLEANUP.json',cleanup);gh(['release','upload',TAG,D/'REMOTE_VERIFIED.json',D/'CLEANUP.json'],30)
  shutil.rmtree(O/'cloud');shutil.rmtree(back)
 except BaseException as e:dump(D/'REMOTE_PENDING.json',dict(error=repr(e),raw_retained=not(D/'CLEANUP.json').exists(),no_automatic_retry=True,models=0))
 command(['git','add','--',str(D.relative_to(R))]);command(['git','commit','--only','-m','Keep V1032 delivery verification receipts without a second push','--',str(D.relative_to(R))]);dump(O/'CLOSED.json',dict(closed=True,models_authorized=False,remote_verified=(D/'REMOTE_VERIFIED.json').exists(),one_source_push_attempt=True));print(json.dumps(dict(commit=head,sync=sync,remote_verified=(D/'REMOTE_VERIFIED.json').exists())),flush=True)
if __name__=='__main__':main()
