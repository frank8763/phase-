"""Publish an already source/decompression-verified archive; never repack or overwrite."""
import hashlib,json,subprocess,time
from pathlib import Path
from archive import R,ROOT,OUT,REC,GH,REPO,TAG,api,sha,dump,gh

def main():
    index=json.loads((REC/'RECORD_INDEX.json').read_text());assert index['source_and_decompressed_sha_verified'];archive=OUT/index['archive_name'];assert sha(archive)==index['archive_sha256'];found=[x for x in api(f'repos/{REPO}/releases?per_page=30')if x['tag_name']==TAG];assert len(found)==1;release=found[0];done=[]
    for p in [archive,OUT/'RECORD_INDEX.json']:
        assets=api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100');matches=[x for x in assets if x['name']==p.name]
        if not matches:
            gh(['release','upload',TAG,str(p),'--repo',REPO],capture_output=True,text=True,timeout=180);matches=[x for x in api(f'repos/{REPO}/releases/{release["id"]}/assets?per_page=100')if x['name']==p.name]
        assert len(matches)==1;a=matches[0];digest=sha(p);assert a['size']==p.stat().st_size and a['digest']=='sha256:'+digest;h=hashlib.sha256();size=0
        with(OUT/(p.name+'.download.console')).open('w')as err:
            proc=subprocess.Popen([str(GH),'release','download',TAG,'--repo',REPO,'--pattern',p.name,'--output','-'],cwd=R,stdout=subprocess.PIPE,stderr=err)
            for b in iter(lambda:proc.stdout.read(1048576),b''):h.update(b);size+=len(b)
            assert proc.wait(timeout=10)==0
        assert h.hexdigest()==digest and size==p.stat().st_size;done.append(dict(name=p.name,bytes=size,sha256=digest,server_digest=a['digest'],streamed_download_sha_verified=True));print(json.dumps(done[-1]),flush=True)
    proof=dict(passed=True,release_id=release['id'],release_url=index['release_url'],assets=done,all_server_and_download_sha_verified=True,status='VERIFIED_DRAFT_AWAITING_SOURCE_PUBLICATION',verified_unix=time.time(),pre_upload_metadata_error='Draft release has no public tag yet; get-by-tag returned404. Existing draft reused by list/id, original log preserved, no duplicate archive or release.');dump(REC/'REMOTE_VERIFIED.json',proof);dump(OUT/'REMOTE_VERIFIED.json',proof)
if __name__=='__main__':main()
