"""Select only closed V951 case3 from its verified Release, without model imports."""
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v952_stopped_steering_alignment'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh'
PREFIX=Path('runs/v858_nav2_verified/v950/response_03')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(exist_ok=True);index=json.loads((ROOT/'records/nav2_v948_v951_20261109/RECORD_INDEX.json').read_text())
    restored=[]
    with tempfile.TemporaryDirectory(dir=OUT)as temporary:
        folder=Path(temporary)
        for record in index['archives']:
            names=[record['group']+'.INVENTORY.json',*[p['name']for p in record['parts']]]
            command=[str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--dir',str(folder)]
            for name in names:command+=['--pattern',name]
            subprocess.run(command,cwd=ROOT,check=True,timeout=120)
            inventory=json.loads((folder/names[0]).read_text());catalog={r['path']:r for r in inventory['files']}
            combined=folder/'combined.tar.zst';whole=hashlib.sha256()
            with combined.open('xb')as target:
                for part in record['parts']:
                    path=folder/part['name'];assert path.stat().st_size==part['bytes']and sha(path)==part['sha256']
                    with path.open('rb')as stream:
                        for block in iter(lambda:stream.read(1048576),b''):whole.update(block);target.write(block)
            assert whole.hexdigest()==record['archive_sha256']
            decoder=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE)
            with tarfile.open(fileobj=decoder.stdout,mode='r|')as archive:
                for member in archive:
                    path=Path(member.name)
                    if not path.is_relative_to(PREFIX):continue
                    assert member.isfile()and '..'not in path.parts and not path.is_absolute()
                    target=ROOT/path;expected=catalog[member.name]
                    if target.exists():assert not target.is_symlink()and sha(target)==expected['sha256']
                    else:
                        target.parent.mkdir(parents=True,exist_ok=True)
                        with archive.extractfile(member)as source,target.open('xb')as output:shutil.copyfileobj(source,output,1048576)
                    assert target.stat().st_size==expected['bytes']and sha(target)==expected['sha256']
                    restored.append(dict(path=str(path),bytes=expected['bytes'],sha256=expected['sha256']))
            assert decoder.wait()==0
    result=dict(passed=True,release_url=index['release_url'],restored=restored,models=0,integrations=0)
    (OUT/'RESTORE_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(files=len(restored),bytes=sum(r['bytes']for r in restored),models=0)))


if __name__=='__main__':main()
