"""Versioned32MiB Release delivery and actual downloaded member verification."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-'
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):
    p=Path(p);t=p.with_suffix('.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()
def gh(args,output=None,timeout=300):
    p=subprocess.run([str(GH),*args],cwd=R,stdout=output if output is not None else subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    assert p.returncode==0,'ROUND_DELIVERY_FAILED '+str(args[:3])+' '+p.stderr.decode(errors='replace')[-300:]
    return p.stdout.decode() if output is None else None
def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    raw=Path(sys.argv[1]);assert not raw.is_absolute() and raw.parts[:1]==('runs',)
    folder=(R/raw).resolve();assert folder.parent==R/'runs' and read(folder/'FINALIZED.json')['local_memberSHA_and_reassembly_verified']
    assert not (folder/'DELIVERY_CLAIM.json').exists(),'ROUND_DELIVERY_ALREADY_CLAIMED'
    sync=read(folder/'SYNC_RESULT.json');assert sync['remote_verified'],'SOURCE_REF_NOT_VERIFIED_KEEP_RAW'
    tag='phase-'+folder.name.replace('_','-')+'-20261120';dump(folder/'DELIVERY_CLAIM.json',dict(tag=tag,started_unix=time.time(),source_commit=sync['head'],models=0))
    try:
        index=read(folder/'ARCHIVE_INDEX.json')
        used=int(subprocess.run(['du','-sx','--block-size=1',str(R/'runs')],capture_output=True,text=True,check=True,timeout=60).stdout.split()[0])
        assert used+index['archive_bytes']+64*1024**2<=10*1024**3,'DOWNLOAD_SPACE_RESERVE_KEEP_RAW'
        request=folder/'RELEASE_REQUEST.json';dump(request,dict(tag_name=tag,target_commitish=sync['head'],name='Phase '+folder.name+' audited raw evidence',body='Closed Phase simulation evidence. Science pass/failure is in COMPLETION.json, independently of archive integrity. All32MiB assets and decompressed members are read back before any local raw cleanup.',draft=False,prerelease=False,make_latest='false'))
        release=json.loads(gh(['api','--method','POST',f'repos/{REPO}/releases','--input',str(request)],timeout=90));dump(folder/'RELEASE.json',dict(id=release['id'],url=release['html_url'],tag=tag))
        for row in index['parts']:
            p=folder/'archive'/row['name'];assert p.stat().st_size==row['bytes']<=32*1024**2 and sha(p)==row['sha256'];gh(['release','upload',tag,str(p),'--repo',REPO])
        gh(['release','upload',tag,str(folder/'ARCHIVE_INDEX.json'),'--repo',REPO]);download=folder/'remote_readback';download.mkdir();parts=[];digest=hashlib.sha256()
        for row in index['parts']:
            p=download/row['name']
            with p.open('xb') as out:gh(['release','download',tag,'--repo',REPO,'--pattern',row['name'],'--output','-'],output=out)
            assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
            with p.open('rb') as f:
                for b in iter(lambda:f.read(1024**2),b''):digest.update(b)
            parts.append(p)
        assert digest.hexdigest()==index['archive_sha256']
        spec=importlib.util.spec_from_file_location('weekend_transfer_reader',C/'storage_preserve.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        wanted={x['path']:x for x in index['files']};seen=set()
        with tarfile.open(fileobj=module.Reader(parts),mode='r|gz') as archive:
            for member in archive:
                assert member.name in wanted and member.name not in seen;row=wanted[member.name]
                if 'symlink' in row:assert member.issym() and member.linkname==row['symlink']
                else:
                    assert member.isfile() and member.size==row['bytes'];h=hashlib.sha256();stream=archive.extractfile(member)
                    for b in iter(lambda:stream.read(1024**2),b''):h.update(b)
                    assert h.hexdigest()==row['sha256']
                seen.add(member.name)
        assert seen==set(wanted)
        downloaded=gh(['release','download',tag,'--repo',REPO,'--pattern','ARCHIVE_INDEX.json','--output','-'])
        assert hashlib.sha256(downloaded.encode()).hexdigest()==sha(folder/'ARCHIVE_INDEX.json')
        proof=dict(passed=True,release_url=release['html_url'],tag=tag,source_commit=sync['head'],every_asset_download_SHA_verified=True,every_decompressed_member_SHA_verified=True,recovery_index_download_SHA_verified=True,source_members=len(seen),verified_unix=time.time(),raw_deleted=False,models=0)
        dump(folder/'FULL_REMOTE_VERIFIED.json',proof);gh(['release','upload',tag,str(folder/'FULL_REMOTE_VERIFIED.json'),'--repo',REPO])
        for p in parts:p.unlink()
        download.rmdir();print(json.dumps(proof))
    except BaseException as exc:
        dump(folder/'DELIVERY_ERROR.json',dict(error=repr(exc),all_unverified_originals_retained=True,models=0));raise
if __name__=='__main__':main()
