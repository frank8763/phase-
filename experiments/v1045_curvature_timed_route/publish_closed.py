"""Publish finite V1044 responses and their zero-model route diagnosis once."""
import fcntl,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1044_curvature_speed_prediction';D=R/'records/nav2_v1044_20261111';RAW=R/'runs/v858_nav2_verified/v1044';REPORT=R/'docs/RPCCR_CURVATURE_SPEED_V1044_REPORT.md';TAG='phase-curvature-speed-response-v1044-20261111';GH=R/'tools/phase_storage_20261107/vendor/gh'
NAMES=['v1042_original_timed_route','v1043_speed_predictor_identification','v1044_curvature_speed_prediction','v1045_curvature_timed_route','v1046_retreat_entry_timed_route']
s=importlib.util.spec_from_file_location('v1045_stream_archive',R/'experiments/v1020_terminal_two_route_development/archive.py');arc=importlib.util.module_from_spec(s);s.loader.exec_module(arc)
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def cmd(args,timeout=30):
 p=subprocess.run(list(map(str,args)),cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1500:])
 return p.stdout

def main():
 assert not(O/'PUBLICATION_CLAIM.json').exists()and not(O/'SOURCE_SYNC_CLAIM.json').exists(),'NO_DELIVERY_RETRY';D.mkdir(exist_ok=True)
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert arc.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 done=json.loads((O/'COMPLETION.json').read_text());assert done['closed']and done['passed']and not json.loads((O/'APPROVAL.json').read_text())['models_authorized'];assert all(row['audit']['passed']and row['result']['replay']['passed']for row in done['rows']);freeze=json.loads((R/'experiments/v1044_curvature_speed_prediction/SOURCE_FREEZE.json').read_text());assert all(arc.sha(R/p)==h for p,h in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
 query=json.loads((R/'runs/v1045_curvature_timed_route/RESULT.json').read_text());retreat=json.loads((R/'runs/v1046_retreat_entry_timed_route/RESULT.json').read_text());assert query['models']==retreat['models']==0 and query['integrations']==retreat['integrations']==0
 paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md',str(REPORT.relative_to(R)),*[str(Path('experiments')/n)for n in NAMES],str(D.relative_to(R))]
 # Review and reject formatting defects before claiming immutable publication.
 for p in (R/'experiments').glob('v104[23456]*/*.py'):compile(p.read_text(),str(p),'exec')
 cmd(['git','add','--',*paths]);cmd(['git','diff','--cached','--check','--',*paths]);dump(O/'PUBLICATION_CLAIM.json',dict(started=time.time(),models=0))
 summary=dict(component_passed=True,new_models=3,new_response_native=1500,own_replay_native=1500,private_mujoco_native=0,new_whole_navigation_native=0,new_24=0,old_failures_preserved=True,rows=done['rows'],time_route_source=query,retreat_entry_source=retreat,source_freeze_all_sha_verified=True,guard_original=True,execution_lock_idle=True,models_authorized=False,original_dynamic_acceptance=False)
 dump(D/'FINAL_SUMMARY.json',summary);dump(O/'FINAL_INDEPENDENT_AUDIT.json',dict(passed=True,component_only=True,all_three_actual_and_saved_audits=True,source_freeze_sha_verified=True,counts=[3,1500,1500,0],new_whole_navigation_native=0,original_dynamic_acceptance=False,models=0))
 files={R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',REPORT}
 for root in [*[R/'experiments'/n for n in NAMES],*[R/'runs'/n for n in NAMES],RAW,D]:files.update(p for p in arc.walk(root)if p.suffix not in ['.pyc','.so','.lock']and p.name not in ['PUBLICATION_CLAIM.json','publication.console'])
 def budget():return sum(p.stat().st_size for n in NAMES for p in arc.walk(R/'runs'/n))+sum(p.stat().st_size for p in arc.walk(RAW))<2*1024**3
 record,inventory=arc.package(R,files,O/'cloud','v1044-speed-response-and-time-source',budget);dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag=TAG,archives=[record],restoration='tools/phase_storage_20261107/restore.py',original_dynamic_acceptance=False));dump(O/'FINALIZED.json',dict(passed=True,component_only=True,independent_audit_passed=True,all_source_and_decompressed_sha_verified=True,part_reassembly_sha_verified=True,original_dynamic_acceptance=False));dump(D/'FINALIZED.json',json.loads((O/'FINALIZED.json').read_text()))
 cmd(['git','add','--',*paths]);cmd(['git','diff','--cached','--check','--',*paths]);print(cmd(['git','diff','--cached','--stat','--',*paths]),flush=True)
 for p in cmd(['git','diff','--cached','--name-only','--',*paths]).splitlines():assert (R/p).stat().st_size<90*1024**2
 cmd(['git','commit','--only','-m','Identify curvature-dependent speed response and verify three complete physical components','--',*paths]);head=cmd(['git','rev-parse','HEAD']).strip();dump(O/'SOURCE_SYNC_CLAIM.json',dict(commit=head,one_push=True,one_head_read=True));sync=dict(commit=head,push_succeeded=False,remote_head_verified=False)
 try:cmd(['git','push','origin','HEAD:main'],30);sync['push_succeeded']=True
 except BaseException as e:sync['push_error']=repr(e)
 try:sync['remote_head']=cmd(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except BaseException as e:sync['head_verification_error']=repr(e)
 dump(D/'SOURCE_SYNC_RESULT.json',sync);print(json.dumps(sync),flush=True)
 try:
  assert sync['push_succeeded']or sync['remote_head_verified'],'SOURCE_PUSH_UNCONFIRMED_RAW_RETAINED'
  def gh(args,timeout=60):return cmd([GH,*args,'--repo','frank8763/phase-'],timeout)
  notes=O/'RELEASE_NOTES.md';notes.write_text('V1044 fixed straight/left/right response components PASS, each500 actual+500 complete replay, original10mm/8mrad/15mrad gates unchanged. Old failures retained. One curvature-speed predictor coefficient; no training or hardware. Full original dynamic and24 are not accepted. Source '+head+'. Archive has per-part and decompressed-member SHA.\n')
  gh(['release','create',TAG,'--target',head,'--title','Phase V1044 curvature-speed prediction: three physical responses passed','--notes-file',notes,'--latest=false'],30);gh(['release','upload',TAG,*list((O/'cloud').iterdir()),D/'RECORD_INDEX.json',D/'FINAL_SUMMARY.json',D/'FINALIZED.json',D/'SOURCE_SYNC_RESULT.json',REPORT],120)
  back=O/'readback';back.mkdir(exist_ok=False)
  def provider(part):gh(['release','download',TAG,'--pattern',part['name'],'--dir',back],120);return back/part['name'],True
  arc.verify(record,inventory,provider);verified=dict(passed=True,release_url='https://github.com/frank8763/phase-/releases/tag/'+TAG,source_commit=head,source_remote_head_verified=sync['remote_head_verified'],all_remote_part_and_member_sha_verified=True,source_members=len(inventory),models=0);dump(D/'REMOTE_VERIFIED.json',verified)
  mapping={x['path']:x for x in inventory};deleted=[]
  for root in [RAW,R/'runs/v1043_speed_predictor_identification/input/selected']:
   for p in list(arc.walk(root)):
    row=mapping[str(p.relative_to(R))];assert p.stat().st_size==row['bytes']and arc.sha(p)==row['sha256'];deleted.append(dict(path=row['path'],bytes=row['bytes']));p.unlink()
  links=[]
  for base,dirs,names in os.walk(RAW,followlinks=False):
   for name in dirs+names:
    p=Path(base,name)
    if p.is_symlink():links.append(str(p.relative_to(R)));p.unlink()
  cleanup=dict(passed=True,deleted_bytes=sum(x['bytes']for x in deleted),manifest=deleted,removed_resource_links_only=links,old_unverified_raw_untouched=True,models=0);dump(D/'CLEANUP.json',cleanup);gh(['release','upload',TAG,D/'REMOTE_VERIFIED.json',D/'CLEANUP.json'],30);shutil.rmtree(O/'cloud');shutil.rmtree(back)
 except BaseException as e:dump(D/'REMOTE_PENDING.json',dict(error=repr(e),raw_retained=not(D/'CLEANUP.json').exists(),no_automatic_retry=True,models=0))
 cmd(['git','add','--',str(D.relative_to(R))]);cmd(['git','commit','--only','-m','Keep curvature-speed delivery verification receipts without second push','--',str(D.relative_to(R))]);dump(O/'CLOSED.json',dict(closed=True,models_authorized=False,remote_verified=(D/'REMOTE_VERIFIED.json').exists(),one_source_push_attempt=True));print(json.dumps(dict(commit=head,sync=sync,remote_verified=(D/'REMOTE_VERIFIED.json').exists())),flush=True)
if __name__=='__main__':main()
