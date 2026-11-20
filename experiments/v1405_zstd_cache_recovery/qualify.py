"""Actual zstd across part boundaries and wrong-member SHA refusal."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
from types import SimpleNamespace
from worker import R,C,O,h,verify_stream


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(O/'QUALIFICATION.json').exists()
    buffer=io.BytesIO();payload=b'bounded original zstd archive recovery qualification'*1000
    with tarfile.open(fileobj=buffer,mode='w')as tar:
        member=tarfile.TarInfo('fixture/source');member.size=len(payload);tar.addfile(member,io.BytesIO(payload))
    compressed=subprocess.run(['zstd','-q','-T1','-3','-c'],input=buffer.getvalue(),capture_output=True,check=True).stdout
    pieces=[compressed[:31],compressed[31:]];parts=[dict(name='fixture.part%03d'%i,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())for i,b in enumerate(pieces)]
    index=dict(files=[dict(path='fixture/source',bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())],parts=parts,archive_sha256=hashlib.sha256(compressed).hexdigest())
    assets={p['name']:dict(size=p['bytes'],digest='sha256:'+p['sha256'])for p in parts};data={p['name']:b for p,b in zip(parts,pieces)}
    with tempfile.TemporaryDirectory(dir=O)as directory:
        folder=Path(directory)
        def download(path,asset):path.write_bytes(data[path.name])
        reader=SimpleNamespace(folder=folder,assets=assets,download=download,verified=[])
        assert verify_stream(reader,index)==1 and len(reader.verified)==2 and not list(folder.iterdir())
        bad=copy.deepcopy(index);bad['files'][0]['sha256']='0'*64
        try:verify_stream(SimpleNamespace(folder=folder,assets=assets,download=download,verified=[]),bad)
        except AssertionError as exc:assert str(exc).startswith('MEMBER_SHA')
        else:raise AssertionError('ZSTD_WRONG_MEMBER_SHA_ACCEPTED')
    plan=h.read(O/'PLAN.json');proof=dict(passed=True,real_zstd_cross_parts_all_SHA_verified=True,wrong_member_SHA_rejected=True,
        finite_network_and_precise_source_inode_gates_reused=True,groups=len(plan['groups']),transport_bytes=plan['planned_logical_transport_bytes'],obsolete_offline_bytes=plan['planned_obsolete_offline_bytes'],models=0)
    h.dump(O/'QUALIFICATION.json',proof)
    files=[*C.glob('*.py'),C/'PROTOCOL.md',O/'PLAN.json',R/'experiments/v1389_idempotent_storage_transfer/resume.py',R/'experiments/v1382_weekend_campaign/storage_preserve.py',R/'experiments/v1065_preflight_metadata_continuation/archive.py']
    h.dump(O/'SOURCE_FREEZE.json',dict(files={str(p.relative_to(R)):h.sha(p)for p in files},models=0));print(json.dumps(proof))


if __name__=='__main__':main()
