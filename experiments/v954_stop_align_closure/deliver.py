"""Bounded source sync and fully verified closed evidence transport, no models."""
import ast
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/v954_stop_align_delivery';REC=ROOT/'records/nav2_v952_v953_20261109'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh'
REPO='frank8763/phase-';TAG='phase-rpccr-stop-align-v952-v953-20261109'
SOURCES=['v952_stopped_steering_alignment','v953_stop_align_components','v954_stop_align_closure']
FOLDERS=[ROOT/'runs'/s for s in SOURCES]+[ROOT/'runs/v858_nav2_verified/v953']
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_STOP_ALIGN_V952_V953_REPORT.md',
    str(REC.relative_to(ROOT)),*['experiments/'+s for s in SOURCES]]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as source:
        for block in iter(lambda:source.read(1048576),b''):h.update(block)
    return h.hexdigest()


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def run(args,limit=30):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=limit)
    assert result.returncode==0,(result.stderr or result.stdout)[-1600:]
    return result.stdout


def gh(args,limit=120):return run([str(GH),*args,'--repo',REPO],limit)


def packer():
    # Reuse only definitions from the established packer; skip its old-run mkdir
    # and main entry, so importing maintenance code never mutates an old batch.
    path=ROOT/'experiments/v856_nav2_closure/package_records.py';tree=ast.parse(path.read_text())
    selected=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom,ast.FunctionDef))]
    context=dict(R=ROOT,ROOT=ROOT,OUT=OUT/'cloud',CHUNK=32*1024**2)
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])),str(path),'exec'),context)
    return SimpleNamespace(**context)


