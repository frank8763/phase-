"""Continue closed zero-model delivery after two frozen EOF-blank check findings.

Never reruns publication preparation, archive creation, models, or a push.
The existing archive is verified without rewriting; the first source push remains
unclaimed. Frozen scientific files are retained byte for byte.
"""
import fcntl,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1039_causal_approach';D=R/'records/nav2_v1039_20261111';RAW=R/'runs/v858_nav2_verified/v1039';GH=R/'tools/phase_storage_20261107/vendor/gh';TAG='phase-causal-observation-v1039-v1041-20261111';REPORT=R/'docs/RPCCR_CAUSAL_APPROACH_V1039_V1041_REPORT.md'
s=importlib.util.spec_from_file_location('v1039_delivery_archive',R/'experiments/v1020_terminal_two_route_development/archive.py');arc=importlib.util.module_from_spec(s);s.loader.exec_module(arc)
NAMES=['v1034_portal_timed_source','v1035_signed_timed_input_source','v1036_recovery_seeded_timed_source','v1037_periodic_norm_source','v1038_staged_timed_source','v1039_causal_approach','v1040_approach_information_audit','v1041_causal_phase_alignment']
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def cmd(args,timeout=30):
 p=subprocess.run(list(map(str,args)),cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1500:])
 return p.stdout

