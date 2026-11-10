"""Restore only four completed response arrays/inputs after asset/member SHA."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1002_causal_response_predictor';GH=R/'tools/phase_storage_20261107/vendor/gh'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
    index=json.loads((R/'records/nav2_v995_20261110/RECORD_INDEX.json').read_text());group=index['archives'][0];fetch=O/'download';fetch.mkdir(exist_ok=False)
    def download(name):
        x=subprocess.run([str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--pattern',name,'--dir',str(fetch)],capture_output=True,text=True,timeout=30)
        assert x.returncode==0,x.stderr[-1000:]
    download(group['group']+'.INVENTORY.json');catalog={x['path']:x for x in json.loads((fetch/(group['group']+'.INVENTORY.json')).read_text())['files']}
    archive=fetch/'combined.tar.zst';digest=hashlib.sha256()
    with archive.open('xb')as out:
        for part in group['parts']:
            download(part['name']);p=fetch/part['name'];assert p.stat().st_size==part['bytes']and sha(p)==part['sha256']
            with p.open('rb')as stream:
                for block in iter(lambda:stream.read(1048576),b''):digest.update(block);out.write(block)
    assert digest.hexdigest()==group['archive_sha256']
    tasks=json.loads((R/'experiments/v995_sim_time_response/TASKS.json').read_text());wanted={}
    for task in tasks:
        prefix='runs/v858_nav2_verified/v995/'+task['name']+'/'
        for suffix in ['RESULT.json','physics/NATIVE_TRACE.npz','physics/SETUP.json','physics/ALLOCATION.json.gz','physics/BODY_COMMANDS.json']:
            wanted[prefix+suffix]=O/'responses'/task['name']/suffix
    proc=subprocess.Popen(['zstd','-q','-dc',str(archive)],stdout=subprocess.PIPE);rows=[]
    with tarfile.open(fileobj=proc.stdout,mode='r|')as stream:
        for member in stream:
            if member.name not in wanted:continue
            assert member.isfile();p=wanted[member.name];p.parent.mkdir(parents=True,exist_ok=True)
            with stream.extractfile(member)as source,p.open('xb')as target:shutil.copyfileobj(source,target)
            row=catalog[member.name];assert sha(p)==row['sha256']and p.stat().st_size==row['bytes']
            rows.append(dict(original=member.name,path=str(p.relative_to(R)),sha256=row['sha256'],bytes=row['bytes']))
    assert proc.wait(timeout=30)==0 and len(rows)==20
    (O/'RESTORE_RECEIPT.json').write_text(json.dumps(dict(passed=True,models=0,integrations=0,files=rows),indent=2)+'\n');shutil.rmtree(fetch)
    print(json.dumps(dict(restored_files=len(rows),bytes=sum(x['bytes']for x in rows),models=0)))
