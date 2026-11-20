"""Zero-model symlink-aware source archive after both V1383 tasks passed."""
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;P=R/'runs'/C.name
SCI=R/'experiments/v1383_exact_timed_handoff';O=R/'runs/v1383_exact_timed_handoff';RAW=R/'runs/v858_nav2_verified/v1383'
spec=importlib.util.spec_from_file_location('archive_recovery_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py')
io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)

def target_inside(path,target):
    target=Path(target);resolved=Path(os.path.normpath(str(target if target.is_absolute() else path.parent/target)))
    assert resolved.is_relative_to(R),'SOURCE_LINK_ESCAPES_PHASE'
    return resolved

def inventory(paths,frozen):
    rows={}
    def add(p,follow_source=False,chain=()):
        assert p.is_relative_to(R) and p not in chain and len(chain)<32,'SOURCE_LINK_CYCLE_OR_ESCAPE'
        name=str(p.relative_to(R))
        if name in rows:
            if follow_source and 'symlink' in rows[name]:add(target_inside(p,rows[name]['symlink']),True,chain+(p,))
            return
        if p.is_symlink():
            target=p.readlink();rows[name]=dict(path=name,symlink=str(target))
            if follow_source:add(target_inside(p,target),True,chain+(p,))
        else:
            assert p.is_file(),'MISSING_REGULAR_SOURCE '+name
            rows[name]=dict(path=name,bytes=p.stat().st_size,sha256=io.sha(p))
    for p in paths:add(p)
    for name in frozen:
        if not name.startswith('runs/'):add(R/name,True)
    # Source symlinks may have appeared first in a tree inventory. Resolve their
    # target bytes as well, while preserving the link itself in the archive.
    for name in list(rows):
        if name in frozen and 'symlink' in rows[name]:add(target_inside(R/name,rows[name]['symlink']),True,(R/name,))
    return list(rows.values())

def main():
    assert not (P/'CLAIM.json').exists() and io.read(P/'QUALIFICATION.json')['passed']
    io.dump(P/'CLAIM.json',dict(started_unix=time.time(),models=0,old_finalizer_not_restarted=True))
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (O/'FINALIZED.json').exists() and io.read(O/'FINALIZER_EXIT.json')['returncode']==1
        summary=io.read(O/'COMPLETION.json');assert summary['passed'] and summary['closed'] and not summary['unexecuted']
        assert (R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
        for row in summary['results']:
            assert row['passed'] and row['native']['passed'] and row['audit']['passed'] and all(row['audit']['checks'].values())
        freeze=io.read(SCI/'SOURCE_FREEZE.json')['files']
        assert all(io.sha(R/name)==h for name,h in freeze.items())
        assert all(io.sha(R/name)==h for name,h in io.read(P/'SOURCE_FREEZE.json')['files'].items())
        files=set()
        for root in [SCI,O,RAW,C,P,R/'experiments/v1379_timed_response_preparation',R/'runs/v1379_timed_response_preparation']:
            for p in root.rglob('*'):
                if p.is_file() or p.is_symlink():
                    if '__pycache__' not in p.parts and 'transport_scratch' not in p.parts:files.add(p)
        files.add(R/'docs/EXACT_TIMED_HANDOFF_V1383_REPORT.md')
        items=inventory(sorted(files),freeze);wanted={row['path']:row for row in items}
        directory=P/'archive';directory.mkdir(exist_ok=False)
        before=io.usage()
        class BoundedParts(io.Parts):
            def write(self,data):
                assert before+self.total+len(data)+4*1024**2<10*1024**3,'ARCHIVE_TEMPORARY_STORAGE_CAP'
                return super().write(data)
        writer=BoundedParts(directory,'v1383-source-complete')
        with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3,mtime=0) as compressor,tarfile.open(fileobj=compressor,mode='w|') as archive:
            for row in items:
                member=tarfile.TarInfo(row['path'])
                if 'symlink' in row:member.type=tarfile.SYMTYPE;member.linkname=row['symlink'];archive.addfile(member)
                else:
                    member.size=row['bytes']
                    with (R/row['path']).open('rb') as stream:archive.addfile(member,stream)
        writer.finish();parts=[];whole=hashlib.sha256()
        for row in writer.parts:
            p=directory/row['name'];assert row['bytes']<=32*1024**2 and io.sha(p)==row['sha256'];parts.append(p)
            with p.open('rb') as stream:
                for b in iter(lambda:stream.read(1024**2),b''):whole.update(b)
        assert whole.hexdigest()==writer.digest.hexdigest();seen=set()
        with tarfile.open(fileobj=io.Reader(parts),mode='r|gz') as archive:
            for member in archive:
                assert member.name in wanted and member.name not in seen;row=wanted[member.name]
                if 'symlink' in row:assert member.issym() and member.linkname==row['symlink']
                else:
                    assert member.isfile() and member.size==row['bytes'];h=hashlib.sha256();stream=archive.extractfile(member)
                    for b in iter(lambda:stream.read(1024**2),b''):h.update(b)
                    assert h.hexdigest()==row['sha256']
                seen.add(member.name)
        assert seen==set(wanted) and all(io.sha(R/name)==h for name,h in freeze.items())
        index=dict(files=items,parts=writer.parts,archive_sha256=writer.digest.hexdigest(),archive_bytes=writer.total,local_members_and_reassembly_verified=True,remote_download_restore_verified=False,raw_deleted=False,models=0,recovery_entry=str((C/'archive.py').relative_to(R)),old_finalizer_failure_retained=True)
        assert not (O/'ARCHIVE_INDEX.json').exists();io.dump(P/'ARCHIVE_INDEX.json',index);io.dump(O/'ARCHIVE_INDEX.json',index)
        for row,p in zip(writer.parts,parts):
            target=O/'archive'/row['name'];assert not target.exists();os.link(p,target)
        proof=dict(passed=True,timed_handoff_pair_passed=True,local_memberSHA_and_reassembly_verified=True,source_unchanged=True,symlink_members=sum('symlink' in row for row in items),frozen_source_link_targets_archived=True,raw_directory_links_preserved_as_text=True,recovery_entry=str((C/'archive.py').relative_to(R)),old_finalizer_failure_retained=True,models=0)
        io.dump(P/'FINALIZED.json',proof);io.dump(O/'FINALIZED.json',proof)
        p=R/'runs/v1382_weekend_campaign/LEDGER.json';ledger=io.read(p);record=next(x for x in ledger['rounds'] if x['id']==SCI.name)
        record.update(status='CLOSED_PASSED',finalized=True,full32210_handoff_qualified=True,archive_index=str((O/'ARCHIVE_INDEX.json').relative_to(R)),archive_recovery=str(P.relative_to(R)))
        ledger.update(latest_32210_handoff_qualified=True,status='ROUND_CLOSED_REVIEW_REQUIRED',models_now_authorized=False);io.dump(p,ledger)
        pointer=io.read(R/'CURRENT_EXPERIMENT.json');pointer['latest_v1383'].update(full32210_handoff_qualified=True,archive_recovered=True);io.dump(R/'CURRENT_EXPERIMENT.json',pointer)
        print(json.dumps(dict(proof,archive_members=len(items),archive_bytes=writer.total)))

if __name__=='__main__':main()
