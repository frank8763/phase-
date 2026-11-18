"""Read back entire upstream groups; retain four exact saved-input files only."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import threading
import time
import urllib.request

R=Path(__file__).resolve().parents[2];O=R/'runs/v1299_paired_mechanism_study'
D=R/'records/v1281_backup_20261118'
NAMES={'EW_ONWARD_INPUT.json','EW_ONWARD_SELECTION.json','EW_ONWARD_TABLE.npz','EW_ONWARD_REFERENCE.npz'}


def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def restore(group,inventory,base):
    slot=int(group['group'][-2:]);errors=[];overall=hashlib.sha256();process=subprocess.Popen(['zstd','-q','-dc'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    def feed():
        try:
            for part in group['parts']:
                h=hashlib.sha256();n=0
                with urllib.request.urlopen(base+part['name'],timeout=60)as src:
                    for block in iter(lambda:src.read(1048576),b''):
                        h.update(block);overall.update(block);n+=len(block);process.stdin.write(block)
                assert n==part['bytes']and h.hexdigest()==part['sha256'],'UPSTREAM_COMPRESSED_SHA'
        except BaseException as exc:errors.append(repr(exc))
        finally:process.stdin.close()
    t=threading.Thread(target=feed,daemon=True);t.start();seen=set();retained=[];out=O/('input_slot%02d'%slot);out.mkdir(exist_ok=False)
    try:
        with tarfile.open(fileobj=process.stdout,mode='r|')as tar:
            for member in tar:
                assert member.isfile()and member.name in inventory and member.name not in seen,'INVALID_UPSTREAM_MEMBER'
                row=inventory[member.name];name=Path(member.name).name
                selected=member.name.startswith(f'runs/v858_nav2_verified/v1281/main_slot{slot:02}/')and name in NAMES
                target=out/name;tmp=target.with_suffix(target.suffix+'.tmp')
                stream=tar.extractfile(member);h=hashlib.sha256();f=tmp.open('xb')if selected else None
                try:
                    for block in iter(lambda:stream.read(1048576),b''):
                        h.update(block)
                        if f:f.write(block)
                finally:
                    if f:f.close()
                assert member.size==row['bytes']and h.hexdigest()==row['sha256'],'UPSTREAM_MEMBER_SHA'
                if selected:
                    tmp.replace(target);retained.append(dict(upstream_path=member.name,local_path=str(target.relative_to(R)),bytes=row['bytes'],sha256=row['sha256']))
                seen.add(member.name)
        while process.stdout.read(1048576):pass
        t.join(timeout=90);assert not t.is_alive()and not errors,errors
        assert process.wait(timeout=10)==0 and overall.hexdigest()==group['archive_sha256']and len(seen)==group['source_files'],'GROUP_READBACK'
        assert len(retained)==4 and {Path(x['local_path']).name for x in retained}==NAMES,'FOUR_REQUIRED_INPUTS'
        proof=dict(passed=True,slot=slot,verified_upstream_members=len(seen),compressed_bytes=group['archive_bytes'],retained=retained,models=0)
        dump(out/'RESTORED.json',proof);print(json.dumps(dict(slot=slot,restored_files=4,upstream_members_verified=len(seen))),flush=True);return proof
    finally:
        if process.poll()is None:process.kill();process.wait()


def main():
    assert(R/'REVIEW_PENDING').exists();O.mkdir(exist_ok=True);assert not(O/'RESTORE_COMPLETE.json').exists(),'NO_DUPLICATE_RESTORE'
    index=json.loads((D/'RECORD_INDEX.json').read_text());inventory={x['path']:x for x in json.loads((D/'SOURCE_INVENTORY.json').read_text())['files']}
    groups=[g for g in index['archives']if g['group']in[f'v1281-main_slot{s:02}'for s in range(17,25)]];assert len(groups)==8
    begin=time.monotonic();results=[];base='https://github.com/frank8763/phase-/releases/download/'+index['release_tag']+'/'
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        fs=[pool.submit(restore,g,inventory,base)for g in groups]
        for f in fs:results.append(f.result())
    dump(O/'RESTORE_COMPLETE.json',dict(passed=True,slots=results,wall_s=time.monotonic()-begin,physical_models=0,retained_bytes=sum(x['bytes']for g in results for x in g['retained'])))


if __name__=='__main__':main()
