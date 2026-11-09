"""One combined source sync; verified failed/qualified response evidence and cleanup."""
import fcntl
import importlib.util
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/v969_rpp_night_delivery';REC=ROOT/'records/nav2_v968_20261109'
SOURCES=['v968_rpp_closed_loop_night','v969_rpp_night_closure']
FOLDERS=[ROOT/'runs/v968_rpp_closed_loop_night',ROOT/'runs/v858_nav2_verified/v968',*[ROOT/'runs'/s for s in ['v968_startup_fixture01','v968_component_software_fixture','v968_component_software_fixture02','v968_component_software_fixture03']]]
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_CLOSED_LOOP_NIGHT_V968_REPORT.md',str(REC.relative_to(ROOT)),*['experiments/'+s for s in SOURCES]]
TAG='phase-rpccr-rpp-closed-loop-v968-20261109'
spec=importlib.util.spec_from_file_location('verified_closed_transport',ROOT/'experiments/v954_stop_align_closure/deliver.py')
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
transport.OUT=OUT;transport.REC=REC;transport.TAG=TAG
sha=transport.sha;run=transport.run;gh=transport.gh;dump=transport.dump


def prepare():
    assert json.loads((REC/'LOCAL_CLOSURE.json').read_text())['closed']
    assert json.loads((REC/'FINAL_INDEPENDENT_AUDIT.json').read_text())['source_sha_all_verified']
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    with(OUT/'PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    snapshot={str(p.relative_to(ROOT)):sha(p)for s in SOURCES for p in(ROOT/'experiments'/s).iterdir()if p.is_file()}
    dump(REC/'SOURCE_SNAPSHOT.json',dict(files=snapshot,new_models=0,integrations=0))
    links=[]
    for folder in FOLDERS:
        for current,dirs,files in os.walk(folder,followlinks=False):
            for name in dirs+files:
                p=Path(current)/name
                if p.is_symlink():links.append(dict(path=str(p.relative_to(ROOT)),target=os.readlink(p),target_accessed=False))
    dump(REC/'GENERATED_LINKS.json',dict(links=links))
    module=transport.packer();module.OUT.mkdir(exist_ok=False)
    excluded=[];files=[]
    for folder in [*FOLDERS,*[ROOT/'experiments'/s for s in SOURCES]]:
        for p in module.walk(folder):
            if '__pycache__'in p.parts or 'mesa_shader_cache'in p.parts or p.name in {'close.console','campaign.console'}:
                excluded.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size,reason='REBUILDABLE_CACHE_OR_EXCLUDED_ACTIVE_CLOSURE_OUTPUT'))
            else:files.append(p)
    dump(REC/'EXCLUDED_REBUILDABLE_CACHE.json',dict(files=excluded,not_required_for_scientific_replay=True))
    files.extend(module.walk(REC));files.extend(ROOT/p for p in STAGE[:3])
    record=module.archive('v968-rpp-closed-loop-night',files)
    result=json.loads((REC/'FINAL_INDEPENDENT_AUDIT.json').read_text())
    index=dict(repository='frank8763/phase-',release_tag=TAG,release_url=f'https://github.com/frank8763/phase-/releases/tag/{TAG}',
        scientific_outcome=result['night_status'],current_status=result['current_status'],counts=result['counts'],handoff=result['handoff_result'],
        training=0,hardware=0,archives=[{k:v for k,v in record.items()if k!='files'}])
    dump(REC/'RECORD_INDEX.json',index)
    run(['git','add','--',*STAGE]);run(['git','diff','--cached','--check'])
    staged=run(['git','diff','--cached','--name-only']).splitlines()
    assert all((ROOT/p).stat().st_size<90*1024**2 for p in staged)
    dump(OUT/'PREPARED.json',dict(staged=len(staged),member_sha_verified=True,new_models=0))
    print(json.dumps(dict(prepared=True,staged=len(staged),archive=index['archives'])),flush=True)


