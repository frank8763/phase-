"""Preserve closed historical Phase caches remotely before exact-manifest cleanup.

No models or processes outside Phase are inspected. No source/current/runtime or
tracked/protected dependency is deleted. Release uploads and actual downloads
precede per-member SHA and unlink; missing remote proof never permits deletion.
"""
import fcntl
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
W=O/'storage';GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-';TAG='phase-preserved-history-weekend-20261120'
ROOT_END=1795395600;LIMIT=10*1024**3;TARGET=8*1024**3
def dump(p,v):
    p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()
def gh(args,timeout=120,output=None):
    assert time.time()<ROOT_END,'WEEKEND_STORAGE_DEADLINE'
    p=subprocess.run([str(GH),*args],cwd=R,stdout=output if output is not None else subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    assert p.returncode==0,'GITHUB_TRANSFER_FAILED '+str(args[:3])+' '+p.stderr.decode(errors='replace')[-300:]
    return p.stdout.decode() if output is None else None
def usage():
    p=subprocess.run(['du','-sx','--block-size=1',str(R/'runs')],capture_output=True,text=True,check=True,timeout=90)
    return int(p.stdout.split()[0])
class Parts:
    def __init__(self,folder,prefix):self.folder=folder;self.prefix=prefix;self.parts=[];self.file=None;self.size=0;self.digest=hashlib.sha256();self.total=0
    def write(self,data):
        view=memoryview(data)
        while view:
            if self.file is None:
                self.path=self.folder/(self.prefix+'.tar.gz.part%03d'%len(self.parts));self.file=self.path.open('xb');self.size=0;self.part_hash=hashlib.sha256()
            n=min(len(view),32*1024**2-self.size);piece=view[:n];self.file.write(piece);self.part_hash.update(piece);self.digest.update(piece);self.total+=n;self.size+=n;view=view[n:]
            if self.size==32*1024**2:self.finish()
        return len(data)
    def flush(self):
        if self.file:self.file.flush()
    def finish(self):
        if self.file:self.file.close();self.parts.append(dict(name=self.path.name,bytes=self.size,sha256=self.part_hash.hexdigest()));self.file=None
class Reader(io.RawIOBase):
    def __init__(self,paths):self.paths=iter(paths);self.current=None
    def readable(self):return True
    def read(self,n=-1):
        if n<0:n=1024**2
        out=bytearray()
        while len(out)<n:
            if self.current is None:
                try:self.current=next(self.paths).open('rb')
                except StopIteration:break
            b=self.current.read(n-len(out))
            if b:out.extend(b)
            else:self.current.close();self.current=None
        return bytes(out)
def build_plan():
    assert (R/'REVIEW_PENDING').exists() and read(R/'CURRENT_EXPERIMENT.json')['active_run'] is None
    frozen=read(R/'experiments/v1380_timed_handoff_component/SOURCE_FREEZE.json')['files'];protected=set(frozen)
    tracked=subprocess.run(['git','ls-files','-z'],cwd=R,capture_output=True,check=True).stdout.decode().split('\0');protected.update(p for p in tracked if p)
    inodes=set()
    for name in protected:
        p=R/name
        if p.is_file() and not p.is_symlink():s=p.stat();inodes.add((s.st_dev,s.st_ino))
    groups=[];base=R/'runs/v858_nav2_verified'
    for root in base.iterdir():
        if root.is_symlink() or not root.is_dir() or not re.fullmatch(r'v\d+',root.name):continue
        version=int(root.name[1:])
        if not 1000<=version<1280:continue
        files=[];allocated=0
        for p in root.rglob('*'):
            if p.is_symlink() or not p.is_file():continue
            name=str(p.relative_to(R));s=p.stat()
            if name in protected or (s.st_dev,s.st_ino) in inodes:continue
            files.append(dict(path=name,bytes=s.st_size,sha256=sha(p),device=s.st_dev,inode=s.st_ino,mtime_ns=s.st_mtime_ns))
            allocated+=s.st_blocks*512
        if files:groups.append(dict(id=root.name,files=files,allocated_bytes=allocated))
    groups.sort(key=lambda g:g['allocated_bytes'],reverse=True)
    before=usage();selected=[];amount=0
    for group in groups:
        selected.append(group);amount+=group['allocated_bytes']
        if amount>=before-TARGET+512*1024**2:break
    assert amount>=before-LIMIT,'NOT_ENOUGH_UNPROTECTED_CLOSED_CACHES'
    return dict(root=str(R),before_allocated_bytes=before,target_allocated_bytes=TARGET,limit_bytes=LIMIT,groups=selected,protected_source_paths_count=len(protected),protected_freeze_sha256=sha(R/'experiments/v1380_timed_handoff_component/SOURCE_FREEZE.json'),source_head=subprocess.run(['git','rev-parse','HEAD'],cwd=R,capture_output=True,text=True,check=True).stdout.strip(),models=0,physical_native=0)
def create_release():
    repo=json.loads(gh(['api',f'repos/{REPO}']));assert repo['full_name']==REPO
    p=subprocess.run([str(GH),'release','view',TAG,'--repo',REPO,'--json','id,url'],cwd=R,capture_output=True,text=True,timeout=60)
    if p.returncode==0:return json.loads(p.stdout)
    head=subprocess.run(['git','ls-remote','origin','refs/heads/main'],cwd=R,capture_output=True,text=True,check=True,timeout=15).stdout.split()[0]
    request=W/'CREATE_RELEASE.json';dump(request,dict(tag_name=TAG,target_commitish=head,name='Phase historical raw evidence preservation 2026-11-20',body='Immutable SHA-indexed closed Phase simulation caches. Upload and actual downloaded/decompressed member verification precede manifest cleanup. Source/current/runtime, active inputs and tracked files are retained. This release makes no new navigation or paper acceptance claim.',draft=False,prerelease=False,make_latest='false'))
    result=json.loads(gh(['api','--method','POST',f'repos/{REPO}/releases','--input',str(request)]));return dict(id=result['id'],url=result['html_url'])
def upload(path,release_id):
    assets=json.loads(gh(['api',f'repos/{REPO}/releases/{release_id}/assets?per_page=100']))
    same=[a for a in assets if a['name']==path.name]
    if same:
        assert len(same)==1 and same[0]['size']==path.stat().st_size and same[0].get('digest')=='sha256:'+sha(path),'REMOTE_ASSET_CONFLICT'
        return
    gh(['release','upload',TAG,str(path),'--repo',REPO],timeout=300)
def preserve(group,release):
    folder=W/group['id'];folder.mkdir(exist_ok=False);dump(folder/'SOURCE_INVENTORY.json',group)
    writer=Parts(folder,group['id'])
    with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=1,mtime=0) as compressor,tarfile.open(fileobj=compressor,mode='w|') as archive:
        for row in group['files']:
            p=R/row['path'];assert not p.is_symlink() and p.is_file() and p.stat().st_size==row['bytes']
            info=tarfile.TarInfo(row['path']);info.size=row['bytes'];info.mode=0o600
            with p.open('rb') as source:archive.addfile(info,source)
    writer.finish();index=dict(id=group['id'],parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),files=group['files'],release_url=release['url'],models=0)
    index_path=folder/(group['id']+'.INDEX.json');dump(index_path,index)
    for row in writer.parts:upload(folder/row['name'],release['id'])
    upload(index_path,release['id']);download=folder/'download';download.mkdir();whole=hashlib.sha256();parts=[]
    for row in writer.parts:
        p=download/row['name']
        with p.open('xb') as out:gh(['release','download',TAG,'--repo',REPO,'--pattern',row['name'],'--output','-'],timeout=300,output=out)
        assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'DOWNLOADED_PART_MISMATCH'
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1024**2),b''):whole.update(b)
        parts.append(p)
    assert whole.hexdigest()==index['archive_sha256']
    wanted={row['path']:row for row in group['files']};seen=set()
    with tarfile.open(fileobj=Reader(parts),mode='r|gz') as archive:
        for member in archive:
            assert member.isfile() and member.name in wanted and member.name not in seen
            row=wanted[member.name];assert member.size==row['bytes'];h=hashlib.sha256();stream=archive.extractfile(member)
            for b in iter(lambda:stream.read(1024**2),b''):h.update(b)
            assert h.hexdigest()==row['sha256'],'DECOMPRESSED_MEMBER_SHA_MISMATCH';seen.add(member.name)
    assert seen==set(wanted)
    # Download the index as well: recovery metadata must be remotely usable.
    downloaded=gh(['release','download',TAG,'--repo',REPO,'--pattern',index_path.name,'--output','-'],timeout=120)
    assert hashlib.sha256(downloaded.encode()).hexdigest()==sha(index_path),'DOWNLOADED_INDEX_SHA'
    proof=dict(passed=True,every_asset_actual_download_SHA_verified=True,every_decompressed_member_SHA_verified=True,recovery_index_download_SHA_verified=True,release_url=release['url'],group=group['id'],source_files=len(seen),source_bytes=sum(x['bytes'] for x in group['files']),archive_bytes=writer.total,verified_unix=time.time(),models=0)
    dump(folder/'FULL_REMOTE_VERIFIED.json',proof)
    named_proof=folder/(group['id']+'.REMOTE_VERIFIED.json');dump(named_proof,proof);upload(named_proof,release['id'])
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert (R/'REVIEW_PENDING').exists() and read(R/'CURRENT_EXPERIMENT.json')['active_run'] is None
        frozen=read(O/'STORAGE_SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in frozen.items()),'STORAGE_PROGRAM_CHANGED'
        for row in group['files']:
            p=R/row['path'];assert not p.is_symlink() and p.resolve().is_relative_to(R/'runs/v858_nav2_verified');s=p.stat()
            assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(row['device'],row['inode'],row['bytes'],row['mtime_ns']) and sha(p)==row['sha256'],'LOCAL_RAW_CHANGED_BEFORE_DELETE'
        for row in group['files']:(R/row['path']).unlink()
    # Only duplicate verified local transports/downloads are removed, not proof.
    for p in parts:p.unlink()
    download.rmdir()
    for row in writer.parts:(folder/row['name']).unlink()
    dump(folder/'CLEANUP_RESULT.json',dict(passed=True,files=len(group['files']),raw_logical_bytes=proof['source_bytes'],raw_only_deleted_after_full_remote_readback=True,remaining_runs_allocated_bytes=usage(),models=0))
    return proof
def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));W.mkdir(exist_ok=False)
    frozen=read(O/'STORAGE_SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in frozen.items()),'STORAGE_SOURCE_CHANGED'
    dump(W/'CLAIM.json',dict(started_unix=time.time(),pid=os.getpid(),scope='new verified preservation of historical Phase caches; no models'))
    try:
        plan=build_plan();dump(W/'PLAN.json',plan);release=create_release();dump(W/'RELEASE.json',release);verified=[]
        for group in plan['groups']:
            if usage()<=TARGET:break
            result=preserve(group,release);verified.append(result);dump(W/'PROGRESS.json',dict(completed_groups=len(verified),last_group=group['id'],remaining_runs_allocated_bytes=usage(),release_url=release['url'],models=0))
            print(json.dumps(dict(group=group['id'],remote_members_verified=result['source_files'],remaining_bytes=usage())),flush=True)
        final_bytes=usage();assert final_bytes<LIMIT-512*1024**2,'STORAGE_RESERVE_STILL_INSUFFICIENT'
        dump(W/'FINALIZED.json',dict(passed=True,remaining_runs_allocated_bytes=final_bytes,limit_bytes=LIMIT,verified_groups=verified,source_protected=True,models=0))
        ledger=read(O/'LEDGER.json');ledger.update(status='STORAGE_READY_FOR_FIRST_ROUND',models_now_authorized=False,storage_ready=True,storage_allocated_bytes=final_bytes,storage_proof=str((W/'FINALIZED.json').relative_to(R)));dump(O/'LEDGER.json',ledger)
    except BaseException as exc:
        import traceback
        dump(W/'ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),unverified_originals_retained=True,models=0));raise
if __name__=='__main__':main()
