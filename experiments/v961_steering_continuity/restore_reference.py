"""Select only V959case6 actual response inputs from the verified prior Release."""
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v961_steering_continuity'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh'
PREFIX='runs/v858_nav2_verified/v959/response_06/'
WANTED={'BODY_AND_STEERING.npz','physics/SETUP.json','physics/NATIVE_TRACE.npz','physics/INITIAL_STATE.npz','physics/REPLAY.json','physics/BODY_COMMANDS.json'}


def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def main():
    index=json.loads((ROOT/'records/nav2_v955_v960_20261109/RECORD_INDEX.json').read_text());restored=[]
    with tempfile.TemporaryDirectory(dir=OUT)as temporary:
        folder=Path(temporary)
        for group in index['archives']:
            args=[str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--dir',str(folder)]
            for name in [group['group']+'.INVENTORY.json',*[p['name']for p in group['parts']]]:args+=['--pattern',name]
            subprocess.run(args,cwd=ROOT,check=True,timeout=120)
            inventory=json.loads((folder/(group['group']+'.INVENTORY.json')).read_text());catalog={r['path']:r for r in inventory['files']}
            combined=folder/'combined.tar.zst';whole=hashlib.sha256()
            with combined.open('xb')as target:
                for part in group['parts']:
                    p=folder/part['name'];assert p.stat().st_size==part['bytes']and sha(p)==part['sha256']
                    with p.open('rb')as f:
                        for block in iter(lambda:f.read(1048576),b''):whole.update(block);target.write(block)
            assert whole.hexdigest()==group['archive_sha256']
            decoder=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE)
            with tarfile.open(fileobj=decoder.stdout,mode='r|')as archive:
                for member in archive:
                    if not member.name.startswith(PREFIX)or member.name[len(PREFIX):]not in WANTED:continue
                    path=Path(member.name);assert member.isfile()and not path.is_absolute()and '..'not in path.parts
                    target=ROOT/path;expected=catalog[member.name];target.parent.mkdir(parents=True,exist_ok=True)
                    if not target.exists():
                        with archive.extractfile(member)as source,target.open('xb')as out:shutil.copyfileobj(source,out,1048576)
                    assert not target.is_symlink()and sha(target)==expected['sha256']
                    restored.append(dict(path=member.name,sha256=expected['sha256'],bytes=expected['bytes']))
            assert decoder.wait()==0
    assert len(restored)==len(WANTED)
    (OUT/'RESTORE_RECEIPT.json').write_text(json.dumps(dict(passed=True,restored=restored,release_url=index['release_url'],models=0,integrations=0),indent=2)+'\n')
    print(json.dumps(dict(files=len(restored),bytes=sum(r['bytes']for r in restored),models=0)))


if __name__=='__main__':main()
