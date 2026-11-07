"""Immutable supplementary archive for the one recorded operational continuation."""
import hashlib,json,os,subprocess,tarfile,time
from pathlib import Path
from archive import R,ROOT,OUT,REC,GH,REPO,TAG,api,sha,dump,gh

def main():
    assert json.loads((ROOT/'interface01/ROUND_WINDOW.json').read_text())['round_closed'];assert json.loads((REC/'interface01/FINAL_INDEPENDENT_AUDIT.json').read_text())['passed'];target=OUT/'v857-interface-evidence.tar.zst';assert not target.exists()
    paths=[]
    for base in [ROOT/'interface01']:
        for current,dirs,files in os.walk(base,followlinks=False):
            dirs[:]=[x for x in dirs if not(Path(current)/x).is_symlink()]
            paths.extend(Path(current)/x for x in files if(Path(current)/x).is_file()and not(Path(current)/x).is_symlink())
    paths.extend(ROOT/x for x in ['SOURCE_SYNC_RESULT.json','source_push.console','archive.console','publish.console','SEMANTIC_AUDIT.console']if(ROOT/x).exists())
    inventory=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(paths)];expected={x['path']:x for x in inventory}
    with target.open('wb')as f:
        z=subprocess.Popen(['zstd','-q','-3','-T1','-c'],stdin=subprocess.PIPE,stdout=f)
        with tarfile.open(fileobj=z.stdin,mode='w|')as tar:
            for row in inventory:tar.add(R/row['path'],arcname=row['path'],recursive=False)
        z.stdin.close();assert z.wait(timeout=60)==0
    z=subprocess.Popen(['zstd','-q','-dc',str(target)],stdout=subprocess.PIPE);seen=set()
    with tarfile.open(fileobj=z.stdout,mode='r|')as tar:
        for m in tar:
            assert m.name in expected and m.name not in seen and m.isfile();seen.add(m.name);h=hashlib.sha256();f=tar.extractfile(m)
            for b in iter(lambda:f.read(1048576),b''):h.update(b)
            assert m.size==expected[m.name]['bytes']and h.hexdigest()==expected[m.name]['sha256']
    assert z.wait(timeout=20)==0 and seen==set(expected)
    index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',archive_name=target.name,archive_bytes=target.stat().st_size,archive_sha256=sha(target),source_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),files=inventory,source_and_decompressed_sha_verified=True,scientific_outcome='FULL_ORIGINAL_REPLAY_EXACT_CORRECTED_MODEL_ACTUATOR_INTERFACE_REJECTED_BEFORE_INTEGRATION',original_deadline_not_reset=True,original_first_failure_preserved=True);dump(REC/'INTERFACE_RECORD_INDEX.json',index);dump(OUT/'INTERFACE_RECORD_INDEX.json',index)
    release=api(f'repos/{REPO}/releases/437466242');assert not release['draft'];done=[]
    for p in [target,OUT/'INTERFACE_RECORD_INDEX.json']:
        assets=api(f'repos/{REPO}/releases/437466242/assets?per_page=100');matches=[x for x in assets if x['name']==p.name]
        if not matches:gh(['release','upload',TAG,str(p),'--repo',REPO],capture_output=True,text=True,timeout=180);matches=[x for x in api(f'repos/{REPO}/releases/437466242/assets?per_page=100')if x['name']==p.name]
        a=matches[0];digest=sha(p);assert a['size']==p.stat().st_size and a['digest']=='sha256:'+digest;h=hashlib.sha256();size=0
        with(OUT/(p.name+'.download.console')).open('w')as err:
            proc=subprocess.Popen([str(GH),'release','download',TAG,'--repo',REPO,'--pattern',p.name,'--output','-'],cwd=R,stdout=subprocess.PIPE,stderr=err)
            for b in iter(lambda:proc.stdout.read(1048576),b''):h.update(b);size+=len(b)
            assert proc.wait(timeout=10)==0
        assert size==p.stat().st_size and h.hexdigest()==digest;done.append(dict(name=p.name,bytes=size,sha256=digest,server_digest=a['digest'],streamed_download_sha_verified=True));print(json.dumps(done[-1]),flush=True)
    proof=json.loads((REC/'REMOTE_VERIFIED.json').read_text());proof.update(status='PUBLIC_ORIGINAL_AND_ONE_OPERATION_SUPPLEMENT_ALL_SHA_VERIFIED',supplement_assets=done,release_id=437466242,public=True,verified_unix=time.time());dump(REC/'REMOTE_VERIFIED.json',proof);dump(OUT/'FULL_REMOTE_VERIFIED.json',proof)
if __name__=='__main__':main()
