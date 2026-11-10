"""Zero-model cleanup continuation: preserve link metadata, never follow targets.

The original immutable archive and cleanup assertion are not overwritten.
No Git push or physics API exists in this maintenance continuation.
"""
import fcntl,hashlib,importlib.util,json,os,shutil,time
from pathlib import Path

R=Path(__file__).resolve().parents[2];O=R/'runs/v994_diagnostic_timing_postmortem';REC=R/'records/nav2_v993_20261110'
spec=importlib.util.spec_from_file_location('v994_immutable_delivery_helpers',R/'experiments/v994_diagnostic_timing_postmortem/deliver.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')

def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert read(REC/'REMOTE_VERIFIED.json')['all_asset_and_decompressed_member_sha_verified']
    assert read(REC/'GIT_SYNC_RESULT.json')['remote_head_verified']
    assert d.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    with(O/'CLEANUP_CONTINUATION_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,no_second_push=True),f)
    links=[];physical=R/'runs/v858_nav2_verified/v993'
    for current,dirs,files in os.walk(physical,followlinks=False):
        for name in dirs+files:
            p=Path(current)/name
            if p.is_symlink():links.append(dict(path=str(p.relative_to(R)),link=os.readlink(p),target_not_accessed=True))
    assert len(links)==2
    for row in links:
        assert row['path'].endswith('/physics/paired/assets/meshes_fixed')
        assert row['link']=='/home/linghu/catkin_ws/src/mk-mini/training/assets/mkmini_real/meshes_fixed'
    dump(REC/'SYMLINKS_MANIFEST.json',dict(links=links,models=0,source='readlink of known task outputs only',
        target_accessed=False,original_archive_not_overwritten=True,zero_model_cleanup_error_preserved=True))
    (REC/'ORIGINAL_CLEANUP_ERROR.json').write_bytes((O/'PUBLISH_DELIVERY_ERROR.json').read_bytes())
    back=O/'cleanup_receipt_readback';back.mkdir(exist_ok=False)
    def receipt(p):
        d.gh(['release','upload',d.TAG,str(p)])
        d.gh(['release','download',d.TAG,'--pattern',p.name,'--dir',str(back)])
        assert d.sha(p)==d.sha(back/p.name)
    for p in [REC/'SYMLINKS_MANIFEST.json',REC/'ORIGINAL_CLEANUP_ERROR.json',Path(__file__).resolve()]:receipt(p)
    index=read(REC/'RECORD_INDEX.json');group=index['archives'][0]['group']
    catalog={x['path']:x for x in read(O/'readback'/(group+'.INVENTORY.json'))['files']}
    excluded={x['path']:x for x in read(REC/'EXCLUDED_REBUILDABLE_FILES.json')['files']}
    removed=[]
    for root in [physical,R/'runs/v993_steering_transient_diagnosis/prior_v974']:
        assert root.is_relative_to(R/'runs')and not root.is_symlink()
        size=0
        for p in d.t.packer(O/'cloud')['walk'](root):
            rel=str(p.relative_to(R));row=catalog.get(rel,excluded.get(rel));assert row is not None,rel
            assert d.sha(p)==row['sha256']and p.stat().st_size==row['bytes'],rel;size+=p.stat().st_size
        for row in links:
            p=R/row['path']
            if p.is_relative_to(root):
                assert p.is_symlink()and os.readlink(p)==row['link'];p.unlink()
        assert not any(p.is_symlink()for p in root.rglob('*'))
        shutil.rmtree(root);removed.append(dict(path=str(root.relative_to(R)),bytes=size))
    for root in [O/'cloud',O/'readback',O/'receipt_readback']:
        assert root.is_relative_to(R/'runs')and not root.is_symlink()
        size=sum(p.stat().st_size for p in d.t.packer(O/'cloud')['walk'](root));shutil.rmtree(root)
        removed.append(dict(path=str(root.relative_to(R)),bytes=size))
    d.verified_sources()
    dump(REC/'CLEANUP_RESULT.json',dict(deleted=removed,deleted_bytes=sum(x['bytes']for x in removed),models=0,
        remote_member_sha_verified_before_cleanup=True,symlink_metadata_remote_verified=True,
        link_targets_accessed=False,original_cleanup_failure_preserved=True,no_second_push=True))
    receipt(REC/'CLEANUP_RESULT.json')
    dump(REC/'FINALIZED.json',dict(closed=True,scientific_status='NOT_PASSED_TIMING_INTERRUPTION',
        source_commit=read(REC/'GIT_SYNC_RESULT.json')['commit'],release_url=index['release_url'],
        archive_and_member_sha_remote_verified=True,symlink_metadata_remote_verified=True,
        raw_cache_cleaned=True,models_authorized=False,cleanup_original_error_preserved=True,no_second_push=True))
    receipt(REC/'FINALIZED.json');shutil.rmtree(back)
    print(json.dumps(dict(finalized=True,deleted_bytes=sum(x['bytes']for x in removed),models=0,no_second_push=True)),flush=True)

if __name__=='__main__':main()
