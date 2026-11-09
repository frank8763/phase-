"""Restore only this closed batch's raw evidence; never starts a model."""
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
INDEX=ROOT/'records/nav2_v955_v960_20261109/RECORD_INDEX.json'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh'
PREFIXES=['runs/v955_damped_stopped_alignment/','runs/v956_damped_response18/','runs/v957_response18_closure/','runs/v958_hold_steering_contract/','runs/v959_hold_response18/','runs/v960_hold_response_closure/','runs/v858_nav2_verified/v956/','runs/v858_nav2_verified/v959/']


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def main():
    index=json.loads(INDEX.read_text());cache=ROOT/'runs/v960_restore_cache';cache.mkdir(exist_ok=True)
    restored=[]
    with tempfile.TemporaryDirectory(dir=cache)as temporary:
        folder=Path(temporary)
        for group in index['archives']:
            cmd=[str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--dir',str(folder)]
            for name in [group['group']+'.INVENTORY.json',*[r['name']for r in group['parts']]]:cmd+=['--pattern',name]
            subprocess.run(cmd,cwd=ROOT,check=True,timeout=120)
            inventory=json.loads((folder/(group['group']+'.INVENTORY.json')).read_text())
            catalog={r['path']:r for r in inventory['files']};whole=hashlib.sha256();combined=folder/'combined.tar.zst'
            with combined.open('xb')as target:
                for part in group['parts']:
                    path=folder/part['name'];assert path.stat().st_size==part['bytes']and sha(path)==part['sha256']
                    with path.open('rb')as source:
                        for block in iter(lambda:source.read(1048576),b''):whole.update(block);target.write(block)
            assert whole.hexdigest()==group['archive_sha256']
            decoder=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE)
            with tarfile.open(fileobj=decoder.stdout,mode='r|')as archive:
                for member in archive:
                    if not any(member.name.startswith(prefix)for prefix in PREFIXES):continue
                    path=Path(member.name);assert member.isfile()and not path.is_absolute()and '..'not in path.parts
                    target=ROOT/path;assert target.resolve().is_relative_to(ROOT/'runs')
                    expected=catalog[member.name]
                    if not target.exists():
                        target.parent.mkdir(parents=True,exist_ok=True)
                        with archive.extractfile(member)as source,target.open('xb')as out:shutil.copyfileobj(source,out,1048576)
                    assert not target.is_symlink()and sha(target)==expected['sha256']
                    restored.append(dict(path=str(path),sha256=expected['sha256'],bytes=expected['bytes']))
            assert decoder.wait()==0;combined.unlink()
    (cache/'RESTORE_RECEIPT.json').write_text(json.dumps(dict(restored=restored,models=0,integrations=0),indent=2)+'\n')
    print(json.dumps(dict(files=len(restored),bytes=sum(r['bytes']for r in restored),models=0)))


if __name__=='__main__':main()
