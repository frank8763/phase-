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
from owner import R,C,O,read,sha,write
def used():
    import subprocess
    return int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],text=True).split()[0])


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
        native=read(O/'model/RESULT.json');assert native['closed'] and not native['passed'] and native['analytical_native']==200 and not native['analytical_inflight_unknown']
        assert native['nominal_native']==0 and native['complete_braking_branches']==1
        assert read(O/'CLOSED_REVIEW.json')['full_branch_proof_saved_before_refusal']
        chain=read(O/'RECOVERY_CHAIN.json');paths=set()
        for root in [C,O]:paths.update(p for p in root.rglob('*')if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts)
        paths.add(R/'docs/COMPLETE_TIMED_MODEL_V1417_REPORT.md')
        paths.add(R/'runs/v858_nav2_verified/v1378/steering_response/COMPONENT_INITIAL_PACKET.json')
        paths.update(R/n for n in chain['delta_additional_sources'])
        for row in chain['bases']:
            assert sha(R/row['index'])==row['index_sha256'] and sha(R/row['verified'])==row['verified_sha256'] and read(R/row['verified'])['passed']
            paths.update([R/row['index'],R/row['verified']])
        items=inventory(sorted(paths),{});wanted={r['path']:r for r in items};directory=O/'archive';directory.mkdir(exist_ok=False);before=used()
        class Parts(io.Parts):
            def write(self,data):
                assert self.total+len(data)<=32*1024**2 and before+self.total+len(data)+36*1024**2<10*1024**3, 'MODEL_ORIGIN_ARCHIVE_STORAGE_CAP'
                return super().write(data)
        writer=Parts(directory,'v1417-complete-timed-witness-refused')
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
        write(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='V1417 source, actual used saved input, complete failed200 proof/arrays and CLI/launch/closure evidence, with verified source/input base recovery chain; unrelated broad frozen run inventory is not duplicated'))
        write(O/'FINALIZED.json',dict(passed=True,scientific_passed=False,analytical_native=200,independent_audit_native=0,independent_audit_unexecuted=True,explicit_model_constructions=1,full_refused_branch_saved=True,delta_sources_and_audit_results_member_SHA_verified=True,archive_bytes=writer.total,members=len(items),physical_admission=False,models_during_archive=0))
        ledger=R/'runs/v1382_weekend_campaign/LEDGER.json';d=read(ledger);row=next(x for x in d['rounds']if x['id']==C.name);row.update(finalized=True,archive_index=str((O/'ARCHIVE_INDEX.json').relative_to(R)));write(ledger,d)
        print(json.dumps(read(O/'FINALIZED.json')))


if __name__=='__main__':main()
