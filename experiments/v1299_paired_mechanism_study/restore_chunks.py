"""Bounded small HTTP ranges; resume identical bytes, then full SHA/member audit."""
import concurrent.futures,hashlib,json,os,subprocess,tarfile,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1299_paired_mechanism_study';D=R/'records/v1281_backup_20261118'
NAMES={'EW_ONWARD_INPUT.json','EW_ONWARD_SELECTION.json','EW_ONWARD_TABLE.npz','EW_ONWARD_REFERENCE.npz'}


def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    index=json.loads((D/'RECORD_INDEX.json').read_text());inventory={x['path']:x for x in json.loads((D/'SOURCE_INVENTORY.json').read_text())['files']}
    dest=O/'chunk_transport';dest.mkdir(exist_ok=False);started=time.monotonic();deadline=started+300;jobs=[];catalog=[]
    for slot in[18,19,20,21,23]:
        group=next(g for g in index['archives']if g['group']==f'v1281-main_slot{slot:02}')
        for part in group['parts']:
            candidates=[p for p in O.glob('*/'+part['name'])if p.is_file()and p.stat().st_size<=part['bytes']]
            old=max(candidates,key=lambda p:p.stat().st_size)if candidates else None
            prefix=old.stat().st_size if old else 0;prefixfile=dest/(part['name']+'.prefix')
            if old:prefixfile.write_bytes(old.read_bytes())
            offsets=list(range(prefix,part['bytes'],1024*1024));pieces=[]
            for first in offsets:
                last=min(part['bytes']-1,first+1024*1024-1);p=dest/(part['name']+f'.{first:09d}.chunk');job=dict(slot=slot,name=part['name'],first=first,last=last,total=part['bytes'],path=str(p));jobs.append(job);pieces.append(job)
            catalog.append(dict(slot=slot,part=part,prefix=prefix,prefixfile=str(prefixfile),pieces=pieces))
    dump(dest/'PLAN.json',dict(parts=catalog,requests=len(jobs),max_workers=8,models=0,software_total_s=300))
    base='https://github.com/frank8763/phase-/releases/download/'+index['release_tag']+'/'
    def get(job):
        assert time.monotonic()<deadline,'CHUNK_ROOT_DEADLINE'
        url=base+job['name']+f'?phase_range={job["first"]}-{job["last"]}'
        req=urllib.request.Request(url,headers={'Range':f'bytes={job["first"]}-{job["last"]}','User-Agent':'Phase-verified-evidence-small-ranges'})
        with urllib.request.urlopen(req,timeout=30)as src:
            expected=f'bytes {job["first"]}-{job["last"]}/{job["total"]}'
            assert src.status==206 and src.headers.get('Content-Range')==expected,'RANGE_IDENTITY '+str(src.headers.get('Content-Range'))
            data=src.read(job['last']-job['first']+2)
        assert len(data)==job['last']-job['first']+1,'RANGE_LENGTH'
        Path(job['path']).write_bytes(data);return dict(slot=job['slot'],name=job['name'],first=job['first'],bytes=len(data))
    pool=concurrent.futures.ThreadPoolExecutor(max_workers=8);futures=[pool.submit(get,j)for j in jobs];done=[];errors=[]
    try:
        for f in concurrent.futures.as_completed(futures,timeout=305):
            try:done.append(f.result())
            except BaseException as exc:errors.append(repr(exc))
            dump(dest/'PROGRESS.json',dict(completed=len(done),errors=len(errors),total=len(jobs),wall_s=time.monotonic()-started))
    except BaseException as exc:errors.append(repr(exc))
    if errors:
        dump(dest/'DOWNLOAD_ERRORS.json',dict(errors=errors,completed=len(done),total=len(jobs),wall_s=time.monotonic()-started));print(json.dumps(dict(passed=False,errors=errors[:3],complete=len(done),total=len(jobs))),flush=True)
        pool.shutdown(wait=False,cancel_futures=True);os._exit(1)
    pool.shutdown();parts={}
    for entry in catalog:
        p=dest/entry['part']['name']
        with p.open('xb')as stream:
            if entry['prefix']:stream.write(Path(entry['prefixfile']).read_bytes())
            for j in entry['pieces']:stream.write(Path(j['path']).read_bytes())
        assert p.stat().st_size==entry['part']['bytes']and sha(p)==entry['part']['sha256'],'FINAL_PART_SHA'
        parts[entry['part']['name']]=p
    results=[]
    for slot in[18,19,20,21,23]:
        group=next(g for g in index['archives']if g['group']==f'v1281-main_slot{slot:02}');combined=dest/f'slot{slot:02}.tar.zst'
        with combined.open('xb')as stream:
            for part in group['parts']:stream.write(parts[part['name']].read_bytes())
        assert sha(combined)==group['archive_sha256'],'WHOLE_GROUP_SHA'
        out=O/f'input_chunks_slot{slot:02}';out.mkdir();proc=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE);seen=set();retained=[]
        try:
            with tarfile.open(fileobj=proc.stdout,mode='r|')as tar:
                for member in tar:
                    assert member.isfile()and member.name in inventory and member.name not in seen
                    item=inventory[member.name];h=hashlib.sha256();source=tar.extractfile(member);name=Path(member.name).name;selected=member.name.startswith(f'runs/v858_nav2_verified/v1281/main_slot{slot:02}/')and name in NAMES;target=out/name;stream=target.open('xb')if selected else None
                    try:
                        for b in iter(lambda:source.read(1048576),b''):
                            h.update(b)
                            if stream:stream.write(b)
                    finally:
                        if stream:stream.close()
                    assert member.size==item['bytes']and h.hexdigest()==item['sha256'],'MEMBER_SHA'
                    if selected:retained.append(dict(upstream_path=member.name,local_path=str(target.relative_to(R)),bytes=item['bytes'],sha256=item['sha256']))
                    seen.add(member.name)
            assert proc.wait(timeout=10)==0 and len(seen)==group['source_files']and len(retained)==4
        finally:
            if proc.poll()is None:proc.kill();proc.wait()
        proof=dict(passed=True,slot=slot,retained=retained,verified_upstream_members=len(seen),transport_sha_verified=True,models=0);dump(out/'RESTORED.json',proof);results.append(proof);print(json.dumps(dict(slot=slot,passed=True)),flush=True)
    dump(O/'RESTORE_CHUNKS_COMPLETE.json',dict(passed=True,results=results,wall_s=time.monotonic()-started,models=0,physical_native=0))


if __name__=='__main__':main()
