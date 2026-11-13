"""One closed-component Release delivery, full remote SHA readback, no cleanup."""
import sys,json,time,signal,subprocess,urllib.request,urllib.parse,importlib.util,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1091_certified_exit';D=R/'records/nav2_v1091_20261113'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
def dump(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def main():
    D.mkdir(exist_ok=True);assert not(D/'DELIVERY_CLAIM.json').exists()
    assert json.loads((O/'FINALIZED.json').read_text())['passed']
    dump(D/'DELIVERY_CLAIM.json',dict(started_unix=time.time(),release_only=True,push_attempts=0,models=0,integrations=0))
    def halt(*_):raise TimeoutError('BOUNDED300S_REMOTE_DELIVERY')
    signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,300)
    try:
        source=json.loads((O/'ARCHIVE_INDEX.json').read_text());record=source['archive'];inventory=source['inventory']
        spec=importlib.util.spec_from_file_location('closed_exit_remote_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
        token=subprocess.check_output([str(R/'tools/phase_storage_20261107/vendor/gh'),'auth','token','--hostname','github.com'],text=True,timeout=5).strip();assert token
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args):raise RuntimeError('AUTHENTICATED_REDIRECT_REFUSED')
        client=urllib.request.build_opener(NoRedirect())
        def post(url,data,kind='application/json'):
            assert url.startswith(('https://api.github.com/repos/frank8763/phase-/releases','https://uploads.github.com/repos/frank8763/phase-/releases/'))
            req=urllib.request.Request(url,data=data,method='POST',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':kind,'User-Agent':'Phase-closed-evidence','X-GitHub-Api-Version':'2022-11-28'})
            with client.open(req,timeout=45)as response:return json.load(response)
        tag='phase-certified-exit-v1091-20261113'
        dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag=tag,archives=[record]))
        dump(D/'INVENTORY.json',dict(files=inventory))
        release=post('https://api.github.com/repos/frank8763/phase-/releases',json.dumps(dict(tag_name=tag,target_commitish='main',name='V1091 actual certified stop component',body='Passed saved failure exit component, not full navigation. Exact 24535 historical natives, 2200 actual stop, full26735 own replay and14 independent gates. Original V1090 failure preserved. Full sources and all scene evidence with SHA inventories; source branch sync follows final bounded daytime closure.',make_latest='false')).encode())
        upload=release['upload_url'].split('{')[0];urls={}
        for p in [O/'cloud'/record['parts'][0]['name'],D/'RECORD_INDEX.json',D/'INVENTORY.json',O/'FINALIZED.json',O/'COMPLETION.json']:
            item=post(upload+'?name='+urllib.parse.quote(p.name),p.read_bytes(),'application/octet-stream');assert item['size']==p.stat().st_size;urls[p.name]=item['browser_download_url']
        # General streaming verifier also checks the concatenated archive and
        # every decompressed source; no deletion of original records here.
        folder=O/'remote_readback';folder.mkdir(exist_ok=False)
        def provider(part):
            path=folder/part['name']
            with urllib.request.urlopen(urls[part['name']],timeout=45)as src,path.open('xb')as dst:shutil.copyfileobj(src,dst,1024**2)
            return path,True
        arc.verify(record,inventory,provider);folder.rmdir()
        result=dict(passed=True,release_url=release['html_url'],source_members=len(inventory),all_parts_and_decompressed_members_sha_verified=True,push_attempts=0,models=0,integrations=0,raw_not_deleted=True)
        dump(D/'REMOTE_VERIFIED.json',result);print(json.dumps(result),flush=True)
    except BaseException as error:
        dump(D/'DELIVERY_RESULT.json',dict(passed=False,error=repr(error),raw_retained=True,no_retry=True,models=0,integrations=0));print(json.dumps(dict(passed=False,error=repr(error),raw_retained=True)),flush=True)
    finally:signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
