"""Local stream and SHA rejection qualification, no old worker launch."""
import copy
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile

from worker import O,R,C,RemoteReader,verify_stream,h


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not(O/'QUALIFICATION.json').exists()
    payload=b'current streamed recovery source member'*1000;member=tarfile.TarInfo('fixture/source.bin');member.size=len(payload)
    raw=io.BytesIO()
    with tarfile.open(fileobj=raw,mode='w:gz') as archive:
        archive.addfile(member,io.BytesIO(payload));link=tarfile.TarInfo('fixture/link');link.type=tarfile.SYMTYPE;link.linkname='source.bin';archive.addfile(link)
    compressed=raw.getvalue();pieces=[compressed[:31],compressed[31:]]
    rows=[dict(name='fixture.part%03d'%i,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())for i,b in enumerate(pieces)]
    assets={r['name']:dict(size=r['bytes'],digest='sha256:'+r['sha256'])for r in rows};memory={r['name']:b for r,b in zip(rows,pieces)}
    index=dict(files=[dict(path='fixture/source.bin',bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()),dict(path='fixture/link',symlink='source.bin')],parts=rows,archive_sha256=hashlib.sha256(compressed).hexdigest())
    with tempfile.TemporaryDirectory(dir=O) as root:
        folder=Path(root)
        def download(path,asset):path.write_bytes(memory[path.name])
        reader=RemoteReader(rows,assets,folder,download);assert verify_stream(reader,index)==2 and len(reader.verified)==2 and not list(folder.glob('*.part*'))
        bad=copy.deepcopy(index);bad['files'][0]['sha256']='0'*64
        reader=RemoteReader(rows,assets,folder,download)
        try:verify_stream(reader,bad)
        except AssertionError as exc:assert str(exc)=='ARCHIVE_MEMBER_SHA'
        else:raise AssertionError('WRONG_MEMBER_SHA_ACCEPTED')
        if reader.stream is not None:reader.stream.close()
    plan=h.read(O/'PLAN.json');assert plan['groups'] and all(g['archive_bytes']>0 for g in plan['groups'])
    proof=dict(passed=True,gzip_cross_asset_stream_member_and_link_and_whole_SHA=True,wrong_member_SHA_rejected=True,
               planned_groups=len(plan['groups']),planned_transport_bytes=plan['planned_logical_recovery_bytes'],
               finite_network_transport_reused_from_v1389=True,maximum_download_asset_bytes=32*1024**2,
               production_reader_source='experiments/v1382_weekend_campaign/deliver_full9390_preparation.py',models=0,physical_admission=False)
    h.dump(O/'QUALIFICATION.json',proof)
    files=[C/'worker.py',C/'qualify.py',C/'PROTOCOL.md',O/'PLAN.json',R/'experiments/v1389_idempotent_storage_transfer/resume.py',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py',R/'experiments/v1382_weekend_campaign/storage_preserve.py']
    h.dump(O/'SOURCE_FREEZE.json',dict(files={str(p.relative_to(R)):h.sha(p) for p in files},models=0));print(json.dumps(proof))


if __name__=='__main__':main()