def main():
 assert (O/'PUBLICATION_CLAIM.json').exists()and not(O/'SOURCE_SYNC_CLAIM.json').exists(),'NO_REPEAT_SYNC';assert not(O/'DELIVERY_CONTINUATION_CLAIM.json').exists(),'NO_REPEAT_CONTINUATION';dump(O/'DELIVERY_CONTINUATION_CLAIM.json',dict(started=time.time(),models=0,scope='first unsent source push and existing archive transfer only'))
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert arc.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 done=json.loads((O/'COMPLETION.json').read_text());assert done['closed']and done['passed']and not json.loads((O/'APPROVAL.json').read_text())['models_authorized'];freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(arc.sha(R/p)==h for p,h in freeze['files'].items())
 index=json.loads((D/'RECORD_INDEX.json').read_text());record=index['archives'][0];inventory=json.loads((O/'cloud'/(record['group']+'.INVENTORY.json')).read_text())['files'];arc.verify(record,inventory,lambda part:(O/'cloud'/part['name'],False))
 error=dict(models=0,integrations=0,stage='local git diff --cached --check after successful immutable local archive verification',source_push_attempts_before=0,error='two frozen source files have one extra blank line at EOF',paths=['experiments/v1038_staged_timed_source/phase_geometry.py:20','experiments/v1039_causal_approach/component_plan.py:17'],frozen_source_unchanged=True,archive_not_overwritten=True,resolution='retain exact frozen bytes and explicitly accept only these EOF blank findings; continue first source delivery once')
 dump(D/'PUBLICATION_CHECK_EXCEPTION.json',error)
 paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',str(REPORT.relative_to(R)),*[str(Path('experiments')/n)for n in NAMES],str(D.relative_to(R))]
 # Small supplement preserves stable first publisher failure and post-close operator metadata.
 supplement={C/'complete_publication.py',D/'PUBLICATION_CHECK_EXCEPTION.json',O/'PUBLICATION_CLAIM.json',O/'DELIVERY_CONTINUATION_CLAIM.json',O/'publication_initial.console',O/'FINALIZED.json',D/'FINALIZED.json',REPORT,R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md'}
 extra,extra_inventory=arc.package(R,supplement,O/'cloud-closure','v1039-closed-delivery-supplement');index['archives'].append(extra);index['restore_order']='listed archives in order; later closure metadata supersedes earlier snapshots';dump(D/'RECORD_INDEX.json',index)
 cmd(['git','add','--',*paths]);check=subprocess.run(['git','diff','--cached','--check','--',*paths],cwd=R,capture_output=True,text=True);expected='experiments/v1038_staged_timed_source/phase_geometry.py:20: new blank line at EOF.\nexperiments/v1039_causal_approach/component_plan.py:17: new blank line at EOF.\n';assert check.returncode!=0 and check.stdout==expected and not check.stderr,repr((check.returncode,check.stdout,check.stderr))
 print(cmd(['git','diff','--cached','--stat','--',*paths]),flush=True)
 for p in cmd(['git','diff','--cached','--name-only','--',*paths]).splitlines():assert (R/p).stat().st_size<90*1024**2
 cmd(['git','commit','--only','-m','Verify causal observation component and remaining original dynamic-route obstruction','--',*paths]);head=cmd(['git','rev-parse','HEAD']).strip();dump(O/'SOURCE_SYNC_CLAIM.json',dict(commit=head,one_push=True,one_head_read=True));sync=dict(commit=head,push_succeeded=False,remote_head_verified=False)
 try:cmd(['git','push','origin','HEAD:main'],30);sync['push_succeeded']=True
 except BaseException as e:sync['push_error']=repr(e)
 try:sync['remote_head']=cmd(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except BaseException as e:sync['head_verification_error']=repr(e)
 dump(D/'SOURCE_SYNC_RESULT.json',sync);print(json.dumps(sync),flush=True)
 try:
  assert sync['push_succeeded']or sync['remote_head_verified'],'SOURCE_PUSH_UNCONFIRMED_RAW_RETAINED'
  def gh(args,timeout=60):return cmd([GH,*args,'--repo','frank8763/phase-'],timeout)
  notes=O/'RELEASE_NOTES.md';notes.write_text('Original-task finite causal observation component PASS; original full dynamic goal and24 NOT passed. New observation area reduction99.14%, narrowed full-cycle contract still obstructed. Original preparation and affinity exceptions retained. Source '+head+'. Per-part and decompressed-member SHA verification required before cleanup.\n')
  gh(['release','create',TAG,'--target',head,'--title','Phase V1039 causal observation and remaining timed-route diagnosis','--notes-file',notes,'--latest=false'],30)
  assets=[*list((O/'cloud').iterdir()),*list((O/'cloud-closure').iterdir()),D/'RECORD_INDEX.json',D/'FINAL_SUMMARY.json',D/'SOURCE_SYNC_RESULT.json',D/'FINALIZED.json',D/'PUBLICATION_CHECK_EXCEPTION.json',REPORT];gh(['release','upload',TAG,*assets],120)
  back=O/'readback';back.mkdir(exist_ok=False)
  def provider(part):gh(['release','download',TAG,'--pattern',part['name'],'--dir',back],120);return back/part['name'],True
  arc.verify(record,inventory,provider);arc.verify(extra,extra_inventory,provider);verified=dict(passed=True,release_url='https://github.com/frank8763/phase-/releases/tag/'+TAG,source_commit=head,source_remote_head_verified=sync['remote_head_verified'],all_remote_part_and_member_sha_verified=True,source_members=len(inventory),supplement_members=len(extra_inventory),models=0);dump(D/'REMOTE_VERIFIED.json',verified)
  mapping={x['path']:x for x in inventory};deleted=[]
  for p in list(arc.walk(RAW)):
   row=mapping[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and arc.sha(p)==row['sha256'];deleted.append(dict(path=row['path'],bytes=row['bytes']));p.unlink()
  links=[]
  for base,dirs,names in os.walk(RAW,followlinks=False):
   for name in dirs+names:
    p=Path(base,name)
    if p.is_symlink():links.append(str(p.relative_to(R)));p.unlink()
  cleanup=dict(passed=True,deleted_raw_bytes=sum(x['bytes']for x in deleted),manifest=deleted,removed_resource_links_only=links,old_unverified_raw_untouched=True,models=0);dump(D/'CLEANUP.json',cleanup);gh(['release','upload',TAG,D/'REMOTE_VERIFIED.json',D/'CLEANUP.json'],30);shutil.rmtree(O/'cloud');shutil.rmtree(O/'cloud-closure');shutil.rmtree(back)
 except BaseException as e:dump(D/'REMOTE_PENDING.json',dict(error=repr(e),raw_retained=not(D/'CLEANUP.json').exists(),no_automatic_retry=True,models=0))
 cmd(['git','add','--',str(D.relative_to(R))]);cmd(['git','commit','--only','-m','Retain observation delivery receipts without repeating source push','--',str(D.relative_to(R))]);dump(O/'CLOSED.json',dict(closed=True,models_authorized=False,remote_verified=(D/'REMOTE_VERIFIED.json').exists(),one_source_push_attempt=True,initial_pre_push_check_error_preserved=True));print(json.dumps(dict(commit=head,sync=sync,remote_verified=(D/'REMOTE_VERIFIED.json').exists())),flush=True)
if __name__=='__main__':main()
