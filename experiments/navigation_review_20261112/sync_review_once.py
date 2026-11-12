"""Single new-review push and immutable Release evidence readback, no model."""
import sys,json,subprocess,hashlib,time,urllib.request,urllib.parse,shutil,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/navigation_review_20261112';D=R/'records/navigation_review_20261112';OLD=R/'records/nav2_v1080_v1082_20261112';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not(D/'GIT_SYNC_CLAIM.json').exists();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();dump(D/'GIT_SYNC_CLAIM.json',dict(head=head,at=time.time(),new_review_only=True,one_push=True));sync=dict(head=head,push_succeeded=False,remote_head_verified=False)
 try:
  p=subprocess.run(['git','push','origin','HEAD:main'],cwd=R,capture_output=True,text=True,timeout=30);sync.update(push_succeeded=p.returncode==0,diagnostic=(p.stdout+p.stderr)[-1000:]);q=subprocess.run(['git','ls-remote','origin','refs/heads/main'],cwd=R,capture_output=True,text=True,timeout=5);remote=q.stdout.split()[0]if q.returncode==0 and q.stdout.split()else None;sync.update(remote_head=remote,remote_head_verified=remote==head)
 except subprocess.TimeoutExpired as e:sync['error']='bounded sync timeout'
 dump(D/'GIT_SYNC_RESULT.json',sync);print(json.dumps(sync),flush=True)
 if not(sync['push_succeeded']and sync['remote_head_verified']):return 1
 assert not(D/'DELIVERY_CLAIM.json').exists();dump(D/'DELIVERY_CLAIM.json',dict(head=head,at=time.time(),one_release=True))
 gh=R/'tools/phase_storage_20261107/vendor/gh';t=subprocess.run([str(gh),'auth','token','--hostname','github.com'],capture_output=True,text=True,check=True,timeout=5).stdout.strip();assert t
 class NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*args):raise RuntimeError('AUTH_REDIRECT_REFUSED')
 api=urllib.request.build_opener(NoRedirect())
 def post(url,data):
  assert url.startswith(('https://api.github.com/repos/frank8763/phase-/releases','https://uploads.github.com/repos/frank8763/phase-/releases/'))
  req=urllib.request.Request(url,data=data,method='POST',headers={'Authorization':'Bearer '+t,'Content-Type':'application/json'if url.endswith('/releases')else'application/octet-stream','Accept':'application/vnd.github+json','User-Agent':'Phase-review-evidence','X-GitHub-Api-Version':'2022-11-28'})
  with api.open(req,timeout=60)as f:return json.load(f)
 index=json.loads((D/'RECORD_INDEX.json').read_text());tag=index['release_tag'];release=post('https://api.github.com/repos/frank8763/phase-/releases',json.dumps(dict(tag_name=tag,target_commitish=head,name='Phase dynamic-navigation full review and failed V1080/V1082 evidence',body='Original failures retained: V1080 actual longitudinal speed breach; V1082 new one-step guard infeasible before request15. Full source/native evidence and zero-model retrospective, exact saved rejection, cleanup manifests. No new navigation, training, or acceptance claim.',make_latest='false')).encode());upload=release['upload_url'].split('{')[0];assets={}
 files=[*sorted((R/'runs/v1082_guarded_saved_continuation/cloud').iterdir()),*sorted((O/'cloud').iterdir()),D/'RECORD_INDEX.json',D/'REVIEW_SUMMARY.json',D/'CLEANUP_RESULT.json',D/'GIT_SYNC_RESULT.json']
 for p in files:
  assert p.is_file()and not p.is_symlink();row=post(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes());assert row['size']==p.stat().st_size
  if row.get('digest'):assert row['digest']=='sha256:'+sha(p)
  assets[p.name]=row['browser_download_url']
 s=importlib.util.spec_from_file_location('review_remote_archive_verifier',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(s);s.loader.exec_module(arc);back=O/'remote_readback';back.mkdir(exist_ok=False)
 def provider(part):
  url=assets[part['name']];assert url.startswith('https://github.com/frank8763/phase-/releases/download/'+tag+'/');p=back/part['name']
  with urllib.request.urlopen(url,timeout=60)as src,p.open('xb')as f:shutil.copyfileobj(src,f,1048576)
  return p,True
 inventories=[json.loads((OLD/'INVENTORY.json').read_text())['files'],json.loads((D/'SUPPLEMENT_INVENTORY.json').read_text())['files']]
 for record,inventory in zip(index['archives'],inventories):arc.verify(record,inventory,provider)
 source_checks=[]
 for name in ['README.md','CURRENT_EXPERIMENT.json','docs/PHASE_NAVIGATION_FULL_REVIEW_20261112.md','experiments/v1081_transient_speed_guard/governor.py']:
  with urllib.request.urlopen('https://raw.githubusercontent.com/frank8763/phase-/'+head+'/'+name,timeout=10)as f:data=f.read()
  assert hashlib.sha256(data).hexdigest()==sha(R/name);source_checks.append(name)
 result=dict(passed=True,release_url=release['html_url'],source_head=head,both_archives_all_source_decompressed_sha_verified=True,total_source_members=sum(len(x)for x in inventories),critical_source_remote_byte_readbacks=source_checks,raw_retained=True,models=0,integrations=0,old_failures_preserved=True);dump(D/'REMOTE_VERIFIED.json',result);p=D/'REMOTE_VERIFIED.json';row=post(upload+'?name='+p.name,p.read_bytes())
 with urllib.request.urlopen(row['browser_download_url'],timeout=10)as f:assert hashlib.sha256(f.read()).hexdigest()==sha(p)
 back.rmdir();print(json.dumps(result),flush=True);return 0
if __name__=='__main__':
 try:sys.exit(main())
 except BaseException as e:
  if isinstance(e,SystemExit):raise
  dump(D/'DELIVERY_ERROR.json',dict(error=repr(e),raw_retained=True,no_automatic_retry=True,models=0));print(json.dumps(dict(delivery_failed=True,error=repr(e),raw_retained=True)),flush=True);sys.exit(1)
