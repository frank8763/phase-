"""Zero-model cleanup continuation after verified archive, preserving a mesh link.

The first cleanup refused a generated mesh-directory symlink. Record its link
metadata remotely, verify every regular file, then unlink only the local link;
the link target is never traversed, opened or deleted. No publication/push retry.
"""
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v944_rpccr_segment_postmortem'
OPS=ROOT/'runs/v943_rpccr_segment_navigation';REC=ROOT/'records/nav2_v943_20261109'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-'
TAG='phase-rpccr-recovery-v943-20261109'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def gh(args):
    subprocess.run([str(GH),*args,'--repo',REPO],cwd=ROOT,check=True,timeout=60,
                   stdout=subprocess.DEVNULL)


def main():
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(ROOT/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC/'REMOTE_VERIFIED.json').read_text())['passed']
    assert not(REC/'DELIVERY_RESULT.json').exists()
    with(OUT/'CLEANUP_CONTINUATION_CLAIM.json').open('x') as f:json.dump(dict(models=0,at=time.time()),f)
    originals={}
    for folder in [OPS/'cloud',OUT/'cloud']:
        for inventory in folder.glob('*.INVENTORY.json'):
            for row in json.loads(inventory.read_text())['files']:
                if row['type']=='file':originals[row['path']]=row['sha256']
    folders=[ROOT/'runs/v858_nav2_verified/v943',ROOT/'runs/v943_startup_fixture02',
             ROOT/'runs/v936_rpccr_corridor_search/saved']
    links=[]
    for folder in folders:
        for current,dirs,files in os.walk(folder,followlinks=False):
            for name in dirs+files:
                path=Path(current)/name
                if path.is_symlink():links.append(dict(path=str(path.relative_to(ROOT)),target=os.readlink(path)))
    assert len(links)==1 and links[0]['path']=='runs/v858_nav2_verified/v943/main_we/physics/paired/assets/meshes_fixed'
    metadata=dict(models=0,integrations=0,original_cleanup_block_preserved=True,
                  links=links,target_accessed=False,target_deleted=False,
                  justification='Generated pointer to existing frozen mesh dependencies; compiled scene_model.mjb and all regular evidence already remotely verified.')
    (REC/'CLEANUP_LINK_METADATA.json').write_text(json.dumps(metadata,indent=2)+'\n')
    receipts=OUT/'cleanup_receipt_readback';receipts.mkdir(exist_ok=False)
    for path in [REC/'CLEANUP_LINK_METADATA.json',Path(__file__)]:
        gh(['release','upload',TAG,str(path)])
        gh(['release','download',TAG,'--pattern',path.name,'--dir',str(receipts)])
        assert sha(path)==sha(receipts/path.name)
    deleted=0;cleaned=[]
    for folder in folders:
        assert folder.resolve().is_relative_to(ROOT/'runs') and not folder.is_symlink()
        for current,dirs,files in os.walk(folder,followlinks=False):
            dirs[:]=[name for name in dirs if not(Path(current)/name).is_symlink()]
            for name in files:
                path=Path(current)/name
                assert not path.is_symlink()
                assert originals.get(str(path.relative_to(ROOT)))==sha(path),'UNVERIFIED_REQUIRED_RAW'
                deleted+=path.stat().st_size
        for item in links:
            path=ROOT/item['path']
            if path.is_relative_to(folder):
                assert path.is_symlink() and os.readlink(path)==item['target'];path.unlink()
        shutil.rmtree(folder);cleaned.append(str(folder.relative_to(ROOT)))
    prior=ROOT/'runs/v936_rpccr_corridor_search'
    assert json.loads((prior/'RESTORE_VERIFIED.json').read_text())['passed']
    for folder in [prior/'download',OPS/'cloud',OUT/'cloud',OUT/'download']:
        assert folder.resolve().is_relative_to(ROOT/'runs') and not folder.is_symlink()
        assert not any(p.is_symlink() for p in folder.rglob('*'))
        deleted+=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())
        shutil.rmtree(folder);cleaned.append(str(folder.relative_to(ROOT)))
    result=dict(status='REMOTE_VERIFIED_REQUIRED_RAW_AND_DUPLICATE_CACHE_CLEANED',
                deleted_bytes=deleted,cleaned_paths=cleaned,models=0,
                shared_link_unlinked_target_untouched=True,metadata_and_qualifications_retained=True,
                release_url=f'https://github.com/{REPO}/releases/tag/{TAG}')
    (REC/'DELIVERY_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    gh(['release','upload',TAG,str(REC/'DELIVERY_RESULT.json')])
    gh(['release','download',TAG,'--pattern','DELIVERY_RESULT.json','--dir',str(receipts)])
    assert sha(REC/'DELIVERY_RESULT.json')==sha(receipts/'DELIVERY_RESULT.json')
    shutil.rmtree(receipts)
    if(OUT/'receipt_readback').exists():shutil.rmtree(OUT/'receipt_readback')
    subprocess.run(['git','add','--',str(REC.relative_to(ROOT)),str(Path(__file__).relative_to(ROOT))],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m','Record verified V943 remote evidence and link-safe cleanup'],cwd=ROOT,check=True,
                   stdout=subprocess.DEVNULL)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
