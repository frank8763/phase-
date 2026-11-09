"""Restore only requested V943/prerequisite run paths; verify archive/member SHA."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REC=ROOT/'records/nav2_v945_20261109'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('prefix');args=parser.parse_args()
    prefix=Path(args.prefix)
    assert not prefix.is_absolute() and '..' not in prefix.parts and prefix.parts[0]=='runs'
    index=json.loads((REC/'RECORD_INDEX.json').read_text())
    cache=ROOT/'runs/v945_restore_cache';cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        temp=Path(tmp)
        for group in index['archives']:
            folder=temp/group['group'];folder.mkdir()
            names=[group['group']+'.INVENTORY.json',*[p['name'] for p in group['parts']]]
            command=[str(GH),'release','download',index['release_tag'],'--repo',index['repository'],'--dir',str(folder)]
            for name in names:command+=['--pattern',name]
            subprocess.run(command,cwd=ROOT,check=True,timeout=180)
            inventory=json.loads((folder/names[0]).read_text());catalog={r['path']:r for r in inventory['files']}
            combined=folder/'archive.tar.zst';whole=hashlib.sha256()
            with combined.open('xb') as output:
                for part in group['parts']:
                    path=folder/part['name'];assert path.stat().st_size==part['bytes'] and sha(path)==part['sha256']
                    with path.open('rb') as stream:
                        for block in iter(lambda:stream.read(1048576),b''):whole.update(block);output.write(block)
            assert whole.hexdigest()==group['archive_sha256']
            process=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE)
            with tarfile.open(fileobj=process.stdout,mode='r|') as archive:
                for member in archive:
                    name=Path(member.name)
                    if not name.is_relative_to(prefix):continue
                    assert member.isfile() and not name.is_absolute() and '..' not in name.parts
                    target=ROOT/name;assert target.resolve().is_relative_to(ROOT/'runs')
                    expected=catalog[member.name]
                    if target.exists():
                        assert target.is_file() and not target.is_symlink() and sha(target)==expected['sha256']
                        continue
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with archive.extractfile(member) as source,target.open('xb') as output:shutil.copyfileobj(source,output,1048576)
                    assert target.stat().st_size==expected['bytes'] and sha(target)==expected['sha256']
            assert process.wait()==0
    cache.rmdir()


if __name__=='__main__':main()
