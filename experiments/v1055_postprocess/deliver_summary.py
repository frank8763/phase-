"""One small post-run supplement; no second push or raw release re-upload."""
import hashlib,importlib.util,json,subprocess,urllib.parse,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1055_atomic_publication_execution';D=R/'records/nav2_v1055_20261111';TAG='phase-atomic-execution-v1055-20261111'
def main():
 claim=O/'FINAL_SUPPLEMENT_CLAIM.json'
 with claim.open('x')as f:json.dump(dict(models=0,new_push=False,new_raw_upload=False),f)
 spec=importlib.util.spec_from_file_location('v1055_postprocess_archive',R/'experiments/v1055_atomic_publication_execution/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
 files={R/'docs/RPCCR_ATOMIC_EXECUTION_V1055_REPORT.md',D/'HUMAN_SUMMARY.json',D/'OFFLINE_ACTOR_DOMAIN_COVERAGE.json',O/'MAIN_DISCOVERY_CHAIN_AUDIT.json',O/'FIGURE_PROVENANCE.json',O/'ACTUAL_MAIN_PATH_AND_CLEARANCE.png',*C.glob('*.py')};record,inventory=arc.package(R,files,O/'final_supplement','v1055-final-report-and-coverage');(D/'FINAL_SUPPLEMENT_INDEX.json').write_text(json.dumps(dict(record=record,models=0),indent=2)+'\n')
 try:
  with urllib.request.urlopen('https://api.github.com/repos/frank8763/phase-/releases/tags/'+TAG,timeout=10)as response:release=json.load(response)
  upload=release['upload_url'].split('{')[0];assert upload.startswith('https://uploads.github.com/repos/frank8763/phase-/releases/');gh=R/'tools/phase_storage_20261107/vendor/gh';token=subprocess.run([str(gh),'auth','token','--hostname','github.com'],capture_output=True,text=True,check=True,timeout=5).stdout.strip()
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*args):raise RuntimeError('Authenticated redirect refused')
  api=urllib.request.build_opener(NoRedirect());assets={}
  for p in [*sorted((O/'final_supplement').iterdir()),D/'FINAL_SUPPLEMENT_INDEX.json']:
   req=urllib.request.Request(upload+'?name='+urllib.parse.quote(p.name),data=p.read_bytes(),method='POST',headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream','User-Agent':'Phase-final-zero-model-report'})
   with api.open(req,timeout=30)as response:row=json.load(response)
   assert row['size']==p.stat().st_size;assets[p.name]=row['browser_download_url']
  back=O/'supplement_readback';back.mkdir()
  def provider(part):
   p=back/part['name'];url=assets[part['name']];assert url.startswith('https://github.com/frank8763/phase-/releases/download/'+TAG+'/')
   with urllib.request.urlopen(url,timeout=30)as response,p.open('xb')as out:
    for data in iter(lambda:response.read(1048576),b''):out.write(data)
   return p,True
  arc.verify(record,inventory,provider);(D/'FINAL_SUPPLEMENT_REMOTE_VERIFIED.json').write_text(json.dumps(dict(passed=True,all_parts_and_decompressed_members_sha_verified=True,source_members=len(inventory),release_url=release['html_url'],models=0,new_push=False),indent=2)+'\n');print('final_report_and_coverage_remote_sha_verified',True)
 except BaseException as e:(D/'FINAL_SUPPLEMENT_REMOTE_PENDING.json').write_text(json.dumps(dict(error=repr(e),no_retry=True,raw_evidence_prior_verification_unchanged=True),indent=2)+'\n');print('small_supplement_kept_local',True)
if __name__=='__main__':main()
