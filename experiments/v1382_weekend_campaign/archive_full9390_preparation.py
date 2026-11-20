"""Source-complete, zero-model closure of the one V1393 analytical round."""
import fcntl
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import time
R=Path(__file__).resolve().parents[2];C=R/'experiments/v1393_full9390_preparation';O=R/'runs/v1393_full9390_preparation'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
io=load('preparation_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py')
source=load('qualified_source_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py')
def main():
    assert io.read(O/'ANALYSIS_COMPLETION.json')['closed'] and not (O/'ARCHIVE_CLAIM.json').exists()
    io.dump(O/'ARCHIVE_CLAIM.json',dict(started_unix=time.time(),models=0,source_sha256=io.sha(Path(__file__))))
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
        frozen=io.read(O/'ANALYSIS_SOURCE_FREEZE.json')['files'];assert all(io.sha(R/name)==h for name,h in frozen.items())
        paths={R/name for name in frozen}
        for root in [C,O]:
            paths.update(p for p in root.rglob('*') if (p.is_file() or p.is_symlink()) and '__pycache__' not in p.parts)
        paths.update([Path(__file__).resolve(),R/'docs/FULL9390_V1393_ANALYSIS_REPORT.md'])
        items=source.inventory(sorted(paths),frozen);wanted={x['path']:x for x in items}
        directory=O/'closed_archive';directory.mkdir(exist_ok=False);before=io.usage()
        class BoundedParts(io.Parts):
            def write(self,data):
                assert before+self.total+len(data)+4*1024**2<10*1024**3,'TOTAL_TEMPORARY_ARCHIVE_CAP'
                return super().write(data)
        writer=BoundedParts(directory,'v1393-source-complete')
        with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3,mtime=0) as compressor,tarfile.open(fileobj=compressor,mode='w|') as archive:
            for row in items:
                member=tarfile.TarInfo(row['path'])
                if 'symlink' in row:member.type=tarfile.SYMTYPE;member.linkname=row['symlink'];archive.addfile(member)
                else:
                    member.size=row['bytes']
                    with (R/row['path']).open('rb') as stream:archive.addfile(member,stream)
        writer.finish();whole=hashlib.sha256();parts=[]
        for row in writer.parts:
            p=directory/row['name'];assert row['bytes']<=32*1024**2 and io.sha(p)==row['sha256'];parts.append(p)
            with p.open('rb') as stream:
                for block in iter(lambda:stream.read(1024**2),b''):whole.update(block)
        assert whole.hexdigest()==writer.digest.hexdigest();seen=set()
        with tarfile.open(fileobj=io.Reader(parts),mode='r|gz') as archive:
            for member in archive:
                assert member.name in wanted and member.name not in seen;row=wanted[member.name]
                if 'symlink' in row:assert member.issym() and member.linkname==row['symlink']
                else:
                    assert member.isfile() and member.size==row['bytes'];stream=archive.extractfile(member);h=hashlib.sha256()
                    for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
                    assert h.hexdigest()==row['sha256']
                seen.add(member.name)
        assert seen==set(wanted) and all(io.sha(R/name)==h for name,h in frozen.items())
        index=dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,raw_deleted=False,models=0)
        io.dump(O/'ARCHIVE_INDEX.json',index);io.dump(O/'FINALIZED.json',dict(passed=True,analysis_passed=io.read(O/'ANALYSIS_RESULT.json')['passed'],physical_admission=False,actual_moving_response_qualified=False,source_members=len(items),archive_bytes=writer.total,full_source_and_data_member_SHA_and32MiB_reassembly_verified=True,models=0))
        print(json.dumps(io.read(O/'FINALIZED.json')))
if __name__=='__main__':main()
