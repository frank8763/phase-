"""Restore a selected closed task after every downloaded archive/member SHA."""
import argparse
import subprocess
from package import *


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--list',action='store_true')
    parser.add_argument('--task',choices=['rpp_main']); parser.add_argument('--destination')
    parser.add_argument('--from-readback',action='store_true'); args=parser.parse_args()
    index=read(D/'RECORD_INDEX.json')
    if args.list:
        print(json.dumps(dict(tasks=['rpp_main'],release=index['release_url']))); return
    assert args.task
    base=R
    if args.destination:
        base=Path(args.destination).absolute(); assert '..' not in base.parts and base.is_relative_to(R/'runs') and base!=R/'runs'
        assert not base.exists() and not base.is_symlink() and not any(p.is_symlink() for p in base.parents)
    items=read(D/'SOURCE_INVENTORY.json')['files']; prefix='runs/v858_nav2_verified/v1337/'+args.task+'/'
    selected=[x for x in items if x['path'].startswith(prefix) and x.get('kind')!='symlink']
    assert len(selected)>=15,'EMPTY_TASK_NOT_RESTORABLE'
    for item in selected:
        p=Path(item['path']); assert not p.is_absolute() and '..' not in p.parts
        path=base/p; assert path.is_relative_to(R/'runs') and not any(p.is_symlink() for p in path.parents)
        assert not path.exists() and not path.is_symlink(),'EXISTING_OUTPUT_NOT_OVERWRITTEN'
    folder=O/('restore_'+args.task); folder.mkdir(exist_ok=False)
    parts=O/'readback' if args.from_readback else folder
    if args.from_readback: assert read(D/'FULL_REMOTE_VERIFIED.json')['passed']
    for item in index['parts']:
        path=parts/item['name']
        if not args.from_readback:
            with path.open('xb') as stream:
                run=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'release','download',index['release_tag'],'--repo','frank8763/phase-','--pattern',item['name'],'--output','-'],cwd=R,stdout=stream,stderr=subprocess.PIPE,timeout=60)
            assert run.returncode==0,'DOWNLOAD_FAILED'
        assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256']
    archive=folder/index['archive_name']
    with archive.open('xb') as stream:
        for item in index['parts']: stream.write((parts/item['name']).read_bytes())
    assert sha(archive)==index['archive_sha256']; verify(archive,items)
    wanted={x['path'] for x in selected}
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar:
            if member.name not in wanted: continue
            assert member.isfile(); path=base/member.name; path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:
                source=tar.extractfile(member)
                for chunk in iter(lambda:source.read(1048576),b''): stream.write(chunk)
    for item in selected: assert sha(base/item['path'])==item['sha256']
    archive.unlink()
    if not args.from_readback:
        for item in index['parts']: (parts/item['name']).unlink()
    proof=dict(passed=True,task=args.task,restored_regular_files=len(selected),source_archive_members_verified=len(items),destination=str(base),historical_links_not_recreated=True,files=selected,models=0)
    dump(folder/'RESTORED.json',proof); print(json.dumps({k:v for k,v in proof.items() if k!='files'}))


if __name__=='__main__': main()
