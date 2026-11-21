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
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1443_task_local_initializer_cache'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
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
        assert(R/'REVIEW_PENDING').read_bytes()==(R/'runs/v1417_complete_timed_witness/REVIEW_PENDING.before').read_bytes()
        frozen=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
        native=read(O/'CLOSED_REVIEW.json');assert native['actual_native']==native['private_prediction_native']==native['own_replay_native']==0
        assert native['passed']is False and read(R/'runs/v1445_immutable_initializer_writeguard/ENTRY_QUALIFICATION.json')['passed']
        latest=read(R/'runs/v1445_immutable_initializer_writeguard/SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in latest.items())
        paths=set()
        for index in range(1443,1447):
            for parent in [R/'experiments',R/'runs']:
                matches=list(parent.glob('v%d_*'%index));assert len(matches)==1
                paths.update(p for p in matches[0].rglob('*')if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts)
        paths.update([R/'docs/WEEKEND_CAMPAIGN_V1382_PROGRESS.md',R/'RESEARCH_STATUS.md',R/'CURRENT_EXPERIMENT.json',R/'runs/v1382_weekend_campaign/LEDGER.json'])
        base=R/'runs/v1441_initializer_definition_import'
        for name in ['ARCHIVE_INDEX.json','FULL_REMOTE_VERIFIED.json','TRANSPORT_CLEANUP.json']:paths.add(base/name)
        assert read(base/'FULL_REMOTE_VERIFIED.json')['passed']
        items=inventory(sorted(paths),{});wanted={r['path']:r for r in items};directory=O/'archive';directory.mkdir(exist_ok=False);before=used()
        class Parts(io.Parts):
            def write(self,data):
                assert self.total+len(data)<=32*1024**2 and before+self.total+len(data)+32*1024**2+512*1024**2<10*1024**3, 'MODEL_ORIGIN_ARCHIVE_STORAGE_CAP'
                return super().write(data)
        writer=Parts(directory,'v1443-v1446-immutable-guard-failure-and-source')
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
        write(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='V1443 one failed initializer call with original machine RESULT absent, complete first and secondary errors retained in bounded console, unknown canonical/internal model counts and uncharged native Mesa cache files. V1445 original guard immutable OUT and actual no-model OSMesa native cache disable qualified; no complete initializer or navigation PASS'))
        write(O/'FINALIZED.json',dict(passed=True,scientific_navigation_passed=False,models=0,analytical_native=0,physical_native=0,original_guard_immutable_scope_and_no_model_OSMesa_qualified=True,V1443_machine_RESULT_gap_and_complete_console_failure_retained=True,delta_sources_and_audit_results_member_SHA_verified=True,archive_bytes=writer.total,members=len(items),physical_admission=False,models_during_archive=0))
        print(json.dumps(read(O/'FINALIZED.json')))


if __name__=='__main__':main()
