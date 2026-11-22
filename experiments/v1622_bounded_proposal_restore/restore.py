"""Bounded selected-member recovery; original failure bytes never modified."""
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import signal
import tarfile
import time
import traceback
import urllib.request

R=Path(__file__).resolve().parents[2];O=R/'runs/v1622_bounded_proposal_restore'
OLD=R/'runs/v1621_mechanism_input_recovery'
INDEX=R/'runs/v1382_weekend_campaign/storage/v1237/v1237.INDEX.json'
PROOF=R/'runs/v1382_weekend_campaign/storage/v1237/FULL_REMOTE_VERIFIED.json'
WANTED={'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_ROWS.json',
        'runs/v858_nav2_verified/v1237/route_main_EAST_WEST/ROUTE_RECOVERY_INPUT.json'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def save(name,value):
    p=O/name;t=p.with_suffix(p.suffix+'.tmp');raw=json.dumps(value,sort_keys=True,allow_nan=False).encode()+b'\n'
    assert len(raw)<1024**2;t.write_bytes(raw);t.replace(p)


class VerifiedParts(io.RawIOBase):
    def __init__(self,index):
        self.index=index;self.iterator=iter(index['parts']);self.current=None
        self.path=None;self.verified=[];self.compressed_consumed=0
    def readable(self):return True
    def next_part(self):
        if self.current:
            self.current.close();self.current=None
            self.path.unlink() # only this new fullySHAverified duplicate transport
        row=next(self.iterator,None)
        if row is None:return False
        assert row['bytes']<=32*1024**2 and Path(row['name']).name==row['name']
        path=O/'download'/row['name'];offset=0
        if not self.verified:
            partial=OLD/'download'/row['name'];assert partial.is_file()and partial.stat().st_size==17035885
            shutil.copyfile(partial,path);offset=path.stat().st_size
            save('PARTIAL_SOURCE.json',dict(path=str(partial.relative_to(R)),bytes=offset,sha256=sha(partial)))
        url=self.index['release_url'].replace('/tag/','/download/')+'/'+row['name']
        headers={'Range':f'bytes={offset}-{row["bytes"]-1}'} if offset else {}
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=180)as response:
            if offset:
                assert response.status==206 and response.headers['Content-Range'].startswith(f'bytes {offset}-')
            else:assert response.status==200
            count=offset
            with path.open('ab'if offset else'xb')as target:
                for block in iter(lambda:response.read(1024**2),b''):
                    count+=len(block);assert count<=row['bytes'];target.write(block)
        assert path.stat().st_size==row['bytes']and sha(path)==row['sha256']
        self.verified.append(row);save('PART_PROGRESS.json',dict(verified=self.verified,selected_only=True))
        self.path=path;self.current=path.open('rb');return True
    def readinto(self,buffer):
        while True:
            if self.current is None and not self.next_part():return 0
            block=self.current.read(len(buffer))
            if block:
                self.compressed_consumed+=len(block);buffer[:len(block)]=block;return len(block)
            if not self.next_part():return 0
    def close(self):
        if self.current:self.current.close()
        super().close()


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    start=time.monotonic();now=time.time()
    deadline=json.loads((R/'runs/v1620_mechanism_boundary/EVALUATION_AUTHORIZATION.json').read_text())['absolute_deadline_unix']
    assert now+1200<deadline
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SELECTED_RESTORE1200S')));signal.alarm(1200)
    assert json.loads((OLD/'RESULT.json').read_text())['passed']is False
    original=json.loads((R/'records/weekend_storage_v1382_20261120/RECOVERY_INDEX.json').read_text())
    group=next(g for g in original['verified_groups']if g['group']=='v1237')
    assert sha(INDEX)==group['recovery_index_sha256']and json.loads(PROOF.read_text())['passed']
    parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']
    assert (R/'REVIEW_PENDING').is_file()
    with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=now,models=0,index_sha256=sha(INDEX)),f)
    result=dict(passed=False,closed=False,models=0,physical_native=0,retained=[],new_full_archive_readback=False,prior_full_archive_proof=str(PROOF.relative_to(R)),prior_full_archive_proof_sha256=sha(PROOF))
    parts=None
    with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            (O/'download').mkdir();(O/'retained').mkdir();index=json.loads(INDEX.read_text());known={r['path']:r for r in index['files']};parts=VerifiedParts(index);seen=set()
            with io.BufferedReader(parts,buffer_size=1024**2)as reader:
                with tarfile.open(fileobj=reader,mode='r|gz')as archive:
                    for member in archive:
                        assert member.isfile()and member.name in known and member.name not in seen
                        expected=known[member.name];assert member.size==expected['bytes']
                        stream=archive.extractfile(member);h=hashlib.sha256();n=0
                        output=O/'retained'/Path(member.name).name;target=output.open('xb')if member.name in WANTED else None
                        try:
                            for block in iter(lambda:stream.read(1024**2),b''):
                                h.update(block);n+=len(block)
                                if target:target.write(block)
                        finally:
                            if target:target.close()
                        assert n==expected['bytes']and h.hexdigest()==expected['sha256']
                        seen.add(member.name)
                        if member.name in WANTED:
                            result['retained'].append(dict(original=member.name,path=str(output.relative_to(R)),bytes=n,sha256=h.hexdigest()))
                            save('SELECTED_PROGRESS.json',result)
                        if len(result['retained'])==2:break
            assert {r['original']for r in result['retained']}==WANTED
            result.update(passed=True,decoded_members_SHA_verified=len(seen),accessed_parts_all_SHA_verified=parts.verified,compressed_prefix_consumed=parts.compressed_consumed,all_selected_members_index_SHA_verified=True)
        except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
        finally:
            signal.alarm(0);result.update(closed=True,wall_s=time.monotonic()-start);save('RESULT.json',result)
    print(json.dumps(result));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
