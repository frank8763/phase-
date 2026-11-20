"""Download one32MiB asset at a time while verifying the entire tar stream."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
R=Path(__file__).resolve().parents[2];O=R/'runs/v1393_full9390_preparation';TAG='phase-v1393-full9390-analysis-20261120'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
h=load('analysis_remote_bounded_transport',R/'experiments/v1389_idempotent_storage_transfer/resume.py');h.O=O/'remote_delivery';h.W=h.O;h.base.TAG=TAG

class RemoteReader(io.RawIOBase):
    def __init__(self,parts,assets,folder,download):
        self.parts=iter(parts);self.assets=assets;self.folder=folder;self.download=download;self.stream=None;self.path=None;self.digest=hashlib.sha256();self.verified=[]
    def readable(self):return True
    def read(self,n=-1):
        if n<0:n=1024**2
        out=bytearray()
        while len(out)<n:
            if self.stream is None:
                try:row=next(self.parts)
                except StopIteration:break
                assert Path(row['name']).name==row['name'];self.path=self.folder/row['name'];asset=self.assets[row['name']]
                assert asset['size']==row['bytes'] and asset['digest']=='sha256:'+row['sha256']
                self.download(self.path,asset);assert h.sha(self.path)==row['sha256'];self.verified.append(row['name']);self.stream=self.path.open('rb')
            block=self.stream.read(n-len(out))
            if block:out.extend(block);self.digest.update(block)
            else:self.stream.close();self.stream=None;self.path.unlink();self.path=None
        return bytes(out)

def qualify():
    import gzip,tempfile
    with tempfile.TemporaryDirectory(dir=O) as root:
        folder=Path(root);payload=gzip.compress(b'qualified streamed source recovery'*1000);pieces=[payload[:31],payload[31:]];rows=[];assets={};memory={}
        for i,b in enumerate(pieces):
            name='fixture.part%03d'%i;digest=hashlib.sha256(b).hexdigest();rows.append(dict(name=name,bytes=len(b),sha256=digest));assets[name]=dict(name=name,size=len(b),digest='sha256:'+digest);memory[name]=b
        def download(path,asset):path.write_bytes(memory[path.name])
        reader=RemoteReader(rows,assets,folder,download);result=gzip.GzipFile(fileobj=reader).read();assert result==b'qualified streamed source recovery'*1000
        assert reader.digest.hexdigest()==hashlib.sha256(payload).hexdigest() and len(reader.verified)==2 and not list(folder.glob('*.part*'))
    proof=dict(passed=True,streamed32MiB_memory_bound_fixture=True,part_SHA_whole_SHA_decompressed_roundtrip=True,duplicate_download_chunks_removed_only=True,models=0)
    h.dump(O/'REMOTE_STREAM_QUALIFICATION.json',proof);print(json.dumps(proof))

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert h.read(O/'REMOTE_STREAM_QUALIFICATION.json')['passed'] and h.read(O/'FINALIZED.json')['passed']
    sync=h.read(O/'ANALYSIS_SYNC_RESULT.json');assert sync['remote_verified'] and not h.O.exists()
    used=h.base.usage();assert used+64*1024**2<10*1024**3,'STREAM_READBACK_RESERVE'
    h.O.mkdir();h.dump(h.O/'CLAIM.json',dict(started_unix=time.time(),source_head=sync['head'],models=0,maximum_download_asset_bytes=32*1024**2))
    try:
        request=h.O/'CREATE_RELEASE.json';h.dump(request,dict(tag_name=TAG,target_commitish=sync['head'],name='Phase originalRPP full9390 analytical response witness',body='Analytical preparation only,0 physical steps. Original plugin/model, all-source archive and complete braking branches; no actual moving qualification.32MiB asset recovery verified by streamed download, each member SHA and whole archive SHA before duplicate transport cleanup.',draft=False,prerelease=False,make_latest='false'))
        release=json.loads(h.base.gh(['api','--method','POST','repos/frank8763/phase-/releases','--input',str(request)],timeout=90));h.dump(h.O/'RELEASE.json',dict(id=release['id'],url=release['html_url']))
        index=h.read(O/'ARCHIVE_INDEX.json');known=h.assets(h.read(h.O/'RELEASE.json'))
        for row in index['parts']:
            assert row['bytes']<=32*1024**2;path=O/'closed_archive'/row['name'];assert h.sha(path)==row['sha256'];h.ensure_uploaded(path,known)
        h.ensure_uploaded(O/'ARCHIVE_INDEX.json',h.assets(h.read(h.O/'RELEASE.json')));known=h.assets(h.read(h.O/'RELEASE.json'))
        directory=h.O/'readback';directory.mkdir();reader=RemoteReader(index['parts'],known,directory,h.download);wanted={x['path']:x for x in index['files']};seen=set()
        with tarfile.open(fileobj=reader,mode='r|gz') as archive:
            for member in archive:
                assert member.name in wanted and member.name not in seen;row=wanted[member.name]
                if 'symlink' in row:assert member.issym() and member.linkname==row['symlink']
                else:
                    assert member.isfile() and member.size==row['bytes'];stream=archive.extractfile(member);digest=hashlib.sha256()
                    for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
                    assert digest.hexdigest()==row['sha256']
                seen.add(member.name)
        while reader.read(1024**2):pass
        assert seen==set(wanted) and reader.digest.hexdigest()==index['archive_sha256'] and len(reader.verified)==len(index['parts'])
        recovered=directory/'ARCHIVE_INDEX.json';h.download(recovered,known['ARCHIVE_INDEX.json']);assert h.sha(recovered)==h.sha(O/'ARCHIVE_INDEX.json')
        proof=dict(passed=True,source_commit=sync['head'],release_url=release['html_url'],every_asset_actual_download_SHA_verified=True,whole_reassembled_archive_SHA_verified=True,every_decompressed_member_SHA_verified=True,recovery_index_download_SHA_verified=True,source_members=len(seen),archive_bytes=index['archive_bytes'],maximum_live_download_bytes=32*1024**2,models=0,physical_raw_deleted=False,verified_unix=time.time())
        h.dump(O/'FULL_REMOTE_VERIFIED.json',proof);h.ensure_uploaded(O/'FULL_REMOTE_VERIFIED.json',h.assets(h.read(h.O/'RELEASE.json')))
        recovered.unlink();directory.rmdir()
        # Only the verified duplicate transport is removed; all predicted states,
        # branch data, source inputs and physical recovery anchors stay local.
        for row in index['parts']:
            path=O/'closed_archive'/row['name'];assert h.sha(path)==row['sha256']
        for row in index['parts']:(O/'closed_archive'/row['name']).unlink()
        h.dump(O/'TRANSPORT_CLEANUP.json',dict(passed=True,only_verified_transport_removed=True,archive_bytes=index['archive_bytes'],predicted_response_and_braking_data_retained=True,physical_raw_deleted=False,models=0));h.dump(h.O/'FINALIZED.json',proof);print(json.dumps(proof))
    except BaseException as exc:
        import traceback
        h.dump(h.O/'ERROR.json',dict(error=repr(exc),traceback=traceback.format_exc(),unverified_originals_retained=True,models=0));raise
if __name__=='__main__':
    if '--qualify' in sys.argv:qualify()
    else:main()
