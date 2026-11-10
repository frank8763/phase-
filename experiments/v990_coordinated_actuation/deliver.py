"""Source-only batch: one push, incremental Release, readback, scoped cleanup."""
import fcntl
import importlib.util
import json
import shutil
import time
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
O=R/'runs/v990_coordinated_actuation';REC=R/'records/nav2_v990_20261110'
spec=importlib.util.spec_from_file_location('v990_storage',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
TAG='phase-rpccr-coordinated-actuation-v990-20261110';GROUP='v990-coordinated-control-source-qualification'
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_COORDINATED_ACTUATION_V990_REPORT.md',
       'experiments/v990_coordinated_actuation','records/nav2_v990_20261110']


def gh(args):return t.run([str(t.GH),*args,'--repo',t.REPO],30)


def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert t.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    final=json.loads((REC/'FINAL_ZERO_MODEL_AUDIT.json').read_text())
    assert final['passed']and not final['physical_ready']and not final['models_authorized']
    for name,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items():assert t.sha(R/name)==h,name
    assert not(O/'ROUND_WINDOW.json').exists()
    assert not t.run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    with(O/'DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,one_git_push=True),f)
    cloud=O/'cloud';cloud.mkdir();pack=t.packer(cloud)
    files=list(pack['walk'](C))+list(pack['walk'](REC))+[R/n for n in STAGE[:3]]
    files+=[O/n for n in ['RESTORE_RECEIPT.json','BASELINE_RED.json','CONTROL_QUALIFICATION.json','BINDING_QUALIFICATION.json','DELIVERY_CLAIM.json']]
    files+=list(pack['walk'](O/'binding_qualified'))
    assert sum(p.stat().st_size for p in files)<2*1024**3
    group=pack['archive'](GROUP,files)
    index=dict(repository=t.REPO,release_tag=TAG,release_url=f'https://github.com/{t.REPO}/releases/tag/{TAG}',models=0,integrations=0,
        physical_ready=False,models_authorized=False,original_physics_not_duplicated=True,
        archives=[{k:v for k,v in group.items()if k!='files'}])
    t.dump(REC/'RECORD_INDEX.json',index)
    t.run(['git','add','--',*STAGE]);t.run(['git','diff','--cached','--check'])
    for name in t.run(['git','diff','--cached','--name-only']).splitlines():assert(R/name).lstat().st_size<90*1024**2
    # All sources and exact staged paths are reviewed before this script is run.
    t.run(['git','commit','-m','Coordinate steering and rear velocity allocation with independent saved-input qualifications'])
    commit=t.run(['git','rev-parse','HEAD']).strip()
    sync=dict(commit=commit,one_attempt=True,push_limit_s=30,remote_head_limit_s=5)
    with(REC/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    try:t.run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as e:sync['push_error']=repr(e)
    try:
        sync['remote_head']=t.run(['git','ls-remote','origin','refs/heads/main'],5).split()[0]
        sync['remote_head_verified']=sync['remote_head']==commit
    except Exception as e:sync['verify_error']=repr(e)
    t.dump(REC/'GIT_SYNC_RESULT.json',sync)
    # An immutable Release can retain the new source even if branch sync is
    # unknown; never retry the Git push. The archive itself contains the source.
    known=json.loads((R/'records/nav2_v987_20261110/GIT_SYNC_RESULT.json').read_text())
    assert known['remote_head_verified']
    target=commit if sync.get('remote_head_verified')else known['commit']
    gh(['release','create',TAG,'--target',target,'--title','Coordinated actuation: source and control-map qualification only',
        '--notes','Zero new physical models/integrations. Shared virtual curvature, joint motor slew feasibility and steering-hold coordinated braking. Saved-input/constructor/dispatch evidence only; physical engine and actual tracking remain unqualified. Original failures retained. Source included in archive.','--draft'])
    assets=list(cloud.iterdir())+[REC/'RECORD_INDEX.json',REC/'GIT_SYNC_RESULT.json']
    gh(['release','upload',TAG,*map(str,assets)])
    back=O/'readback';back.mkdir()
    for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert t.sha(p)==t.sha(back/p.name)
    t.verifier()(back,index);gh(['release','edit',TAG,'--draft=false'])
    verified=REC/'REMOTE_VERIFIED.json';t.dump(verified,dict(passed=True,models=0,all_asset_and_member_sha_verified=True,
        source_in_release=True,physical_ready=False,models_authorized=False,source_commit=commit,release_url=index['release_url']))
    gh(['release','upload',TAG,str(verified)]);gh(['release','download',TAG,'--pattern',verified.name,'--dir',str(back)])
    assert t.sha(verified)==t.sha(back/verified.name)
    for row in json.loads((O/'RESTORE_RECEIPT.json').read_text())['files']:assert t.sha(R/row['path'])==row['sha256']
    assert O.resolve().is_relative_to(R/'runs')and not O.is_symlink()
    for p in O.rglob('*'):assert not p.is_symlink()and p.resolve().is_relative_to(O)
    manifest=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=t.sha(p))for p in pack['walk'](O)]
    removed=sum(p['bytes']for p in manifest)
    for row in manifest:assert t.sha(R/row['path'])==row['sha256']
    shutil.rmtree(O)
    cleanup=REC/'CLEANUP.json';t.dump(cleanup,dict(models=0,deleted_cache_bytes=removed,files=manifest,
        restored_old_raw_still_in_original_verified_releases=True,new_required_evidence_in_verified_v990_release=True))
    receipts=R/'runs/v990_receipt_readback';receipts.mkdir()
    def receipt(p):
        gh(['release','upload',TAG,str(p)]);gh(['release','download',TAG,'--pattern',p.name,'--dir',str(receipts)]);assert t.sha(p)==t.sha(receipts/p.name)
    receipt(cleanup)
    finalized=REC/'FINALIZED.json';t.dump(finalized,dict(closed=True,status='SOURCE_AND_CONTROL_MAP_QUALIFIED_ONLY',models=0,integrations=0,
        remote_verified=True,raw_cache_cleaned=True,physical_ready=False,models_authorized=False,
        git_head_verified=bool(sync.get('remote_head_verified')),release_url=index['release_url']))
    receipt(finalized);shutil.rmtree(receipts)
    t.run(['git','add','--',str(REC.relative_to(R))]);t.run(['git','diff','--cached','--check'])
    t.run(['git','commit','-m','Record V990 source delivery readback and bounded cache cleanup; no second push'])
    print(json.dumps(dict(finalized=True,models=0,physical_ready=False,git_head_verified=bool(sync.get('remote_head_verified')),
        source_commit=commit,release_url=index['release_url'],deleted_cache_bytes=removed)),flush=True)


if __name__=='__main__':main()
