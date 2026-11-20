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
        frozen=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
        native=read(O/'RESULT.json');assert native['closed']and native['passed']and native['analytical_native']==400 and not native['analytical_inflight_unknown']and native['maximum_state_ctrl_error']==0
        paths=set()
        for root in [C,O,R/'experiments/v1415_unified_causal_witness',R/'runs/v1415_unified_causal_witness',R/'experiments/v1414_current_timed_geometry']:paths.update(p for p in root.rglob('*')if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts)
        paths.update([R/'docs/UNIFIED_TIMED_RESERVE_V1416_REPORT.md',R/'runs/v1410_scalar_feedback_witness/ARCHIVE_INDEX.json',R/'runs/v1410_scalar_feedback_witness/FULL_REMOTE_VERIFIED.json',R/'runs/v1383_exact_timed_handoff/ARCHIVE_INDEX.json',R/'runs/v1383_exact_timed_handoff/FULL_REMOTE_VERIFIED.json'])
        items=inventory(sorted(paths),{});wanted={r['path']:r for r in items};directory=O/'archive';directory.mkdir(exist_ok=False);before=used()
        class Parts(io.Parts):
            def write(self,data):
                assert self.total+len(data)<=32*1024**2 and before+self.total+len(data)+36*1024**2<10*1024**3, 'MODEL_ORIGIN_ARCHIVE_STORAGE_CAP'
                return super().write(data)
        writer=Parts(directory,'v1416-current-timed-reserve-qualified')
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
        write(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='new V1415/V1416 complete bound causal backend, zero-model CLI/storage evidence and complete400 numerical qualification; old V1413 failure retained via explicit verified recovery chain'))
        write(O/'FINALIZED.json',dict(passed=True,current_timed_reserve_qualification_passed=True,analytical_native=400,independent_comparison_native=200,explicit_model_constructions=2,delta_sources_and_audit_results_member_SHA_verified=True,archive_bytes=writer.total,members=len(items),physical_admission=False,models_during_archive=0))
        ledger=R/'runs/v1382_weekend_campaign/LEDGER.json';d=read(ledger);row=next(x for x in d['rounds']if x['id']==C.name);row.update(finalized=True,archive_index=str((O/'ARCHIVE_INDEX.json').relative_to(R)));write(ledger,d)
        print(json.dumps(read(O/'FINALIZED.json')))


if __name__=='__main__':main()
