"""Bounded new-release delivery using official GitHub endpoints, no retries."""
import json,shutil,subprocess,urllib.parse,urllib.request
from kernel import R,load
def deliver(record,inventory,cloud,records,tag,head,summary):
 arc=load('v1077_speed_delivery_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');gh=R/'tools/phase_storage_20261107/vendor/gh';proc=subprocess.run([str(gh),'auth','token','--hostname','github.com'],capture_output=True,text=True,check=True,timeout=5);token=proc.stdout.strip();assert token
 class NoCredentialRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*args):raise RuntimeError('Authenticated endpoint redirect refused')
 api=urllib.request.build_opener(NoCredentialRedirect())
 def post(url,data,ctype='application/json'):
  assert url.startswith(('https://api.github.com/repos/frank8763/phase-/releases','https://uploads.github.com/repos/frank8763/phase-/releases/'))
  req=urllib.request.Request(url,data=data,method='POST',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':ctype,'User-Agent':'Phase-bounded-evidence','X-GitHub-Api-Version':'2022-11-28'})
  with api.open(req,timeout=60)as response:return json.load(response)
 release=post('https://api.github.com/repos/frank8763/phase-/releases',json.dumps(dict(tag_name=tag,target_commitish=head,name='V1077–V1078 speed response and saved-NS continuation',body=summary,make_latest='false')).encode());upload=release['upload_url'].split('{')[0];assets={}
 for p in [*sorted(cloud.iterdir()),records/'RECORD_INDEX.json',records/'FINAL_SUMMARY.json',records/'FINALIZED.json',records/'GIT_SYNC_RESULT.json']:
  row=post(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes(),'application/octet-stream');assert row['size']==p.stat().st_size;assets[p.name]=row['browser_download_url']
 back=cloud.parent/'readback';back.mkdir(exist_ok=False)
 def provider(part):
  url=assets[part['name']];assert url.startswith('https://github.com/frank8763/phase-/releases/download/'+tag+'/');p=back/part['name']
  with urllib.request.urlopen(url,timeout=60)as src,p.open('xb')as out:shutil.copyfileobj(src,out,1048576)
  return p,True
 arc.verify(record,inventory,provider);shutil.rmtree(back)
 return dict(passed=True,release_url=release['html_url'],source_members=len(inventory),all_parts_and_decompressed_members_sha_verified=True,models=0),post,upload
