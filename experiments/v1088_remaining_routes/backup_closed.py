"""Release-only closed-evidence backup and verified cache cleanup; zero models."""
import sys, json, time, signal, subprocess, urllib.request, urllib.parse, shutil, importlib.util, fcntl
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1088_remaining_routes';D=R/'records/nav2_v1088_preparation_20261112'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
spec=importlib.util.spec_from_file_location('closed_backup_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 assert not(D/'DELIVERY_CLAIM.json').exists()
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert arc.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 dump(D/'DELIVERY_CLAIM.json',dict(at=time.time(),release_only=True,push_attempts=0,models=0))
 def timeout(*_):raise TimeoutError('BOUNDED_CLOSED_EVIDENCE_DELIVERY')
 signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,900)
 token=subprocess.check_output([str(R/'tools/phase_storage_20261107/vendor/gh'),'auth','token','--hostname','github.com'],text=True,timeout=5).strip();assert token
 class NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*args):raise RuntimeError('AUTHENTICATED_REDIRECT_REFUSED')
 api=urllib.request.build_opener(NoRedirect())
 def post(url,data,ctype='application/json'):
  assert url.startswith(('https://api.github.com/repos/frank8763/phase-/releases','https://uploads.github.com/repos/frank8763/phase-/releases/'))
  req=urllib.request.Request(url,data=data,method='POST',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':ctype,'User-Agent':'Phase-closed-evidence','X-GitHub-Api-Version':'2022-11-28'})
  with api.open(req,timeout=60)as response:return json.load(response)
 pinned=set(json.loads((R/'experiments/v1087_ns_repeat_after_shutdown/SOURCE_FREEZE.json').read_text())['files'])
 results=[]
 try:
  for version,run in [('v1085','v1085_fresh_ns_validation'),('v1085_entry','v1085_pose_entry_relay'),('v1086','v1086_ns_complete_repeat'),('v1087','v1087_ns_repeat_after_shutdown')]:
   recordroot=R/('records/nav2_'+version+'_20261112');root=R/'runs'/run;index=json.loads((recordroot/'RECORD_INDEX.json').read_text());record=index['archives'][0];inventory=json.loads((recordroot/'INVENTORY.json').read_text())['files'];cloud=root/'cloud';tag=index['release_tag']
   assert not(recordroot/'DELIVERY_CLAIM.json').exists() and not(recordroot/'REMOTE_VERIFIED.json').exists()
   dump(recordroot/'DELIVERY_CLAIM.json',dict(at=time.time(),release_only=True,no_retries=True))
   release=post('https://api.github.com/repos/frank8763/phase-/releases',json.dumps(dict(tag_name=tag,target_commitish='main',name='Phase '+version+' closed navigation evidence',body='Immutable closed evidence. V1085 entry failed; V1085_entry main arrived and supplemental audit passed; V1086 shutdown interrupted; V1087 full repeat passed. Original outcomes preserved. New source commits are local pending one final bounded source push; this Release attaches complete recorded sources and SHA inventories. No new physical work.',make_latest='false')).encode())
   upload=release['upload_url'].split('{')[0];urls={}
   for p in [*sorted(cloud.iterdir()),recordroot/'RECORD_INDEX.json',recordroot/'FINAL_SUMMARY.json',recordroot/'FINALIZED.json',recordroot/'INVENTORY.json']:
    row=post(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes(),'application/octet-stream');assert row['size']==p.stat().st_size;urls[p.name]=row['browser_download_url']
   back=O/('remote_readback_'+version);back.mkdir(exist_ok=False)
   def provider(part):
    p=back/part['name']
    with urllib.request.urlopen(urls[part['name']],timeout=60)as src,p.open('xb')as dst:shutil.copyfileobj(src,dst,1024**2)
    return p,True
   arc.verify(record,inventory,provider);back.rmdir()
   verified=dict(passed=True,release_url=release['html_url'],source_members=len(inventory),all_parts_and_decompressed_members_sha_verified=True,models=0,integrations=0,push_deferred=True)
   dump(recordroot/'REMOTE_VERIFIED.json',verified)
   # Persist a byte/hash deletion list first. Keep all frozen inputs and small summaries.
   candidates=[];by_path={row['path']:row for row in inventory}
   taskroot=R/'runs/v858_nav2_verified'/version
   for p in taskroot.rglob('*'):
    if not p.is_file()or p.is_symlink()or str(p.relative_to(R))in pinned:continue
    key=str(p.relative_to(R));row=by_path.get(key)
    if p.name=='scene_model.mjb':
     assert arc.sha(p)=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8'
     continue  # shared canonical model excluded from this archive; retain locally
    if row is not None and (p.stat().st_size>1024**2 or 'certificates'in p.parts):
     assert arc.sha(p)==row['sha256'];candidates.append(row)
   for p in cloud.iterdir():
    if p.is_file()and '.part'in p.name:candidates.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=arc.sha(p)))
   dump(recordroot/'CLEANUP_MANIFEST.json',dict(remote_verified=True,files=candidates))
   for row in candidates:
    p=R/row['path'];assert not p.is_symlink()and p.resolve().is_relative_to(R/'runs')and arc.sha(p)==row['sha256'];p.unlink()
   cleanup=dict(passed=True,logical_bytes_removed=sum(x['bytes']for x in candidates),files_removed=len(candidates),raw_required_remote_verified=True,frozen_inputs_and_small_metadata_retained=True)
   dump(recordroot/'CLEANUP.json',cleanup)
   for p in [recordroot/'REMOTE_VERIFIED.json',recordroot/'CLEANUP_MANIFEST.json',recordroot/'CLEANUP.json']:
    post(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes(),'application/octet-stream')
   results.append(dict(version=version,**verified,cleanup=cleanup));dump(D/'RESULTS.json',results);print(json.dumps(dict(version=version,remote_verified=True,removed=cleanup['logical_bytes_removed'])),flush=True)
  dump(D/'COMPLETION.json',dict(passed=True,closed=True,results=results,models=0,integrations=0,push_attempts=0))
 except BaseException as e:
  dump(D/'COMPLETION.json',dict(passed=False,closed=True,error=repr(e),completed=results,unverified_raw_retained=True,models=0,integrations=0));print(json.dumps(dict(error=repr(e),unverified_raw_retained=True)),flush=True)
 finally:signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
