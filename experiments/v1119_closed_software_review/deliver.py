"""Archive only closed software series; one Release upload plus full SHA readback."""
import sys,json,time,signal,subprocess,urllib.request,urllib.parse,importlib.util,shutil,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'records/nav2_coupled_source_20261113';OUT=R/'runs/v1120_explicit_timing_seed';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(Path(__file__).resolve().parent));from review import NAMES

def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def used():
 seen=set();total=0
 for base,dirs,names in os.walk(R/'runs',followlinks=False):
  dirs[:]=[n for n in dirs if not Path(base,n).is_symlink()]
  for n in names:
   p=Path(base,n)
   if p.is_symlink():continue
   s=p.stat();key=s.st_dev,s.st_ino
   if key not in seen:seen.add(key);total+=s.st_size
 return total

def main():
 assert json.loads((D/'FINALIZED_REVIEW.json').read_text())['evidence_integrity_passed'];assert not(D/'DELIVERY_CLAIM.json').exists();dump(D/'DELIVERY_CLAIM.json',dict(started_unix=time.time(),release_only=True,no_retry=True,models=0,integrations=0))
 def halt(*_):raise TimeoutError('BOUNDED360S_ARCHIVE_DELIVERY')
 signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,360)
 try:
  spec=importlib.util.spec_from_file_location('closed_software_stream_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
  files=[]
  for name in NAMES:
   assert json.loads((R/'runs'/name/'COMPLETION.json').read_text())['closed']
   for base in [R/'experiments'/name,R/'runs'/name]:files.extend(p for p in arc.walk(base)if p.suffix not in ['.so'])
  files.extend(arc.walk(Path(__file__).resolve().parent));files.extend([D/'FINALIZED_REVIEW.json',R/'RPCCR_COUPLED_ROUTE_AUTHORIZATION_20261113.json',R/'CURRENT_EXPERIMENT.json',R/'docs/RPCCR_COUPLED_ROUTE_PREPARATION_20261113_REPORT.md'])
  record,catalog=arc.package(R,files,OUT/'cloud','coupled_complete_sources_v1115_v1120',lambda:used()+128*1024**2<2*1024**3);dump(D/'INVENTORY.json',dict(files=catalog));dump(D/'ARCHIVE.json',record)
  token=subprocess.check_output([str(R/'tools/phase_storage_20261107/vendor/gh'),'auth','token','--hostname','github.com'],text=True,timeout=5).strip();assert token
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*args):raise RuntimeError('AUTH_REDIRECT_REFUSED')
  client=urllib.request.build_opener(NoRedirect())
  def post(url,data,kind='application/json'):
   assert url.startswith(('https://api.github.com/repos/frank8763/phase-/releases','https://uploads.github.com/repos/frank8763/phase-/releases/'))
   request=urllib.request.Request(url,data=data,method='POST',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':kind,'User-Agent':'Phase-closed-software-evidence','X-GitHub-Api-Version':'2022-11-28'})
   with client.open(request,timeout=45)as response:return json.load(response)
  outcome=json.loads((OUT/'COMPLETION.json').read_text())['passed'];release=post('https://api.github.com/repos/frank8763/phase-/releases',json.dumps(dict(tag_name='phase-coupled-source-v1120-20261113',target_commitish='main',name='Coupled complete-source preparation V1115–V1120',body='Closed analytical preparation only,0 physical models/integrations. Old NS success and V1114 component pass preserved. V1115–V1117 source refusals and V1119 seed-selection defect retained. V1118 mode-state seam24 full suffixes passed. V1120 complete-source admitted='+str(outcome)+'. Same-version three routes/24 not executed; independently authorized12-hour physical root has not started. Full archive/member SHA readback required before local cleanup.',make_latest='false')).encode());upload=release['upload_url'].split('{')[0];urls={}
  for p in [*[OUT/'cloud'/x['name']for x in record['parts']],D/'ARCHIVE.json',D/'INVENTORY.json',D/'FINALIZED_REVIEW.json']:
   item=post(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes(),'application/octet-stream');assert item['size']==p.stat().st_size;urls[p.name]=item['browser_download_url']
  folder=OUT/'remote_readback';folder.mkdir(exist_ok=False)
  def provider(part):
   p=folder/part['name']
   with urllib.request.urlopen(urls[part['name']],timeout=45)as source,p.open('xb')as target:shutil.copyfileobj(source,target,1024**2)
   return p,True
  arc.verify(record,catalog,provider);folder.rmdir();result=dict(passed=True,release_url=release['html_url'],source_members=len(catalog),all_parts_and_decompressed_members_sha_verified=True,models=0,integrations=0,raw_sources_retained_for_pending_live_integration=True);dump(D/'REMOTE_VERIFIED.json',result);print(json.dumps(result),flush=True)
 except BaseException as e:dump(D/'DELIVERY_RESULT.json',dict(passed=False,error=repr(e),no_retry=True,raw_retained=True,models=0,integrations=0));print(json.dumps(dict(passed=False,error=repr(e))),flush=True)
 finally:signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
