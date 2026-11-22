"""One verified part on disk; full archive readback; retain exact two inputs."""
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import tarfile
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
INDEX=R/'runs/v1382_weekend_campaign/storage/v1237/v1237.INDEX.json'
PROOF=R/'runs/v1382_weekend_campaign/storage/v1237/FULL_REMOTE_VERIFIED.json'
NAMES={'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_ROWS.json',
       'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_RECOVERY_INPUT.json'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def save(name,value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
    assert len(raw)<2*1024**2
    tmp=O/(name+'.tmp');tmp.write_bytes(raw);tmp.replace(O/name)


class Parts(io.RawIOBase):
    def __init__(self,index):
        self.index=index;self.parts=iter(index['parts']);self.current=None
        self.path=None;self.whole=hashlib.sha256();self.verified=[];self.total=0

    def readable(self):return True

    def _next(self):
        if self.current is not None:
            self.current.close();self.current=None
            self.path.unlink() # only just-verified duplicate transport
        row=next(self.parts,None)
        if row is None:return False
        assert row['bytes']<=32*1024**2 and Path(row['name']).name==row['name']
        tag=self.index['release_url'].rsplit('/',1)[-1]
        gh=R/'tools/phase_storage_20261107/vendor/gh'
        subprocess.run([str(gh),'release','download',tag,'--repo','frank8763/phase-',
            '--pattern',row['name'],'--dir',str(O/'download')],check=True,timeout=45,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.path=O/'download'/row['name']
        assert self.path.stat().st_size==row['bytes'] and sha(self.path)==row['sha256']
        self.verified.append(row);save('PART_PROGRESS.json',dict(verified=self.verified,models=0))
        self.current=self.path.open('rb');return True

    def readinto(self,buffer):
        while True:
            if self.current is None and not self._next():return 0
            block=self.current.read(len(buffer))
            if block:
                self.whole.update(block);self.total+=len(block);buffer[:len(block)]=block;return len(block)
            if not self._next():return 0

    def close(self):
        if self.current is not None:self.current.close()
        super().close()


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    start=time.monotonic();now=time.time();assert now+900<1795395600
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('RECOVERY_900S')));signal.alarm(900)
    parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
    assert parent['active_round']is None and not parent['models_now_authorized']
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    usage=int(subprocess.check_output(['du','-s','-B1',str(R/'runs')]).split()[0]);assert usage+545*1024**2<15*1024**3
    expected=next(v for v in json.loads((R/'records/weekend_storage_v1382_20261120/RECOVERY_INDEX.json').read_text())['verified_groups']if v['group']=='v1237')
    assert sha(INDEX)==expected['recovery_index_sha256']
    proof=json.loads(PROOF.read_text());assert proof['passed']and proof['every_asset_actual_download_SHA_verified']and proof['every_decompressed_member_SHA_verified']and proof['recovery_index_download_SHA_verified']
    with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=now,models=0,index_sha256=sha(INDEX),prior_remote_proof_sha256=sha(PROOF),allruns_bytes=usage),f)
    result=dict(passed=False,closed=False,models=0,physical_native=0,proposal_only=True,not_fresh_input=True,retained=[])
    parts=None
    with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            index=json.loads(INDEX.read_text());files={row['path']:row for row in index['files']}
            assert NAMES.issubset(files)and sum(files[n]['bytes']for n in NAMES)<1024**2
            (O/'download').mkdir();(O/'retained').mkdir();parts=Parts(index);seen=set()
            with io.BufferedReader(parts,buffer_size=1024**2)as reader:
                with tarfile.open(fileobj=reader,mode='r|gz')as archive:
                    for member in archive:
                        assert member.isfile()and member.name in files and member.name not in seen
                        row=files[member.name];assert member.size==row['bytes']
                        output=O/'retained'/Path(member.name).name
                        stream=archive.extractfile(member);h=hashlib.sha256();length=0
                        target=output.open('xb')if member.name in NAMES else None
                        try:
                            for block in iter(lambda:stream.read(1024**2),b''):
                                length+=len(block);h.update(block)
                                if target:target.write(block)
                        finally:
                            if target:target.close()
                        assert length==row['bytes']and h.hexdigest()==row['sha256']
                        if member.name in NAMES:
                            result['retained'].append(dict(original=member.name,path=str(output.relative_to(R)),bytes=length,sha256=h.hexdigest()))
                            save('SELECTED_PROGRESS.json',result)
                        seen.add(member.name)
                while reader.read(1024**2):pass
            assert len(seen)==len(files)and len(result['retained'])==2
            assert parts.total==index['archive_bytes']and parts.whole.hexdigest()==index['archive_sha256']
            assert len(parts.verified)==len(index['parts'])
            result.update(passed=True,verified_members=len(seen),parts=len(parts.verified),archive_sha256=parts.whole.hexdigest(),index_sha256=sha(INDEX))
        except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
        finally:
            signal.alarm(0);result.update(closed=True,wall_s=time.monotonic()-start);save('RESULT.json',result)
    print(json.dumps(result));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