def shared_verifier():
    path=ROOT/'experiments/v950_zero_model_closure/deliver.py'
    spec=importlib.util.spec_from_file_location('closed_archive_member_verifier',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.verify_download


def prepare():
    assert json.loads((REC/'LOCAL_CLOSURE.json').read_text())['closed']
    assert not json.loads((ROOT/'runs/v953_stop_align_components/AUTHORIZATION.json').read_text())['models_authorized']
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    with(OUT/'PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    snapshot={str(p.relative_to(ROOT)):sha(p)for s in SOURCES for p in (ROOT/'experiments'/s).iterdir()if p.is_file()}
    dump(REC/'SOURCE_SNAPSHOT.json',dict(files=snapshot,new_models=0,integrations=0))
    links=[]
    for folder in FOLDERS:
        for current,dirs,files in os.walk(folder,followlinks=False):
            for name in dirs+files:
                path=Path(current)/name
                if path.is_symlink():links.append(dict(path=str(path.relative_to(ROOT)),target=os.readlink(path),target_accessed=False))
    dump(REC/'GENERATED_LINKS.json',dict(links=links))
    module=packer();module.OUT.mkdir(exist_ok=False)
    files=[p for folder in [*FOLDERS,*[ROOT/'experiments'/s for s in SOURCES],REC]for p in module.walk(folder)
        if '__pycache__'not in p.parts]
    files.extend(ROOT/p for p in STAGE[:3])
    record=module.archive('v952-v953-stop-align-closed',files)
    index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',
        outcome='NOT_PASSED_MEASURED_ALIGNMENT',models=2,actual_native=840,replay_native=840,private_native=0,
        navigation=0,new24=0,unexecuted_response_cases=16,unexecuted_handoff_cases=1,
        original_and_latent_errors_preserved=True,archives=[{k:v for k,v in record.items()if k!='files'}])
    dump(REC/'RECORD_INDEX.json',index)
    run(['git','add','--',*STAGE]);run(['git','diff','--cached','--check'])
    staged=run(['git','diff','--cached','--name-only']).splitlines()
    assert all((ROOT/p).stat().st_size<90*1024**2 for p in staged),'OVERSIZE_GIT_BLOB'
    dump(OUT/'PREPARED.json',dict(staged=len(staged),all_member_sha_verified=True,models=0))
    print(json.dumps(dict(prepared=True,staged=len(staged),archive=index['archives'])),flush=True)


def upload_receipt(path,downloaded):
    gh(['release','upload',TAG,str(path)])
    gh(['release','download',TAG,'--pattern',path.name,'--dir',str(downloaded)])
    assert sha(path)==sha(downloaded/path.name)


def publish():
    assert(OUT/'PREPARED.json').exists()
    with(OUT/'PUBLICATION_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    run(['git','diff','--cached','--check'])
    run(['git','commit','-m','Diagnose stop-alignment interlock chatter with complete native component evidence'])
    head=run(['git','rev-parse','HEAD']).strip()
    sync=dict(commit=head,one_attempt=True,push_limit_s=30,remote_read_limit_s=5)
    with(REC/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as error:sync['push_error']=repr(error)
    try:
        sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0]
        sync['remote_head_verified']=sync['remote_head']==head
    except Exception as error:sync['verify_error']=repr(error)
    dump(REC/'GIT_SYNC_RESULT.json',sync)
    assert sync.get('remote_head_verified'),'SOURCE_REMOTE_UNKNOWN_KEEP_RAW_NO_RETRY'
    index=json.loads((REC/'RECORD_INDEX.json').read_text())
    assets=[p for p in(OUT/'cloud').iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json']
    gh(['release','create',TAG,'--target',head,'--title','RP-CCR measured stop-alignment component evidence V952-V953',
        '--notes','NOT_PASSED. Original response0 passed; response1 failed measured steering alignment.16responses and1complete1.2m handoff unexecuted.2models/840actual/840own-control replay;private/navigation/new24/training0. Nine one-tick ALIGNING episodes independently reconstructed. Unexecuted handoff array-length defect and preparation errors retained. No model retry or extension.','--draft'])
    gh(['release','upload',TAG,*map(str,assets)])
    downloaded=OUT/'readback';downloaded.mkdir(exist_ok=False)
    gh(['release','download',TAG,'--dir',str(downloaded)])
    for path in assets:assert sha(path)==sha(downloaded/path.name)
    shared_verifier()(downloaded,index)
    gh(['release','edit',TAG,'--draft=false'])
    proof=dict(passed=True,source_commit=head,release_url=index['release_url'],
        all_asset_download_sha_verified=True,all_decompressed_members_sha_verified=True,new_models=0)
    dump(REC/'REMOTE_VERIFIED.json',proof)
    for path in [REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:upload_receipt(path,downloaded)
    restored=json.loads((REC/'v952_stopped_steering_alignment_RESTORE_RECEIPT.json').read_text())
    assert restored['passed']
    oldcache=ROOT/'runs/v858_nav2_verified/v950/response_03'
    expected={row['path']:row for row in restored['restored']}
    actual={str(p.relative_to(ROOT))for p in oldcache.rglob('*')if p.is_file()and not p.is_symlink()}
    assert actual==set(expected),'RESTORED_OLD_CACHE_CHANGED'
    for path,row in expected.items():assert sha(ROOT/path)==row['sha256']
    removed=[];deleted=0
    for folder in [*FOLDERS,oldcache,downloaded,OUT/'cloud']:
        if not folder.exists():continue
        assert folder.resolve().is_relative_to(ROOT/'runs')and not folder.is_symlink()
        size=sum(p.stat().st_size for p in folder.rglob('*')if p.is_file()and not p.is_symlink())
        removed.append(dict(path=str(folder.relative_to(ROOT)),bytes=size));deleted+=size;shutil.rmtree(folder)
    dump(REC/'CLEANUP_RESULT.json',dict(deleted_bytes=deleted,removed=removed,remote_verified_before_cleanup=True,models=0))
    receipt=OUT/'receipt_readback';receipt.mkdir(exist_ok=False)
    upload_receipt(REC/'CLEANUP_RESULT.json',receipt)
    dump(REC/'FINALIZED.json',dict(closed=True,scientific_outcome='NOT_PASSED',all_sources_and_decompressed_sha_verified=True,
        remote_verified=True,raw_cache_cleaned=True,release_url=index['release_url'],new_integrations_during_close=0))
    upload_receipt(REC/'FINALIZED.json',receipt);shutil.rmtree(receipt)
    run(['git','add','--',str(REC.relative_to(ROOT))])
    run(['git','commit','-m','Record verified stop-alignment evidence transport and cache cleanup'])
    print(json.dumps(dict(remote=proof,deleted_bytes=deleted)),flush=True)


if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(ROOT/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    {'prepare':prepare,'publish':publish}[sys.argv[1]]()
