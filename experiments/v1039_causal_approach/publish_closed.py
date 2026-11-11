"""One closed-component publication, streamed remote verification before cleanup."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1039_causal_approach';D=R/'records/nav2_v1039_20261111';RAW=R/'runs/v858_nav2_verified/v1039';H=R/'runs/v858_nav2_verified/v1024/dynamic_we'
TAG='phase-causal-observation-v1039-v1041-20261111';GH=R/'tools/phase_storage_20261107/vendor/gh';REPORT=R/'docs/RPCCR_CAUSAL_APPROACH_V1039_V1041_REPORT.md'
s=importlib.util.spec_from_file_location('v1039_stream_archive',R/'experiments/v1020_terminal_two_route_development/archive.py');arc=importlib.util.module_from_spec(s);s.loader.exec_module(arc)
NAMES=['v1034_portal_timed_source','v1035_signed_timed_input_source','v1036_recovery_seeded_timed_source','v1037_periodic_norm_source','v1038_staged_timed_source','v1039_causal_approach','v1040_approach_information_audit','v1041_causal_phase_alignment']
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def command(args,timeout=30):
 p=subprocess.run(list(map(str,args)),cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1500:])
 return p.stdout

def main():
 assert not(O/'PUBLICATION_CLAIM.json').exists()and not(O/'SOURCE_SYNC_CLAIM.json').exists(),'NO_RETRY';D.mkdir(exist_ok=True);dump(O/'PUBLICATION_CLAIM.json',dict(started=time.time(),models=0))
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 done=json.loads((O/'COMPLETION.json').read_text());assert done['closed']and done['passed']and done['audit']['passed'];assert json.loads((O/'APPROVAL.json').read_text())['models_authorized']is False
 assert arc.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(arc.sha(R/p)==h for p,h in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
 assert arc.sha(H/'FINAL_INDEPENDENT_AUDIT.json')=='46c3ccbd169fda14585fe668ca6c7603c05ef8b856dcd76606d8b2570506e195'
 info=json.loads((R/'runs/v1040_approach_information_audit/INFORMATION_AUDIT.json').read_text());assert info['passed'];cut=json.loads((R/'runs/v1041_causal_phase_alignment/FULL_CYCLE_CUT.json').read_text());assert cut['obstruction_proved'];phase=json.loads((R/'runs/v1041_causal_phase_alignment/RESULT.json').read_text());assert phase['models']==0
 summary=dict(component_passed=True,original_difficult_dynamic_passed=False,new_24_executed=0,actual=done['result'],independent_audit=done['audit'],information=info,full_cycle_cut=cut,phase_suffix_query=phase,guard_original=True,execution_lock_idle=True,models_authorized=False,old_failures_preserved=True,initial_auxiliary_thread_affinity_exception_preserved=True,scope='one safe observation component; no complete original goal route')
 dump(D/'FINAL_SUMMARY.json',summary);dump(O/'FINAL_INDEPENDENT_AUDIT.json',dict(passed=True,component_only=True,actual_saved_audit=done['audit'],source_freeze_all_sha_verified=True,original_old_audit_restored_sha_verified=True,accurate_counts=True,original_goal_arrival_claim=False,all_models_closed=True,models=0))
 paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',str(REPORT.relative_to(R)),*[str(Path('experiments')/n)for n in NAMES],str(D.relative_to(R))]
 files={R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',REPORT}
 for root in [*[R/'experiments'/n for n in NAMES],*[R/'runs'/n for n in NAMES],RAW,D]:
  files.update(p for p in arc.walk(root)if p.suffix not in ['.pyc','.so','.lock']and p.name not in ['PUBLICATION_CLAIM.json','publication.console'])
 # Required original-state witnesses, rather than an implicit unrecoverable local dependency.
 files.update(H/p for p in ['DYNAMIC_COMPLETE_PLAN.json','STATIC_COMPLETE_PLAN.json','STATIC_EXECUTION.json','CAUSAL_EVIDENCE.json','FINAL_INDEPENDENT_AUDIT.json','physics/SETUP.json','physics/scene_model.mjb','physics/NATIVE_TRACE.npz','physics/BODY_COMMANDS.json'])
 def budget():return sum(p.stat().st_size for n in NAMES for p in arc.walk(R/'runs'/n))+sum(p.stat().st_size for p in arc.walk(RAW))<2*1024**3
 record,inventory=arc.package(R,files,O/'cloud','v1039-causal-approach-v1041-followup',budget)
 dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag=TAG,archives=[record],restoration='tools/phase_storage_20261107/restore.py',original_dynamic_acceptance=False))
 dump(O/'FINALIZED.json',dict(passed=True,component_only=True,independent_audit_passed=True,local_source_and_decompressed_sha_verified=True,part_reassembly_sha_verified=True,original_goal_arrival_claim=False,models=0))
 dump(D/'FINALIZED.json',json.loads((O/'FINALIZED.json').read_text()))
 command(['git','add','--',*paths]);command(['git','diff','--cached','--check','--',*paths]);print(command(['git','diff','--cached','--stat','--',*paths]),flush=True)
 # No unrelated staged paths or >90MiB blobs are included by this path-limited commit.
 for path in command(['git','diff','--cached','--name-only','--',*paths]).splitlines():assert (R/path).stat().st_size<90*1024**2
 command(['git','commit','--only','-m','Verify original-task safe observation component and quantify remaining time-route obstruction','--',*paths]);head=command(['git','rev-parse','HEAD']).strip();dump(O/'SOURCE_SYNC_CLAIM.json',dict(commit=head,one_push=True,one_head_read=True))
 sync=dict(commit=head,push_succeeded=False,remote_head_verified=False)
 try:command(['git','push','origin','HEAD:main'],30);sync['push_succeeded']=True
 except BaseException as e:sync['push_error']=repr(e)
 try:sync['remote_head']=command(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except BaseException as e:sync['head_verification_error']=repr(e)
 dump(D/'SOURCE_SYNC_RESULT.json',sync);print(json.dumps(sync),flush=True)
 try:
  assert sync['push_succeeded']or sync['remote_head_verified'],'SOURCE_PUSH_UNCONFIRMED_RAW_RETAINED'
  def gh(args,timeout=60):return command([GH,*args,'--repo','frank8763/phase-'],timeout)
  notes=O/'RELEASE_NOTES.md';notes.write_text('V1039 original-task finite causal observation component PASS, 1.33048m; original full dynamic goal and24 NOT passed. New observation area reduction99.14%; narrowed full-cycle contract still obstructed. All errors and limits retained. Source '+head+'. Streamed per-part and per-member SHA verification is required before cleanup.\n')
  gh(['release','create',TAG,'--target',head,'--title','Phase V1039 certified causal observation and remaining timed-route diagnosis','--notes-file',notes,'--latest=false'],30)
  gh(['release','upload',TAG,*list((O/'cloud').iterdir()),D/'RECORD_INDEX.json',D/'FINAL_SUMMARY.json',D/'SOURCE_SYNC_RESULT.json',D/'FINALIZED.json',REPORT],120)
  back=O/'readback';back.mkdir(exist_ok=False)
  def provider(part):gh(['release','download',TAG,'--pattern',part['name'],'--dir',back],120);return back/part['name'],True
  arc.verify(record,inventory,provider);verified=dict(passed=True,release_url='https://github.com/frank8763/phase-/releases/tag/'+TAG,source_commit=head,source_remote_head_verified=sync['remote_head_verified'],all_remote_part_and_member_sha_verified=True,source_members=len(inventory),models=0);dump(D/'REMOTE_VERIFIED.json',verified)
  mapping={x['path']:x for x in inventory};deleted=[]
  for p in list(arc.walk(RAW)):
   row=mapping[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and arc.sha(p)==row['sha256'];deleted.append(dict(path=row['path'],bytes=row['bytes']));p.unlink()
  links=[]
  for base,dirs,names in os.walk(RAW,followlinks=False):
   for name in dirs+names:
    p=Path(base,name)
    if p.is_symlink():links.append(str(p.relative_to(R)));p.unlink()
  cleanup=dict(passed=True,deleted_raw_bytes=sum(x['bytes']for x in deleted),manifest=deleted,removed_resource_links_only=links,old_unverified_raw_untouched=True,models=0);dump(D/'CLEANUP.json',cleanup);gh(['release','upload',TAG,D/'REMOTE_VERIFIED.json',D/'CLEANUP.json'],30);shutil.rmtree(O/'cloud');shutil.rmtree(back)
 except BaseException as e:dump(D/'REMOTE_PENDING.json',dict(error=repr(e),raw_retained=not(D/'CLEANUP.json').exists(),no_automatic_retry=True,models=0))
 command(['git','add','--',str(D.relative_to(R))]);command(['git','commit','--only','-m','Retain causal observation delivery receipts without repeating source push','--',str(D.relative_to(R))]);dump(O/'CLOSED.json',dict(closed=True,models_authorized=False,remote_verified=(D/'REMOTE_VERIFIED.json').exists(),one_source_push_attempt=True));print(json.dumps(dict(commit=head,sync=sync,remote_verified=(D/'REMOTE_VERIFIED.json').exists())),flush=True)
if __name__=='__main__':main()
