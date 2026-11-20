"""Close the old Friday evidence ledger without reopening its model window."""
import fcntl
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import tarfile

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
spec=importlib.util.spec_from_file_location('old_day_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py')
io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)

def main():
    O.mkdir(exist_ok=False);io.dump(O/'CLAIM.json',dict(started_unix=time.time(),models=0))
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ledger=io.read(R/'runs/v1374_day_handoff_validation/DAY_LEDGER.json');guard=(R/'REVIEW_PENDING').read_bytes()
        assert ledger['status']=='REVIEW_PENDING' and ledger['day_total_component_attempts']==5
        assert ledger['actual_total_native']==96811==ledger['own_replay_native']
        assert ledger['historical_prefix_replay_native']==92591 and ledger['new_component_native']==4220
        assert ledger['canonical_vehicle_initializations']==5 and ledger['navigation_tasks_started']==0
        assert ledger['component_tasks_started']==4 and ledger['supplemental_components_started']==1
        assert not ledger['full9390_handoff_qualified'] and not ledger['full32210_handoff_qualified']
        accounting=dict(original_components=4,supplemental_components=1,total_attempts=5,actual_total_native=96811,historical_native=92591,new_native=4220,own_replay_native=96811,canonical_vehicle_initializations=5,internal_factory_model_constructions=None,navigation=0,full9390=False,full32210=False,supplemental_repeat_unexecuted=True,known_preparation_analytical_native=190600,unknown_preparation_analytical_attempts=1,unknown_preparation_analytical_upper_bound=3730,supplemental_cleanup_analytical_native=200,models_during_closure=0)
        io.dump(O/'ACCOUNTING.json',accounting)
        files=set()
        for root in [C,R/'experiments/v1377_timed_handoff_witness',R/'runs/v1377_timed_handoff_witness']:
            files.update(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
        files.update((R/'docs').glob('*V1377*.md'))
        files.update([R/'runs/v1374_day_handoff_validation/DAY_LEDGER.json',O/'ACCOUNTING.json',R/'docs/DAY_HANDOFF_PROGRESS_20261120.md',R/'docs/TIMED_HANDOFF_V1380_FAILURE_DIAGNOSIS.md'])
        items=[]
        for p in sorted(files):
            assert p.is_file() and not p.is_symlink();items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=io.sha(p)))
        directory=O/'archive';directory.mkdir();writer=io.Parts(directory,'v1377-final-zero-model')
        with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3,mtime=0) as compressor,tarfile.open(fileobj=compressor,mode='w|') as archive:
            for row in items:
                member=tarfile.TarInfo(row['path']);member.size=row['bytes']
                with (R/row['path']).open('rb') as stream:archive.addfile(member,stream)
        writer.finish();digest=hashlib.sha256();parts=[]
        for row in writer.parts:
            p=directory/row['name'];assert row['bytes']<=32*1024**2 and io.sha(p)==row['sha256'];parts.append(p)
            with p.open('rb') as stream:
                for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
        assert digest.hexdigest()==writer.digest.hexdigest();wanted={row['path']:row for row in items};seen=set()
        with tarfile.open(fileobj=io.Reader(parts),mode='r|gz') as archive:
            for member in archive:
                assert member.isfile() and member.name in wanted and member.name not in seen
                row=wanted[member.name];assert member.size==row['bytes'];stream=archive.extractfile(member);h=hashlib.sha256()
                for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
                assert h.hexdigest()==row['sha256'];seen.add(member.name)
        assert seen==set(wanted) and (R/'REVIEW_PENDING').read_bytes()==guard
        io.dump(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_sha256=writer.digest.hexdigest(),archive_bytes=writer.total,local_members_and_reassembly_verified=True,remote_download_restore_verified=False,raw_deleted=False,models=0))
        proof=dict(passed=True,old_day_status='REVIEW_PENDING',old_day_counts_unchanged=True,archive_members=len(items),archive_bytes=writer.total,all_member_decompressed_SHA_and32MiB_reassembly_verified=True,source_originals_retained=True,models=0,closed_unix=time.time(),new_weekend_authorization_not_revoked=True)
        io.dump(O/'FINALIZED.json',proof);print(json.dumps(proof))

if __name__=='__main__':main()
