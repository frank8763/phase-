"""One new source-only delivery; verified Release evidence and bounded Git sync."""
import fcntl
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

C=Path(__file__).parent
R=C.resolve().parents[1]
O=R/'runs/v981_tracking_evidence_closure'
RAW=R/'runs/v858_nav2_verified/v981_software'
REC=R/'records/nav2_v981_20261110'
TAG='phase-rpccr-tracking-evidence-v981-20261110'
spec=importlib.util.spec_from_file_location('v981_existing_transport',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_TRACKING_EVIDENCE_REPAIR_V981_REPORT.md',
       'experiments/v981_tracking_evidence_closure','records/nav2_v981_20261110']


def gh(args):
    return t.run([str(t.GH),*args,'--repo',t.REPO],30)


def verify_frozen():
    assert t.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    frozen=json.loads((C/'SOURCE_FREEZE.json').read_text())
    assert frozen['model_authority'] is False
    for name,digest in frozen['files'].items():
        assert t.sha(R/name)==digest,name


def prepare():
    assert not t.run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    final=json.loads((REC/'FINAL_ZERO_MODEL_AUDIT.json').read_text())
    assert final['passed']and final['models']==0 and final['models_authorized']is False
    with(O/'PREPARE_CLAIM.json').open('x')as stream:
        json.dump(dict(at=time.time(),models=0),stream)
    cloud=O/'cloud'
    cloud.mkdir()
    pack=t.packer(cloud)
    files=[p for p in pack['walk'](O)if cloud not in p.parents]
    files+=list(pack['walk'](RAW))+list(pack['walk'](C))+list(pack['walk'](REC))
    files+=[R/name for name in STAGE[:3]]
    selected=R/'runs/v980_recovery_actuation_postmortem'
    files+=[selected/name for name in ['COMPONENT_REFERENCE.json','ONLINE_TRACKING_FAULT.json','COMMAND_TUBES.json.gz','v979-fixed-recovery-physical-gate.INVENTORY.json']]
    assert all(not p.is_symlink()and p.resolve().is_relative_to(R)for p in files)
    assert sum(p.stat().st_size for p in set(files))<64*1024**2
    group=pack['archive']('v981-source-and-fault-injection-qualification',files)
    index=dict(repository=t.REPO,release_tag=TAG,release_url=f'https://github.com/{t.REPO}/releases/tag/{TAG}',
               status=final['status'],models=0,integrations=0,physical_ready=False,models_authorized=False,
               archives=[{k:v for k,v in group.items()if k!='files'}])
    t.dump(REC/'RECORD_INDEX.json',index)
    t.run(['git','add','--',*STAGE])
    t.run(['git','diff','--cached','--check'])
    for name in t.run(['git','diff','--cached','--name-only']).splitlines():
        assert (R/name).lstat().st_size<90*1024**2
    t.dump(O/'PREPARED.json',dict(prepared=True,models=0,source_and_member_sha_verified=True))
    print(json.dumps(dict(prepared=True,files=group['source_files'],archive_bytes=group['archive_bytes'])),flush=True)


