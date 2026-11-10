"""One root evidence delivery; review staged diff before publish, zero models."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
ROOT=R/'runs/daytime_20261110_until20';O=R/'runs/v994_diagnostic_timing_postmortem'
REC=R/'records/nav2_v993_20261110';TAG='phase-rpccr-steering-diagnostics-v993-20261110';REPO='frank8763/phase-'
GH=R/'tools/phase_storage_20261107/vendor/gh'
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_STEERING_DIAGNOSTICS_V993_V994_REPORT.md',
       'experiments/v993_steering_transient_diagnosis','experiments/v994_diagnostic_timing_postmortem',str(REC.relative_to(R))]
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def run(args,limit=30):
    x=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=limit)
    assert x.returncode==0,(x.stderr or x.stdout)[-1800:]
    return x.stdout
def gh(args):return run([str(GH),*args,'--repo',REPO])
spec=importlib.util.spec_from_file_location('v994_verified_storage_helpers',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)

def verified_sources():
    for path in [R/'experiments/v993_steering_transient_diagnosis/SOURCE_FREEZE.json',C/'SOURCE_FREEZE.json']:
        assert all(sha(R/p)==h for p,h in read(path)['files'].items()),str(path)
def prepare():
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    assert read(ROOT/'CLOSURE.json')['model_authority']is False
    with(O/'DELIVERY_PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    verified_sources();cloud=O/'cloud';cloud.mkdir(exist_ok=False);pack=t.packer(cloud)
    files=[];excluded=[]
    for root in [ROOT,R/'runs/v993_steering_transient_diagnosis',R/'runs/v858_nav2_verified/v993',O,REC,
                 R/'experiments/v993_steering_transient_diagnosis',C]:
        for p in pack['walk'](root):
            if cloud in p.parents:continue
            if p.suffix=='.lock'or '__pycache__'in p.parts or 'cache'in p.parts:
                excluded.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),reason='rebuildable_shader_or_python_cache_or_idle_lock'))
                continue
            files.append(p)
    files += [R/p for p in STAGE[:3]]
    assert sum(p.stat().st_size for p in set(files))<2*1024**3,'CACHE_BUDGET'
    dump(REC/'EXCLUDED_REBUILDABLE_FILES.json',dict(files=excluded,necessary_actual_evidence_excluded=False))
    files.append(REC/'EXCLUDED_REBUILDABLE_FILES.json')
    group=pack['archive']('v993-actual-diagnostics-and-v994-zero-model-diagnosis',files)
    index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',
        status='V993_NOT_PASSED_TIMING_INTERRUPTION',navigation_passed=False,new24=0,
        actual_counts=read(REC/'FINAL_INDEPENDENT_ACCOUNTING.json')['counts'],models_during_delivery=0,
        archives=[{k:v for k,v in group.items()if k!='files'}])
    dump(REC/'RECORD_INDEX.json',index)
    run(['git','add','--',*STAGE]);run(['git','diff','--cached','--check'])
    for p in run(['git','diff','--cached','--name-only']).splitlines():assert(R/p).stat().st_size<90*1024**2
    dump(O/'DELIVERY_PREPARED.json',dict(prepared=True,archive_member_sha_verified=True,models=0))

def publish():
    assert read(O/'DELIVERY_PREPARED.json')['prepared'];verified_sources()
    assert not(ROOT/'GIT_SYNC_CLAIM.json').exists()and not(ROOT/'GIT_SYNC_RESULT.json').exists(),'NO_SECOND_ROOT_PUSH'
    run(['git','diff','--cached','--check'])
    run(['git','commit','-m','Preserve fixed steering diagnostic timing failure and qualify fault timing evidence without models'])
    commit=run(['git','rev-parse','HEAD']).strip()
    sync=dict(commit=commit,one_attempt=True,push_limit_s=30,remote_read_limit_s=5)
    with(ROOT/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    (REC/'GIT_SYNC_CLAIM.json').write_bytes((ROOT/'GIT_SYNC_CLAIM.json').read_bytes())
    try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as e:sync['push_error']=repr(e)
    try:sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==commit
    except Exception as e:sync['verify_error']=repr(e)
    dump(ROOT/'GIT_SYNC_RESULT.json',sync);dump(REC/'GIT_SYNC_RESULT.json',sync)
    assert sync.get('remote_head_verified'),'SOURCE_REMOTE_UNKNOWN_KEEP_RAW_NO_RETRY'
    gh(['release','create',TAG,'--target',commit,'--title','V993 steering response: timing interruption; V994 zero-model timing evidence',
        '--notes','V993 first fixed diagnostic complete; second stopped by original 100ms wall lag gate after301 new steps, no complete stop/replay. Remaining tasks unexecuted. No navigation acceptance. Original actual traces and failures preserved; V994 only no-model diagnosis.','--draft'])
    index=read(REC/'RECORD_INDEX.json');cloud=O/'cloud'
    assets=[p for p in cloud.iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json']
    gh(['release','upload',TAG,*map(str,assets)])
    back=O/'readback';back.mkdir(exist_ok=False)
    for p in assets:
        gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)])
        assert sha(p)==sha(back/p.name)
    t.verifier()(back,index);gh(['release','edit',TAG,'--draft=false'])
    dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,commit=commit,all_asset_and_decompressed_member_sha_verified=True,
         original_scientific_outcome='NOT_PASSED_TIMING_INTERRUPTION',models_during_delivery=0))
    receipts=O/'receipt_readback';receipts.mkdir(exist_ok=False)
    def receipt(p):
        gh(['release','upload',TAG,str(p)]);gh(['release','download',TAG,'--pattern',p.name,'--dir',str(receipts)])
        assert sha(p)==sha(receipts/p.name)
    for p in [REC/'GIT_SYNC_CLAIM.json',REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:receipt(p)
    catalog={x['path']:x for x in read(back/(index['archives'][0]['group']+'.INVENTORY.json'))['files']}
    excluded={x['path']:x for x in read(REC/'EXCLUDED_REBUILDABLE_FILES.json')['files']}
    deleted=[]
    roots=[R/'runs/v858_nav2_verified/v993',R/'runs/v993_steering_transient_diagnosis/prior_v974']
    for root in roots:
        assert root.is_relative_to(R/'runs')and not root.is_symlink()
        size=0
        for p in t.packer(cloud)['walk'](root):
            rel=str(p.relative_to(R));row=catalog.get(rel,excluded.get(rel));assert row is not None,rel
            assert sha(p)==row['sha256']and p.stat().st_size==row['bytes'],rel;size+=p.stat().st_size
        assert not any(p.is_symlink()for p in root.rglob('*')),'NO_SYMLINK_CLEANUP'
        shutil.rmtree(root);deleted.append(dict(path=str(root.relative_to(R)),bytes=size))
    for root in [cloud,back]:
        size=sum(p.stat().st_size for p in t.packer(cloud)['walk'](root));shutil.rmtree(root)
        deleted.append(dict(path=str(root.relative_to(R)),bytes=size))
    dump(REC/'CLEANUP_RESULT.json',dict(deleted=deleted,deleted_bytes=sum(x['bytes']for x in deleted),verified_remote_before_cleanup=True,models=0))
    receipt(REC/'CLEANUP_RESULT.json')
    dump(REC/'FINALIZED.json',dict(closed=True,scientific_status='NOT_PASSED_TIMING_INTERRUPTION',
        archive_and_member_sha_remote_verified=True,raw_cache_cleaned=True,models_authorized=False,
        source_commit=commit,release_url=index['release_url'],no_second_push=True))
    receipt(REC/'FINALIZED.json');shutil.rmtree(receipts)
    print(json.dumps(dict(finalized=True,source_commit=commit,release_url=index['release_url'],deleted_bytes=sum(x['bytes']for x in deleted))),flush=True)

if __name__=='__main__':
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    try:{'prepare':prepare,'publish':publish}[sys.argv[1]]()
    except BaseException as e:
        dump(O/(sys.argv[1].upper()+'_DELIVERY_ERROR.json'),dict(error=repr(e),models=0,unverified_raw_retained=True,no_push_retry=True));raise
