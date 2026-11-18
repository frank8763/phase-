"""Bounded authenticated-CLI readback for five incomplete public-stream groups.

Separate target directories preserve original stream artifacts/errors; every
part and every decompressed member still verified against the same frozen index.
"""
import concurrent.futures,hashlib,json,os,subprocess,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1299_paired_mechanism_study';D=R/'records/v1281_backup_20261118';GH=R/'tools/phase_storage_20261107/vendor/gh'
NAMES={'EW_ONWARD_INPUT.json','EW_ONWARD_SELECTION.json','EW_ONWARD_TABLE.npz','EW_ONWARD_REFERENCE.npz'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


def restore(slot,index,inventory):
    start=time.monotonic();group=next(g for g in index['archives']if g['group']==f'v1281-main_slot{slot:02}')
    folder=O/f'readback_slot{slot:02}';folder.mkdir(exist_ok=False);out=O/f'input_resume_slot{slot:02}';out.mkdir(exist_ok=False);proof=dict(passed=False,slot=slot,models=0)
    try:
        combined=folder/'combined.tar.zst'
        with combined.open('xb')as destination:
            for part in group['parts']:
                partfile=folder/part['name']
                with partfile.open('xb')as f:
                    p=subprocess.run([str(GH),'release','download',index['release_tag'],'--repo','frank8763/phase-','--pattern',part['name'],'--output','-'],cwd=R,stdout=f,stderr=subprocess.PIPE,timeout=120)
                assert p.returncode==0,'CLI_DOWNLOAD_FAILED '+p.stderr.decode(errors='replace')[-300:]
                assert partfile.stat().st_size==part['bytes']and sha(partfile)==part['sha256'],'PART_SHA'
                with partfile.open('rb')as f:
                    for b in iter(lambda:f.read(1048576),b''):destination.write(b)
                partfile.unlink()
        assert combined.stat().st_size==group['archive_bytes']and sha(combined)==group['archive_sha256'],'COMPLETE_ARCHIVE_SHA'
        process=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE);seen=set();retained=[]
        try:
            with tarfile.open(fileobj=process.stdout,mode='r|')as tar:
                for member in tar:
                    assert member.isfile()and member.name in inventory and member.name not in seen
                    original=inventory[member.name];h=hashlib.sha256();stream=tar.extractfile(member);name=Path(member.name).name
                    selected=member.name.startswith(f'runs/v858_nav2_verified/v1281/main_slot{slot:02}/')and name in NAMES
                    target=out/name;f=target.open('xb')if selected else None
                    try:
                        for b in iter(lambda:stream.read(1048576),b''):
                            h.update(b)
                            if f:f.write(b)
                    finally:
                        if f:f.close()
                    assert h.hexdigest()==original['sha256']and member.size==original['bytes'],'MEMBER_SHA'
                    if selected:retained.append(dict(upstream_path=member.name,local_path=str(target.relative_to(R)),bytes=original['bytes'],sha256=original['sha256']))
                    seen.add(member.name)
            assert process.wait(timeout=10)==0 and len(seen)==group['source_files']and len(retained)==4
        finally:
            if process.poll()is None:process.kill();process.wait()
        proof.update(passed=True,verified_upstream_members=len(seen),retained=retained,all_compressed_parts_and_members_SHA_verified=True)
        combined.unlink()
    except BaseException as exc:proof['error']=repr(exc)
    proof['wall_s']=time.monotonic()-start;dump(out/'RESTORED.json',proof);print(json.dumps({k:proof.get(k)for k in ['slot','passed','error','wall_s']}),flush=True);return proof


def main():
    claim=O/'RESTORE_FALLBACK_CLAIM.json';assert not claim.exists();dump(claim,dict(slots=[18,19,20,21,23],reason='original public urllib streams incomplete; original files not overwritten',models=0,started_unix=time.time()))
    index=json.loads((D/'RECORD_INDEX.json').read_text());inventory={x['path']:x for x in json.loads((D/'SOURCE_INVENTORY.json').read_text())['files']};results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        futures=[pool.submit(restore,slot,index,inventory)for slot in[18,19,20,21,23]]
        for f in futures:results.append(f.result())
    dump(O/'RESTORE_FALLBACK_COMPLETE.json',dict(passed=all(r['passed']for r in results),results=results,models=0,physical_native=0))


if __name__=='__main__':main()
