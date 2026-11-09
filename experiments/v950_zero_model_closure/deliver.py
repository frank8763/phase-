"""Closed failed component batch: bounded Git sync and verified raw transport."""
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/v948_v951_delivery';REC=ROOT/'records/nav2_v948_v951_20261109'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh'
REPO='frank8763/phase-';TAG='phase-rpccr-forward-handoff-v948-v951-20261109'
SOURCES=['v948_forward_navigation','v949_steering_handoff','v950_steering_response',
         'v951_component_output_entry','v950_zero_model_closure']
FOLDERS=[ROOT/'runs'/p for p in ['v948_forward_navigation','v948_startup_fixture01',
    'v949_steering_handoff','v950_steering_response','v951_component_output_entry']]+[ROOT/'runs/v858_nav2_verified/v950']
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_FORWARD_HANDOFF_V948_V951_REPORT.md',
       str(REC.relative_to(ROOT)),*['experiments/'+s for s in SOURCES]]


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def dump(path,data):path.write_text(json.dumps(data,indent=2)+'\n')


def run(args,limit=30):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=limit)
    assert result.returncode==0,(result.stderr or result.stdout)[-1600:]
    return result.stdout


def gh(args,limit=120):return run([str(GH),*args,'--repo',REPO],limit)


def packer():
    spec=importlib.util.spec_from_file_location('closed_component_archive',ROOT/'experiments/v856_nav2_closure/package_records.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    result.OUT=OUT/'cloud';return result


def prepare():
    assert json.loads((ROOT/'runs/v951_component_output_entry/COMPLETION.json').read_text())['closed']
    assert not json.loads((ROOT/'runs/v951_component_output_entry/AUTHORIZATION.json').read_text())['models_authorized']
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    with(OUT/'PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    snapshot={}
    for folder in SOURCES:
        for p in (ROOT/'experiments'/folder).iterdir():
            if p.is_file():snapshot[str(p.relative_to(ROOT))]=sha(p)
    dump(REC/'SOURCE_SNAPSHOT.json',dict(files=snapshot,new_models_during_snapshot=0,integrations=0,outcome='COMPONENT_NOT_PASSED'))
    links=[]
    for folder in FOLDERS:
        for current,dirs,files in os.walk(folder,followlinks=False):
            for name in dirs+files:
                p=Path(current)/name
                if p.is_symlink():links.append(dict(path=str(p.relative_to(ROOT)),target=os.readlink(p),target_accessed=False))
    dump(REC/'GENERATED_LINKS.json',dict(links=links))
    module=packer();module.OUT.mkdir(exist_ok=False)
    files=[p for folder in [*FOLDERS,*[ROOT/'experiments'/s for s in SOURCES],REC]for p in module.walk(folder)]
    files.extend(ROOT/p for p in STAGE[:3])
    record=module.archive('v948-v951-closed-components',files)
    index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',
        outcome='NOT_PASSED_CURVED_RESPONSE',actual_native=1680,replay_native=1680,private_native=0,navigation=0,
        first_output_error_and_exception_preserved=True,archives=[{k:v for k,v in record.items()if k!='files'}])
    dump(REC/'RECORD_INDEX.json',index)
    run(['git','add','--',*STAGE]);run(['git','diff','--cached','--check'])
    staged=run(['git','diff','--cached','--name-only']).splitlines()
    assert all((ROOT/p).stat().st_size<90*1024**2 for p in staged),'OVERSIZE_GIT_BLOB'
    dump(OUT/'PREPARED.json',dict(staged=len(staged),all_member_sha_verified=True,models=0))
    print(json.dumps(dict(prepared=True,staged=len(staged),archives=index['archives'])),flush=True)


def verify_download(folder,index):
    for record in index['archives']:
        inventory=json.loads((folder/(record['group']+'.INVENTORY.json')).read_text())
        catalog={x['path']:x for x in inventory['files']}
        whole=hashlib.sha256();combined=folder/'combined.tar.zst'
        with combined.open('xb')as target:
            for part in record['parts']:
                path=folder/part['name'];assert path.stat().st_size==part['bytes']and sha(path)==part['sha256']
                with path.open('rb')as stream:
                    for block in iter(lambda:stream.read(1048576),b''):whole.update(block);target.write(block)
        assert whole.hexdigest()==record['archive_sha256']
        reader=subprocess.Popen(['zstd','-q','-dc',str(combined)],stdout=subprocess.PIPE);seen=set()
        with tarfile.open(fileobj=reader.stdout,mode='r|')as archive:
            for member in archive:
                assert member.isfile()and member.name not in seen;seen.add(member.name)
                row=catalog[member.name];h=hashlib.sha256()
                stream=archive.extractfile(member)
                for block in iter(lambda:stream.read(1048576),b''):h.update(block)
                assert member.size==row['bytes']and h.hexdigest()==row['sha256']
        assert reader.wait()==0 and seen==set(catalog)


def publish():
    assert(OUT/'PREPARED.json').exists()
    with(OUT/'PUBLICATION_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    run(['git','diff','--cached','--check'])
    run(['git','commit','-m','Constrain normal navigation forward and diagnose measured brake-steering handoff'])
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
    assets=[p for p in (OUT/'cloud').iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json']
    gh(['release','create',TAG,'--target',head,'--title','RP-CCR forward navigation and measured brake-steering handoff qualification',
        '--notes','NOT_PASSED. Fixed responses0–2passed,3failed original yaw and half-second stop gates;14responses+1handoff unexecuted.1680actual+1680full own-control replay;private/navigation/new24/training0. Original output-scope error and explicit one-time metadata continuation preserved. All old results unchanged.','--draft'])
    gh(['release','upload',TAG,*map(str,assets)])
    downloaded=OUT/'readback';downloaded.mkdir(exist_ok=False)
    gh(['release','download',TAG,'--dir',str(downloaded)])
    for p in assets:assert sha(p)==sha(downloaded/p.name)
    verify_download(downloaded,index)
    gh(['release','edit',TAG,'--draft=false'])
    proof=dict(passed=True,source_commit=head,release_url=index['release_url'],
        all_asset_download_sha_verified=True,all_decompressed_members_sha_verified=True,new_models=0)
    dump(REC/'REMOTE_VERIFIED.json',proof)
    for path in [REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:
        gh(['release','upload',TAG,str(path)]);gh(['release','download',TAG,'--pattern',path.name,'--dir',str(downloaded)])
        assert sha(path)==sha(downloaded/path.name)
    deleted=0
    # These source caches are unmodified restored V945 evidence, whose original
    # release is reverified before their deletion; no original sync is repeated.
    run([sys.executable,'-B','experiments/v946_rpccr_regression_closure/restore_selected.py','runs/v858_nav2_verified/v945/main_we'],180)
    cleanup=[*FOLDERS,ROOT/'runs/v858_nav2_verified/v945',downloaded,OUT/'cloud']
    removed=[]
    for folder in cleanup:
        if not folder.exists():continue
        assert folder.resolve().is_relative_to(ROOT/'runs')and not folder.is_symlink()
        size=sum(p.stat().st_size for p in folder.rglob('*')if p.is_file()and not p.is_symlink())
        removed.append(dict(path=str(folder.relative_to(ROOT)),bytes=size));deleted+=size;shutil.rmtree(folder)
    dump(REC/'CLEANUP_RESULT.json',dict(deleted_bytes=deleted,removed=removed,remote_verified_before_cleanup=True,models=0))
    gh(['release','upload',TAG,str(REC/'CLEANUP_RESULT.json')])
    receipt=OUT/'receipt_readback';receipt.mkdir(exist_ok=False)
    gh(['release','download',TAG,'--pattern','CLEANUP_RESULT.json','--dir',str(receipt)])
    assert sha(REC/'CLEANUP_RESULT.json')==sha(receipt/'CLEANUP_RESULT.json');shutil.rmtree(receipt)
    dump(REC/'FINALIZED.json',dict(closed=True,scientific_outcome='NOT_PASSED',all_sources_and_decompressed_sha_verified=True,
        remote_verified=True,raw_cache_cleaned=True,release_url=index['release_url'],new_integrations_during_close=0))
    run(['git','add','--',str(REC.relative_to(ROOT))]);run(['git','commit','-m','Record verified failed component transport and bounded cache cleanup'])
    print(json.dumps(dict(remote=proof,deleted_bytes=deleted)),flush=True)


if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(ROOT/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    {'prepare':prepare,'publish':publish}[sys.argv[1]]()