def publish():
    assert(OUT/'PREPARED.json').exists()
    with(OUT/'PUBLICATION_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    run(['git','diff','--cached','--check'])
    run(['git','commit','-m','Record actual RPP closed-loop handoff and fixed-deadline night chain'])
    head=run(['git','rev-parse','HEAD']).strip();sync=dict(commit=head,one_attempt=True,push_limit_s=30,remote_read_limit_s=5)
    with(REC/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as e:sync['push_error']=repr(e)
    try:
        sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==head
    except Exception as e:sync['verify_error']=repr(e)
    dump(REC/'GIT_SYNC_RESULT.json',sync);assert sync.get('remote_head_verified'),'SOURCE_REMOTE_UNKNOWN_KEEP_RAW_NO_RETRY'
    index=json.loads((REC/'RECORD_INDEX.json').read_text())
    assets=[p for p in(OUT/'cloud').iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json']
    gh(['release','create',TAG,'--target',head,'--title','RP-CCR measured steering-continuity and conditional dynamic validation',
        '--notes','New bounded V968 actual closed-loop RPP handoff and conditional original routes/fixed24 night chain. Old V962 failure retained. Outcome and exact attempted/unexecuted denominators in RECORD_INDEX and report. Old failures/windows preserved; no model retry, training or hardware. Full native/control/sensor/model evidence with source and decompressed-member SHA verification.','--draft'])
    gh(['release','upload',TAG,*map(str,assets)])
    downloaded=OUT/'readback';downloaded.mkdir(exist_ok=False)
    gh(['release','download',TAG,'--dir',str(downloaded)])
    for p in assets:assert sha(p)==sha(downloaded/p.name)
    transport.shared_verifier()(downloaded,index)
    gh(['release','edit',TAG,'--draft=false'])
    dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,source_commit=head,release_url=index['release_url'],
        all_asset_download_sha_verified=True,all_decompressed_members_sha_verified=True,new_models=0))
    for p in [REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:transport.upload_receipt(p,downloaded)
    inventory=json.loads((downloaded/(index['archives'][0]['group']+'.INVENTORY.json')).read_text())
    catalog={r['path']:r for r in inventory['files']}
    catalog.update({r['path']:r for r in json.loads((REC/'EXCLUDED_REBUILDABLE_CACHE.json').read_text())['files']})
    # Freeze deletion to the exact closed files, including explicitly disposable caches.
    for folder in FOLDERS:
        for p in transport.packer().walk(folder):
            if p.name in {'close.console','campaign.console'}:continue
            row=catalog[str(p.relative_to(ROOT))];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
    restored=json.loads((REC/'RESTORE_RECEIPT.json').read_text())['restored']
    for row in restored:
        p=ROOT/row['path'];assert p.resolve().is_relative_to(ROOT/'runs')and not p.is_symlink()and sha(p)==row['sha256']
    removed=[];deleted=0
    for folder in [*FOLDERS,downloaded,OUT/'cloud']:
        if not folder.exists():continue
        assert folder.resolve().is_relative_to(ROOT/'runs')and not folder.is_symlink()
        if folder==ROOT/'runs/v968_rpp_closed_loop_night':
            targets=[p for p in folder.iterdir()if p.name not in {'close.console','campaign.console'}]
            size=0
            for p in targets:
                if p.is_symlink():p.unlink();continue
                if p.is_dir():
                    size+=sum(q.stat().st_size for q in transport.packer().walk(p));shutil.rmtree(p)
                else:size+=p.stat().st_size;p.unlink()
        else:
            size=sum(p.stat().st_size for p in transport.packer().walk(folder));shutil.rmtree(folder)
        removed.append(dict(path=str(folder.relative_to(ROOT)),bytes=size));deleted+=size
    for row in restored:
        p=ROOT/row['path'];p.unlink();deleted+=row['bytes']
    removed.append(dict(path='EXACT_OLD_SELECTIVE_RESTORE_RECEIPT_FILES',files=len(restored),bytes=sum(r['bytes']for r in restored)))
    dump(REC/'CLEANUP_RESULT.json',dict(deleted_bytes=deleted,removed=removed,remote_verified_before_cleanup=True,new_models=0))
    receipt=OUT/'receipt_readback';receipt.mkdir(exist_ok=False)
    transport.upload_receipt(REC/'CLEANUP_RESULT.json',receipt)
    dump(REC/'FINALIZED.json',dict(closed=True,scientific_outcome=index['scientific_outcome'],all_sources_and_decompressed_sha_verified=True,
        remote_verified=True,raw_cache_cleaned=True,release_url=index['release_url'],new_integrations_during_close=0))
    transport.upload_receipt(REC/'FINALIZED.json',receipt);shutil.rmtree(receipt)
    run(['git','add','--',str(REC.relative_to(ROOT))]);run(['git','commit','-m','Record verified continuous dynamic evidence transport and cache cleanup'])
    print(json.dumps(dict(remote_verified=True,release_url=index['release_url'],deleted_bytes=deleted)),flush=True)


if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(ROOT/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    {'prepare':prepare,'publish':publish}[sys.argv[1]]()
