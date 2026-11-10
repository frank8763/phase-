"""One source-only batch delivery, one Git push, one immutable archive readback."""
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

R=Path(__file__).resolve().parents[2];C=R/'experiments/v977_state_consistent_recovery'
O=R/'runs/v978_source_only_closure';RAW=R/'runs/v977_state_consistent_recovery';REC=R/'records/nav2_v977_20261110'
TAG='phase-rpccr-state-recovery-v977-20261110';REPO='frank8763/phase-'
GH=R/'tools/phase_storage_20261107/vendor/gh'
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_STATE_CONSISTENT_RECOVERY_V977_REPORT.md',
       'experiments/v977_state_consistent_recovery','experiments/v978_source_only_closure','records/nav2_v977_20261110']


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def dump(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')


def run(args,limit=30):
    result=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=limit)
    assert result.returncode==0,(result.stdout+result.stderr)[-1800:]
    return result.stdout


def gh(args,limit=30):return run([str(GH),*args,'--repo',REPO],limit)


def packer(out):
    path=R/'experiments/v856_nav2_closure/package_records.py';tree=ast.parse(path.read_text())
    nodes=[x for x in tree.body if isinstance(x,(ast.Import,ast.ImportFrom,ast.FunctionDef))]
    namespace=dict(R=R,ROOT=R,OUT=out,CHUNK=32*1024**2)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),'exec'),namespace)
    return namespace


def verifier():
    spec=importlib.util.spec_from_file_location('v978_single_archive_verifier',R/'experiments/v950_zero_model_closure/deliver.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.verify_download


def prepare():
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    with(O/'PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    final=json.loads((REC/'FINAL_ZERO_MODEL_AUDIT.json').read_text());assert final['passed'] and not final['physical_ready']
    for rel,digest in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items():assert sha(R/rel)==digest,rel
    assert json.loads((REC/'AUTHORIZATION.json').read_text())['models_authorized'] is False
    cloud=O/'cloud';cloud.mkdir(exist_ok=False);p=packer(cloud)
    files=list(p['walk'](RAW))+list(p['walk'](C))+list(p['walk'](Path(__file__).parent))+list(p['walk'](REC))+[R/x for x in STAGE[:3]]
    assert sum(x.stat().st_size for x in files)<64*1024**2,'SOURCE_ONLY_CACHE_BUDGET'
    group=p['archive']('v977-source-and-zero-model-qualification',files)
    index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',
               status='SOURCE_AND_ZERO_MODEL_QUALIFIED_ONLY',models=0,integrations=0,new_navigation_trials=0,
               physical_tracking_qualified=False,model_authority=False,archives=[{k:v for k,v in group.items()if k!='files'}])
    dump(REC/'RECORD_INDEX.json',index)
    run(['git','add','--',*STAGE]);run(['git','diff','--cached','--check'])
    for name in run(['git','diff','--cached','--name-only']).splitlines():assert (R/name).lstat().st_size<90*1024**2
    dump(O/'PREPARED.json',dict(prepared=True,models=0,all_source_and_member_sha_verified=True))
    print(json.dumps(dict(prepared=True,archive_bytes=group['archive_bytes'],files=group['source_files'])),flush=True)


def publish():
    assert(O/'PREPARED.json').exists()
    with(O/'PUBLISH_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    run(['git','diff','--cached','--check']);run(['git','commit','-m','Qualify steering-state recovery references and exclusive RPP handoff without physical models'])
    commit=run(['git','rev-parse','HEAD']).strip()
    sync=dict(commit=commit,one_attempt=True,push_limit_s=30,remote_head_read_limit_s=5)
    with(REC/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as error:sync['push_error']=repr(error)
    try:sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==commit
    except Exception as error:sync['verify_error']=repr(error)
    dump(REC/'GIT_SYNC_RESULT.json',sync)
    assert sync.get('remote_head_verified'),'SOURCE_REMOTE_UNKNOWN_KEEP_RAW_NO_RETRY'
    index=json.loads((REC/'RECORD_INDEX.json').read_text())
    gh(['release','create',TAG,'--target',commit,'--title','Steering-state recovery: source and zero-model qualification only',
        '--notes','Two fixed V974 causal states; source/geometry/installed RPP software qualifications only. Zero physical models/integrations/new navigation trials. Old failures retained. Full dynamic acceptance remains unpassed.','--draft'])
    assets=[p for p in(O/'cloud').iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json']
    gh(['release','upload',TAG,*map(str,assets)])
    readback=O/'readback';readback.mkdir(exist_ok=False)
    for path in assets:
        gh(['release','download',TAG,'--pattern',path.name,'--dir',str(readback)])
        assert sha(path)==sha(readback/path.name)
    verifier()(readback,index)
    catalog={x['path']:x for x in json.loads((readback/'v977-source-and-zero-model-qualification.INVENTORY.json').read_text())['files']}
    for path in packer(O/'cloud')['walk'](RAW):
        row=catalog[str(path.relative_to(R))];assert sha(path)==row['sha256']and path.stat().st_size==row['bytes']
    gh(['release','edit',TAG,'--draft=false'])
    dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,all_asset_and_member_sha_verified=True,source_commit=commit,
         release_url=index['release_url'],models=0,physical_outcome='UNTESTED_IN_THIS_BATCH'))
    receipts=O/'receipt_readback';receipts.mkdir(exist_ok=False)
    def receipt(path):
        gh(['release','upload',TAG,str(path)]);gh(['release','download',TAG,'--pattern',path.name,'--dir',str(receipts)])
        assert sha(path)==sha(receipts/path.name)
    for path in [REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:receipt(path)
    deleted=[]
    for folder in [RAW,O/'cloud',readback]:
        assert folder.resolve().is_relative_to(R/'runs') and not folder.is_symlink()
        size=sum(x.stat().st_size for x in packer(O/'cloud')['walk'](folder));shutil.rmtree(folder)
        deleted.append(dict(path=str(folder.relative_to(R)),bytes=size))
    dump(REC/'CLEANUP_RESULT.json',dict(removed=deleted,deleted_bytes=sum(x['bytes']for x in deleted),
         verified_remote_before_cleanup=True,models=0))
    receipt(REC/'CLEANUP_RESULT.json')
    dump(REC/'FINALIZED.json',dict(closed=True,status='SOURCE_AND_ZERO_MODEL_QUALIFIED_ONLY',models=0,integrations=0,
         source_and_all_member_sha_verified=True,remote_verified=True,raw_cache_cleaned=True,physical_ready=False,
         models_authorized=False,release_url=index['release_url']))
    receipt(REC/'FINALIZED.json');shutil.rmtree(receipts)
    print(json.dumps(dict(finalized=True,models=0,release_url=index['release_url'],deleted_bytes=sum(x['bytes']for x in deleted))),flush=True)


if __name__=='__main__':
    O.mkdir(exist_ok=True)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    try:{'prepare':prepare,'publish':publish}[sys.argv[1]]()
    except Exception as error:
        dump(O/(sys.argv[1].upper()+'_ERROR.json'),dict(error=repr(error),models=0,integrations=0,unverified_raw_retained=True,no_git_push_retry=True))
        raise
