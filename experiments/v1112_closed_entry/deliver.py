"""One closed-component Release delivery, full remote SHA readback, no cleanup."""
import sys,json,time,signal,subprocess,urllib.request,urllib.parse,importlib.util,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1112_parked_mode_response';D=R/'records/nav2_v1112_20261113'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def main():
    D.mkdir(exist_ok=True);assert not(D/'DELIVERY_CLAIM.json').exists()
    assert json.loads((D/'FINALIZED_REVIEW.json').read_text())['evidence_integrity_passed']
    dump(D/'DELIVERY_CLAIM.json',dict(started_unix=time.time(),release_only=True,push_attempts=0,models=0,integrations=0))
    def halt(*_):raise TimeoutError('BOUNDED300S_REMOTE_DELIVERY')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,300)
    try:
        index=json.loads((D/'RECORD_INDEX.json').read_text());records=index['archives'];inventories=[json.loads((D/name).read_text())['files']for name in index['archive_inventories']]
        spec=importlib.util.spec_from_file_location('closed_exit_remote_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
        token=subprocess.check_output([str(R/'tools/phase_storage_20261107/vendor/gh'),'auth','token','--hostname','github.com'],text=True,timeout=5).strip();assert token
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args):raise RuntimeError('AUTHENTICATED_REDIRECT_REFUSED')
        client=urllib.request.build_opener(NoRedirect())
        def post(url,data,kind='application/json'):
            assert url.startswith(('https://api.github.com/repos/frank8763/phase-/releases','https://uploads.github.com/repos/frank8763/phase-/releases/'))
            req=urllib.request.Request(url,data=data,method='POST',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':kind,'User-Agent':'Phase-closed-evidence','X-GitHub-Api-Version':'2022-11-28'})
            with client.open(req,timeout=45)as response:return json.load(response)
        tag='phase-parked-mode-v1112-20261113'
        release=post('https://api.github.com/repos/frank8763/phase-/releases',json.dumps(dict(tag_name=tag,target_commitish='main',name='V1112 static component entry failure at zero integration',body='NOT_PASSED: one canonical vehicle initialization, zero actual integration and zero replay integration. Static actor-absent component incorrectly compared against dynamic actor-present NS fixture SHA. Both parked responses remain unassessed. Original frozen failure and zero-trace audit failure preserved; all other saved setup fields and t0 body match. Includes full actual static scene, frozen source, software qualification and independent zero-step accounting. No restart or navigation.',make_latest='false')).encode())
        upload=release['upload_url'].split('{')[0];urls={}
        for p in [*[O/folder/part['name']for record,folder in zip(records,['cloud','review_cloud'])for part in record['parts']],D/'RECORD_INDEX.json',D/'INVENTORY.json',D/'REVIEW_INVENTORY.json',D/'FINALIZED_REVIEW.json',O/'COMPLETION.json']:
            item=post(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes(),'application/octet-stream');assert item['size']==p.stat().st_size;urls[p.name]=item['browser_download_url']
        # General streaming verifier also checks the concatenated archive and
        # every decompressed source; no deletion of original records here.
        folder=O/'remote_readback';folder.mkdir(exist_ok=False)
        def provider(part):
            path=folder/part['name']
            with urllib.request.urlopen(urls[part['name']],timeout=45)as src,path.open('xb')as dst:shutil.copyfileobj(src,dst,1024**2)
            return path,True
        for record,inventory in zip(records,inventories):arc.verify(record,inventory,provider)
        folder.rmdir()
        result=dict(passed=True,release_url=release['html_url'],source_members=sum(map(len,inventories)),all_parts_and_decompressed_members_sha_verified=True,push_attempts=0,models=0,integrations=0,raw_not_deleted=True)
        dump(D/'REMOTE_VERIFIED.json',result);print(json.dumps(result),flush=True)
    except BaseException as error:
        dump(D/'DELIVERY_RESULT.json',dict(passed=False,error=repr(error),raw_retained=True,no_retry=True,models=0,integrations=0));print(json.dumps(dict(passed=False,error=repr(error),raw_retained=True)),flush=True)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
