"""One new qualification archive/sync; never retries an older batch's sync.

Public Release readback carries no authorization header across redirects.
Credential is read through gh's configured credential interface, never logged,
and sent only to the two official GitHub API upload endpoints for this repo.
"""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,time,urllib.parse,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1054_atomic_publish';D=R/'records/nav2_v1054_20261111';GH=R/'tools/phase_storage_20261107/vendor/gh';TAG='phase-atomic-publish-v1054-20261111'
spec=importlib.util.spec_from_file_location('v1052_stream_archive',R/'experiments/v1051_retained_corridor_entry/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def cmd(args,timeout=30):
 p=subprocess.run([str(a)for a in args],cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1000:])
 return p.stdout
def main():
 assert not(O/'PUBLISH_CLAIM.json').exists(),'NO_RETRY';dump(O/'PUBLISH_CLAIM.json',dict(at=time.time(),models=0));D.mkdir(exist_ok=True);lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert arc.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 qualification=json.loads((O/'QUALIFICATION.json').read_text());independent=json.loads((O/'INDEPENDENT_SOFTWARE_AUDIT.json').read_text());assert qualification['passed']and independent['passed']
 dump(D/'FINAL_SUMMARY.json',dict(new_models=0,new_integrations=0,software_epochs=11,independent_native_intervals=independent['independently_regenerated_native_intervals'],actual_goal_passed=False,physical_ready=False,original_v1053_publication_failure_retained=True,model_authority=False))
 files={R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'docs/RPCCR_ATOMIC_PUBLICATION_V1053_V1054_REPORT.md',R/'records/nav2_v1053_20261111/SOFTWARE_CACHE_CLEANUP.json'}
 for root in [C,O,D]:
  files.update(p for p in arc.walk(root)if p.suffix not in ['.pyc','.so','.lock']and p.name not in ['publish.console','PUBLISH_CLAIM.json'])
 record,inventory=arc.package(R,files,O/'cloud','v1054-atomic-publish-evidence',lambda:sum(p.stat().st_size for p in arc.walk(O))<2*1024**3);dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag=TAG,archives=[record],restoration='tools/phase_storage_20261107/restore.py',selected_input_dependency_archive=True,not_retry_of_old_release=True));dump(D/'FINALIZED.json',dict(passed=True,models=0,source_and_decompressed_sha_verified=True,scientific_status='ZERO_MODEL_SAVED_STATE_QUALIFICATION_ONLY',actual_dynamic_accepted=False));dump(O/'FINALIZED.json',json.loads((D/'FINALIZED.json').read_text()))
 paths=['records/nav2_v1053_20261111/SOFTWARE_CACHE_CLEANUP.json','CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_ATOMIC_PUBLICATION_V1053_V1054_REPORT.md','experiments/v1054_atomic_publish',str(D.relative_to(R))];cmd(['git','add','--',*paths]);cmd(['git','diff','--cached','--check','--',*paths]);cmd(['git','commit','--only','-m','Add atomic publication candidate and preserve actual publication timeout','--',*paths]);head=cmd(['git','rev-parse','HEAD']).strip();dump(O/'GIT_SYNC_CLAIM.json',dict(commit=head,one_push=True,one_head_read=True));sync=dict(commit=head,push_succeeded=False,remote_head_verified=False)
 try:cmd(['git','push','origin','HEAD:main'],30);sync['push_succeeded']=True
 except BaseException as e:sync['push_error']=repr(e)
 try:sync['remote_head']=cmd(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
 except BaseException as e:sync['head_error']=repr(e)
 dump(D/'GIT_SYNC_RESULT.json',sync)
 try:
  assert sync['push_succeeded']or sync['remote_head_verified'];token=cmd([GH,'auth','token','--hostname','github.com'],5).strip();assert token
  class NoCredentialRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,req,fp,code,msg,headers,newurl):raise RuntimeError('Authenticated API redirect refused')
  api=urllib.request.build_opener(NoCredentialRedirect())
  def request(url,data,ctype='application/json'):
   assert url.startswith(('https://api.github.com/repos/frank8763/phase-/releases','https://uploads.github.com/repos/frank8763/phase-/releases/'))
   req=urllib.request.Request(url,data=data,method='POST',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':ctype,'X-GitHub-Api-Version':'2022-11-28','User-Agent':'Phase-evidence-publisher'})
   with api.open(req,timeout=60)as response:return json.load(response)
  release=request('https://api.github.com/repos/frank8763/phase-/releases',json.dumps(dict(tag_name=TAG,target_commitish=head,name='V1054 atomic publication software qualification; dynamic task not passed',body='V1053 actual third publication timeout kept. V1054 same native controls, allocation before snapshot, readonly atomic handoff. Four timing cases,500 single-CPU samples and11 full software epochs independently regenerated. Zero new physical models; dynamic task not accepted. SHA-indexed latest actual publication input included.',make_latest='false')).encode());upload=release['upload_url'].split('{')[0];assets={}
  for p in [*sorted((O/'cloud').iterdir()),D/'RECORD_INDEX.json',D/'FINAL_SUMMARY.json',D/'FINALIZED.json',D/'GIT_SYNC_RESULT.json']:
   result=request(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes(),'application/octet-stream');assert result['size']==p.stat().st_size;assets[p.name]=result['browser_download_url']
  back=O/'readback';back.mkdir()
  def provider(part):
   url=assets[part['name']];assert url.startswith('https://github.com/frank8763/phase-/releases/download/'+TAG+'/');p=back/part['name']
   # Public URL: no token is forwarded to the asset CDN.
   with urllib.request.urlopen(url,timeout=60)as src,p.open('xb')as out:shutil.copyfileobj(src,out,1024**2)
   return p,True
  arc.verify(record,inventory,provider);verified=dict(passed=True,release_url=release['html_url'],source_members=len(inventory),all_parts_and_decompressed_members_sha_verified=True,old_release_syncs_not_retried=True,models=0);dump(D/'REMOTE_VERIFIED.json',verified)
  # Only the latest actual trace now included and verified in this NEW input
  # dependency archive may be cleaned. Other unverified old roots stay intact.
  mapping={x['path']:x for x in inventory};deleted=[]
  for p in [*arc.walk(O/'software_full_executor'),*arc.walk(O/'software_producer_deadline')]:
   row=mapping[str(p.relative_to(R))];assert arc.sha(p)==row['sha256'];deleted.append(dict(path=row['path'],bytes=row['bytes']));p.unlink()
  dump(D/'CLEANUP.json',dict(deleted_bytes=sum(x['bytes']for x in deleted),manifest=deleted,verified_under_new_input_dependency_archive=True,old_unverified_raw_untouched=True))
  for p in [D/'REMOTE_VERIFIED.json',D/'CLEANUP.json']:request(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes(),'application/octet-stream')
  shutil.rmtree(O/'cloud');shutil.rmtree(back)
 except BaseException as e:dump(D/'REMOTE_PENDING.json',dict(error=repr(e),raw_retained=True,no_retry=True,models=0))
 cmd(['git','add','--',str(D.relative_to(R))]);cmd(['git','commit','--only','-m','Record atomic publication delivery receipt without another push','--',str(D.relative_to(R))]);dump(O/'CLOSED.json',dict(closed=True,models_authorized=False,remote_verified=(D/'REMOTE_VERIFIED.json').exists(),no_retry=True));print(json.dumps(dict(closed=True,source_remote=sync['remote_head_verified'],evidence_remote=(D/'REMOTE_VERIFIED.json').exists(),models=0)))
if __name__=='__main__':main()
