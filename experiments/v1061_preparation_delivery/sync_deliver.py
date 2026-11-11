"""One bounded source push, new Release, streaming readback, exact cleanup."""
import fcntl,importlib.util,json,shutil,subprocess,time,urllib.parse,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1061_three_route_readiness';D=R/'records/nav2_v1061_20261111';C=R/'experiments/v1061_three_route_readiness';TAG='phase-three-route-software-v1061-20261111'
spec=importlib.util.spec_from_file_location('v1061_delivery_archive',C/'archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def cmd(args,timeout):
 p=subprocess.run([str(x)for x in args],cwd=R,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1000:])
 return p.stdout

def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert arc.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert not(O/'GIT_SYNC_CLAIM.json').exists()and not(D/'GIT_SYNC_RESULT.json').exists(),'NO_SYNC_RETRY';assert not json.loads((O/'APPROVAL.json').read_text())['models_authorized'];assert all(arc.sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());head=cmd(['git','rev-parse','HEAD'],5).strip();dump(O/'GIT_SYNC_CLAIM.json',dict(commit=head,one_push_max30s=True,one_remote_read_max5s=True));result=dict(commit=head,push_succeeded=False,remote_head_verified=False,models=0)
 try:cmd(['git','push','origin','HEAD:main'],30);result['push_succeeded']=True
 except BaseException as e:result['push_error']=repr(e)
 try:result['remote_head']=cmd(['git','ls-remote','origin','refs/heads/main'],5).split()[0];result['remote_head_verified']=result['remote_head']==head
 except BaseException as e:result['head_verification_error']=repr(e)
 dump(D/'GIT_SYNC_RESULT.json',result)
 try:
  assert result['remote_head_verified'],'SOURCE_REMOTE_HEAD_UNKNOWN_RAW_RETAINED'
  assert not(O/'RELEASE_DELIVERY_CLAIM.json').exists(),'NO_RELEASE_RETRY';dump(O/'RELEASE_DELIVERY_CLAIM.json',dict(at=time.time(),no_retries=True));token=cmd([R/'tools/phase_storage_20261107/vendor/gh','auth','token','--hostname','github.com'],5).strip();assert token
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*args):raise RuntimeError('AUTHENTICATED_REDIRECT_REFUSED')
  opener=urllib.request.build_opener(NoRedirect())
  def post(url,data,ctype='application/json'):
   assert url.startswith(('https://api.github.com/repos/frank8763/phase-/releases','https://uploads.github.com/repos/frank8763/phase-/releases/'));request=urllib.request.Request(url,data=data,method='POST',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':ctype,'User-Agent':'Phase-zero-model-evidence','X-GitHub-Api-Version':'2022-11-28'})
   with opener.open(request,timeout=60)as response:return json.load(response)
  release=post('https://api.github.com/repos/frank8763/phase-/releases',json.dumps(dict(tag_name=TAG,target_commitish=head,name='V1061 declared EW north 0.10m course: software preparation only',body='User-selected new course; original EW rejection and all old failures retained. Three static input sources and shared software qualification passed. Zero physical models/navigation/MuJoCo integrations. No three-route physical or new24 success claim. Source '+head,make_latest='false')).encode());upload=release['upload_url'].split('{')[0];assets={}
  for p in [*sorted((O/'cloud').iterdir()),D/'RECORD_INDEX.json',D/'FINAL_SUMMARY.json',D/'GIT_SYNC_RESULT.json',D/'FINAL_INDEPENDENT_AUDIT.json']:
   row=post(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes(),'application/octet-stream');assert row['size']==p.stat().st_size;assets[p.name]=row['browser_download_url'];print('Uploaded '+p.name,flush=True)
  index=json.loads((D/'RECORD_INDEX.json').read_text());record=index['archives'][0];inventory=json.loads((O/'cloud'/(record['group']+'.INVENTORY.json')).read_text())['files'];back=O/'readback';back.mkdir(exist_ok=False)
  def provider(part):
   url=assets[part['name']];assert url.startswith('https://github.com/frank8763/phase-/releases/download/'+TAG+'/');path=back/part['name']
   with urllib.request.urlopen(url,timeout=60)as source,path.open('xb')as out:shutil.copyfileobj(source,out,1048576)
   return path,True
  arc.verify(record,inventory,provider);back.rmdir();verified=dict(passed=True,release_url=release['html_url'],source_members=len(inventory),all_parts_and_decompressed_members_sha_verified=True,models=0);dump(D/'REMOTE_VERIFIED.json',verified);print('All remote parts and source members verified',flush=True)
  kept=[];deleted=[]
  for row in inventory:
   path=R/row['path']
   if not path.is_relative_to(O):continue
   relative=path.relative_to(O)
   if path.stat().st_size<=1048576 and len(relative.parts)==1:kept.append(row['path']);continue
   assert path.is_file()and not path.is_symlink()and path.resolve().is_relative_to(O)and arc.sha(path)==row['sha256'];deleted.append(dict(path=row['path'],bytes=row['bytes'],sha256=row['sha256']));path.unlink()
  for path in sorted([p for p in O.rglob('*')if p.is_dir()and p.name not in ['cloud']],key=lambda p:len(p.parts),reverse=True):
   if path.is_relative_to(O/'cloud'):continue
   if not any(path.iterdir()):path.rmdir()
  dump(D/'CLEANUP.json',dict(passed=True,logical_cache_bytes_removed=sum(x['bytes']for x in deleted),files=deleted,small_metadata_retained=kept,only_this_batch_paths=True,old_unverified_raw_untouched=True));final=json.loads((D/'FINALIZED.json').read_text());final.update(remote_delivery_pending=False,remote_all_member_sha_verified=True,required_raw_cache_cleaned=True);dump(D/'FINALIZED.json',final)
  for p in [D/'REMOTE_VERIFIED.json',D/'CLEANUP.json',D/'FINALIZED.json']:
   row=post(upload+'?name='+p.name,p.read_bytes(),'application/octet-stream');assert row['size']==p.stat().st_size
  shutil.rmtree(O/'cloud');print(json.dumps(dict(remote_verified=True,removed_logical_bytes=sum(x['bytes']for x in deleted),models=0)),flush=True)
 except BaseException as e:
  dump(D/'DELIVERY_PENDING.json',dict(error=repr(e),no_automatic_retry=True,unverified_raw_retained=True,models=0));print('Delivery incomplete: '+repr(e),flush=True)
if __name__=='__main__':main()
