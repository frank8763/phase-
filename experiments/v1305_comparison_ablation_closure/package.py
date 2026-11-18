"""Selected full physical evidence and compact saved-state inputs, 4MiB parts."""
import fcntl,hashlib,json,os,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;D=R/'records/v1300_study_backup_20261118'
TAG='phase-static-pilot-and-time-ablation-20261118';PART=4*1024**2


def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(archive,items):
    wanted={x['path']:x for x in items};seen=set()
    with tarfile.open(archive,'r:gz')as tar:
        for member in tar:
            assert member.name in wanted and member.name not in seen
            x=wanted[member.name]
            if x.get('kind')=='symlink':assert member.issym()and member.linkname==x['target']
            else:
                assert member.isfile()and member.size==x['bytes'];s=tar.extractfile(member);h=hashlib.sha256()
                for b in iter(lambda:s.read(1048576),b''):h.update(b)
                assert h.hexdigest()==x['sha256']
            seen.add(member.name)
    assert seen==set(wanted);return len(seen)


def main():
    assert not(D/'RECORD_INDEX.json').exists(),'ONE_PACKAGE'
    assert read(R/'runs/v1300_static_tracking_comparison/COMPLETION.json')['closed']
    assert read(R/'runs/v1299_paired_mechanism_study/COMPLETION.json')['passed']and read(O/'FINAL_TIME_AUDIT.json')['passed']
    assert(R/'REVIEW_PENDING').exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    O.mkdir(exist_ok=True);D.mkdir(exist_ok=True);groups=[];excluded=[]
    def collect(paths):
        items=[]
        for p in paths:
            if p.is_symlink():
                target=str(p.readlink());assert p.name=='meshes_fixed'and target=='/home/linghu/catkin_ws/src/mk-mini/training/assets/mkmini_real/meshes_fixed'
                items.append(dict(path=str(p.relative_to(R)),kind='symlink',target=target,bytes=len(target.encode()),sha256=hashlib.sha256(target.encode()).hexdigest()));continue
            if not p.is_file():continue
            if 'cache'in p.parts:
                excluded.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),reason='reconstructible Mesa cache'));continue
            items.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
        return items
    for task in ['rpp_main','rpp_repeat','mppi_main']:
        root=R/'runs/v858_nav2_verified/v1300'/task;groups.append(dict(group=task,items=collect(sorted(root.rglob('*')))))
    P=R/'runs/v1299_paired_mechanism_study';inputs=[]
    for slot in range(17,25):
        folder=P/f'input_slot{slot:02}'if slot in[17,22,24]else P/f'input_chunks_slot{slot:02}'
        proof=read(folder/'RESTORED.json');assert proof['passed']
        for x in proof['retained']:
            p=R/x['local_path'];assert sha(p)==x['sha256'];inputs.append(p)
        inputs.append(folder/'RESTORED.json')
    groups.append(dict(group='compact_ablation_inputs',items=collect(inputs)))
    output=O/'transport';output.mkdir();index=[];inventory=[]
    for group in groups:
        folder=output/group['group'];folder.mkdir();archive=folder/(group['group']+'.tar.gz')
        with tarfile.open(archive,'w:gz',compresslevel=6,dereference=False)as tar:
            for x in group['items']:tar.add(R/x['path'],arcname=x['path'],recursive=False)
        n=verify(archive,group['items']);parts=[]
        with archive.open('rb')as stream:
            i=0
            while True:
                data=stream.read(PART)
                if not data:break
                part=folder/(archive.name+f'.part{i:03}');part.write_bytes(data);parts.append(dict(name=part.name,bytes=len(data),sha256=sha(part)));i+=1
        entry=dict(group=group['group'],archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),source_files=n,raw_bytes=sum(x['bytes']for x in group['items']),parts=parts)
        index.append(entry);inventory.extend(dict(x,group=group['group'])for x in group['items']);print(json.dumps(dict(packaged=group['group'],files=n,compressed_bytes=entry['archive_bytes'],parts=len(parts))),flush=True)
    dump(D/'SOURCE_INVENTORY.json',dict(files=inventory,excluded_caches=excluded))
    dump(D/'RECORD_INDEX.json',dict(release_tag=TAG,release_url=f'https://github.com/frank8763/phase-/releases/tag/{TAG}',archives=index,source_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),max_transport_part_bytes=PART,models=0))


if __name__=='__main__':main()