def publish():
    assert(O/'PREPARED.json').exists()
    with(O/'PUBLISH_CLAIM.json').open('x')as stream:
        json.dump(dict(at=time.time(),models=0),stream)
    t.run(['git','diff','--cached','--check'])
    t.run(['git','commit','-m','Repair conservative recovery heading sampling and preserve native evidence on worker failure'])
    commit=t.run(['git','rev-parse','HEAD']).strip()
    sync=dict(commit=commit,one_attempt=True,push_limit_s=30,remote_head_read_limit_s=5)
    with(REC/'GIT_SYNC_CLAIM.json').open('x')as stream:
        json.dump(sync,stream)
    try:
        t.run(['git','push','origin','main'],30)
        sync['push_succeeded']=True
    except Exception as error:
        sync['push_error']=repr(error)
    try:
        sync['remote_head']=t.run(['git','ls-remote','origin','refs/heads/main'],5).split()[0]
        sync['remote_head_verified']=sync['remote_head']==commit
    except Exception as error:
        sync['verify_error']=repr(error)
    t.dump(REC/'GIT_SYNC_RESULT.json',sync)
    assert sync.get('remote_head_verified'),'SOURCE_REMOTE_UNKNOWN_KEEP_NECESSARY_RAW_NO_RETRY'
    index=json.loads((REC/'RECORD_INDEX.json').read_text())
    gh(['release','create',TAG,'--target',commit,'--title','Recovery heading precision and failure evidence closure: zero-model qualification',
        '--notes','Source-only repair. Two old failures reproduced; fixed saved-pose and owned-process/native-loop counter fixtures passed. No physical models or navigation. Actual steering transient and full dynamic acceptance remain unqualified.','--draft'])
    assets=[p for p in(O/'cloud').iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json']
    gh(['release','upload',TAG,*map(str,assets)])
    readback=O/'readback'
    readback.mkdir()
    for path in assets:
        gh(['release','download',TAG,'--pattern',path.name,'--dir',str(readback)])
        assert t.sha(path)==t.sha(readback/path.name)
    t.verifier()(readback,index)
    catalog={row['path']:row for row in json.loads((readback/'v981-source-and-fault-injection-qualification.INVENTORY.json').read_text())['files']}
    for path in list(t.packer(O/'cloud')['walk'](RAW)):
        row=catalog[str(path.relative_to(R))]
        assert t.sha(path)==row['sha256']and path.stat().st_size==row['bytes']
    gh(['release','edit',TAG,'--draft=false'])
    t.dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,source_commit=commit,all_assets_and_decompressed_member_sha_verified=True,
         release_url=index['release_url'],models=0,integrations=0,physical_ready=False))
    receipts=O/'receipt_readback'
    receipts.mkdir()
    def receipt(path):
        gh(['release','upload',TAG,str(path)])
        gh(['release','download',TAG,'--pattern',path.name,'--dir',str(receipts)])
        assert t.sha(path)==t.sha(receipts/path.name)
    for path in [REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:
        receipt(path)
    removed=[]
    # Every local raw fixture file must match the verified catalog before removal.
    for path in list(t.packer(O/'cloud')['walk'](O)):
        if any(folder in path.parents for folder in [O/'cloud',readback,receipts]):
            continue
        if path.name in {'PREPARED.json','PUBLISH_CLAIM.json'}:
            continue
        row=catalog.get(str(path.relative_to(R)))
        assert row is not None and row['sha256']==t.sha(path),'UNARCHIVED_RAW_FILE '+str(path)
    for folder in [RAW,O/'cloud',readback]:
        assert not folder.is_symlink()and folder.resolve().is_relative_to(R/'runs')
        size=sum(p.stat().st_size for p in t.packer(O/'cloud')['walk'](folder))
        shutil.rmtree(folder)
        removed.append(dict(path=str(folder.relative_to(R)),bytes=size))
    # O contains only small fixture/meta receipts after the large data is gone;
    # remove its archived fixture subdirectories as well, never other run roots.
    for folder in [p for p in O.iterdir()if p.is_dir()and p!=receipts]:
        assert not folder.is_symlink()
        size=sum(p.stat().st_size for p in t.packer(O)['walk'](folder))
        shutil.rmtree(folder)
        removed.append(dict(path=str(folder.relative_to(R)),bytes=size))
    t.dump(REC/'CLEANUP_RESULT.json',dict(removed=removed,deleted_bytes=sum(row['bytes']for row in removed),
         verified_remote_before_cleanup=True,models=0))
    receipt(REC/'CLEANUP_RESULT.json')
    t.dump(REC/'FINALIZED.json',dict(closed=True,status='SOURCE_AND_ZERO_MODEL_QUALIFIED_ONLY',models=0,integrations=0,
         source_and_all_member_sha_verified=True,remote_verified=True,physical_ready=False,models_authorized=False,
         release_url=index['release_url'],deleted_cache_bytes=sum(row['bytes']for row in removed)))
    receipt(REC/'FINALIZED.json')
    shutil.rmtree(receipts)
    print(json.dumps(dict(finalized=True,models=0,release_url=index['release_url'],deleted_bytes=sum(row['bytes']for row in removed))),flush=True)


if __name__=='__main__':
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    verify_frozen()
    try:
        {'prepare':prepare,'publish':publish}[sys.argv[1]]()
    except Exception as error:
        t.dump(O/(sys.argv[1].upper()+'_ERROR.json'),dict(error=repr(error),models=0,integrations=0,
              necessary_unverified_raw_retained=True,no_push_retry=True))
        raise
