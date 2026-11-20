"""Zero-model source/used-input/full-failed-model archive closure."""
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tarfile
import time
from owner import R,C,O,read,sha,write,used


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not(O/'ARCHIVE_CLAIM.json').exists() and read(O/'COMPLETION.json')['closed']
    write(O/'ARCHIVE_CLAIM.json',dict(started_unix=time.time(),models=0))
    io=load('v1401_original_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py')
    inventory=load('v1401_original_link_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert(R/'REVIEW_PENDING').read_bytes()==(O/'REVIEW_PENDING.before').read_bytes()
        frozen=read(O/'NUMERIC_SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
        native=read(O/'model/RESULT.json');assert native['closed']and native['passed']and not read(O/'COMPLETION.json')['passed']and native['analytical_native']==791940 and not native['analytical_inflight_unknown']
        paths=set()
        for root in [C,O]:paths.update(p for p in root.rglob('*')if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts)
        fixed=read(O/'FIXED_INPUTS.json');paths.update([R/fixed['origin_file'],O/'model/CURRENT_INPUT.json',O/'model/SETUP.json',R/'docs/SCALAR_FEEDBACK_MODEL_V1410_REPORT.md'])
        items=inventory(sorted(paths),frozen);wanted={r['path']:r for r in items};directory=O/'archive';directory.mkdir(exist_ok=False);before=used()
        class Parts(io.Parts):
            def write(self,data):
                assert before+self.total+len(data)+36*1024**2<10*1024**3, 'MODEL_ORIGIN_ARCHIVE_STORAGE_CAP'
                return super().write(data)
        writer=Parts(directory,'v1410-scalar-feedback-json-failure')
        with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3,mtime=0)as compressor,tarfile.open(fileobj=compressor,mode='w|')as archive:
            for row in items:
                member=tarfile.TarInfo(row['path'])
                if 'symlink'in row:member.type=tarfile.SYMTYPE;member.linkname=row['symlink'];archive.addfile(member)
                else:
                    member.size=row['bytes']
                    with(R/row['path']).open('rb')as stream:archive.addfile(member,stream)
        writer.finish();parts=[];whole=hashlib.sha256()
        for row in writer.parts:
            p=directory/row['name'];assert row['bytes']<=32*1024**2 and sha(p)==row['sha256'];parts.append(p)
            with p.open('rb')as stream:
                for block in iter(lambda:stream.read(1024**2),b''):whole.update(block)
        assert whole.hexdigest()==writer.digest.hexdigest();seen=set()
        with tarfile.open(fileobj=io.Reader(parts),mode='r|gz')as archive:
            for member in archive:
                assert member.name in wanted and member.name not in seen;row=wanted[member.name]
                if 'symlink'in row:assert member.issym()and member.linkname==row['symlink']
                else:
                    assert member.isfile()and member.size==row['bytes'];stream=archive.extractfile(member);digest=hashlib.sha256()
                    for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
                    assert digest.hexdigest()==row['sha256']
                seen.add(member.name)
        assert seen==set(wanted)and all(sha(R/n)==h for n,h in frozen.items())
        write(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='qualification source and explicitly used saved packet/setup plus all new qualification evidence; unused historical runs referenced by frozen manifest'))
        write(O/'FINALIZED.json',dict(passed=True,complete_model_witness_passed=False,analytical_native=791940,independent_audit_native=0,explicit_model_constructions=1,source_and_used_inputs_and_failed_evidence_member_SHA_verified=True,archive_bytes=writer.total,members=len(items),physical_admission=False,models_during_archive=0))
        ledger=R/'runs/v1382_weekend_campaign/LEDGER.json';d=read(ledger);row=next(x for x in d['rounds']if x['id']==C.name);row.update(finalized=True,archive_index=str((O/'ARCHIVE_INDEX.json').relative_to(R)));write(ledger,d)
        print(json.dumps(read(O/'FINALIZED.json')))


if __name__=='__main__':main()
