"""One root evidence delivery; review staged diff before publish, zero models."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
ROOT=R/'runs/v1001_local_reference_closure';O=R/'runs/v1001_local_reference_closure'
REC=R/'records/nav2_v1000_20261110';TAG='phase-rpccr-local-progress-source-v1000-20261110';REPO='frank8763/phase-'
GH=R/'tools/phase_storage_20261107/vendor/gh'
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_LOCAL_PROGRESS_REFERENCE_V999_V1001_REPORT.md','docs/figures/V1000_CAUSAL_LOCAL_REFERENCES.png',
 'experiments/v999_search_resolution_diagnosis','experiments/v1000_local_progress_reference','experiments/v1001_local_reference_closure',str(REC.relative_to(R))]
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
    for path in [R/'experiments/v999_search_resolution_diagnosis/SOURCE_FREEZE.json',R/'experiments/v1000_local_progress_reference/SOURCE_FREEZE.json']:
        assert all(sha(R/p)==h for p,h in read(path)['files'].items()),str(path)
def prepare():
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    assert read(ROOT/'COMPLETION.json')['model_authority']is False
    with(O/'DELIVERY_PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    verified_sources();cloud=O/'cloud';cloud.mkdir(exist_ok=False);pack=t.packer(cloud)
    files=[];excluded=[];links=[]
    roots=[R/'runs/v999_search_resolution_diagnosis',R/'runs/v1000_local_progress_reference',O,REC]+[R/x for x in STAGE[4:7]]
    for root in roots:
        for current,dirs,names in os.walk(root,followlinks=False):
            for name in dirs+names:
                p=Path(current)/name
                if p.is_symlink():links.append(dict(path=str(p.relative_to(R)),target=os.readlink(p),target_accessed=False))
        for p in pack['walk'](root):
            if cloud in p.parents:continue
            if p.suffix=='.lock'or '__pycache__'in p.parts or 'cache'in p.parts:
                excluded.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),reason='rebuildable_shader_or_python_cache_or_idle_lock'));continue
            files.append(p)
    dump(REC/'SYMLINKS_MANIFEST.json',dict(links=links,models=0,target_accessed=False))
    files.append(REC/'SYMLINKS_MANIFEST.json')
    files += [R/p for p in STAGE[:4]]+[R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json']
    assert sum(p.stat().st_size for p in set(files))<2*1024**3,'CACHE_BUDGET'
    dump(REC/'EXCLUDED_REBUILDABLE_FILES.json',dict(files=excluded,necessary_actual_evidence_excluded=False))
    files.append(REC/'EXCLUDED_REBUILDABLE_FILES.json')
    group=pack['archive']('v1000-local-progress-source-qualification',files)
    index=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',
        status='TWO_CAUSAL_FINITE_PROGRESS_REFERENCES_SOURCE_QUALIFIED',navigation_passed=False,new24=0,
        actual_counts=read(REC/'FINAL_INDEPENDENT_ACCOUNTING.json')['actual_counts'],models_during_delivery=0,
        archives=[{k:v for k,v in group.items()if k!='files'}])
    dump(REC/'RECORD_INDEX.json',index)
    run(['git','add','--',*STAGE]);run(['git','diff','--cached','--check'])
    for p in run(['git','diff','--cached','--name-only']).splitlines():assert(R/p).stat().st_size<90*1024**2
    dump(O/'DELIVERY_PREPARED.json',dict(prepared=True,archive_member_sha_verified=True,models=0))

def publish():
    assert read(O/'DELIVERY_PREPARED.json')['prepared'];verified_sources()
    assert not(ROOT/'GIT_SYNC_CLAIM.json').exists()and not(ROOT/'GIT_SYNC_RESULT.json').exists(),'NO_SECOND_ROOT_PUSH'
    run(['git','diff','--cached','--check'])
    run(['git','commit','-m','Qualify causal finite-progress recovery references without requiring a full-goal route'])
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
    gh(['release','create',TAG,'--target',commit,'--title','V1000 finite-progress references: both saved states source-qualified, no physical models',
        '--notes','Original full-goal search failure reproduced and resolution matrix preserved. Direct finite-progress search qualifies both original causal saved states with unchanged geometry/progress gates and8negative cases. Zero models/integrations/navigation; actual tracking not yet qualified. Old failures retained.','--draft'])
    index=read(REC/'RECORD_INDEX.json');cloud=O/'cloud'
    assets=[p for p in cloud.iterdir()if p.is_file()]+[REC/'RECORD_INDEX.json']
    gh(['release','upload',TAG,*map(str,assets)])
    back=O/'readback';back.mkdir(exist_ok=False)
    for p in assets:
        gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)])
        assert sha(p)==sha(back/p.name)
    t.verifier()(back,index);gh(['release','edit',TAG,'--draft=false'])
    dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,commit=commit,all_asset_and_decompressed_member_sha_verified=True,
         original_scientific_outcome='TWO_CAUSAL_FINITE_PROGRESS_REFERENCES_SOURCE_QUALIFIED',models_during_delivery=0))
    receipts=O/'receipt_readback';receipts.mkdir(exist_ok=False)
    def receipt(p):
        gh(['release','upload',TAG,str(p)]);gh(['release','download',TAG,'--pattern',p.name,'--dir',str(receipts)])
        assert sha(p)==sha(receipts/p.name)
    for p in [REC/'GIT_SYNC_CLAIM.json',REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:receipt(p)
    catalog={x['path']:x for x in read(back/(index['archives'][0]['group']+'.INVENTORY.json'))['files']}
    excluded={x['path']:x for x in read(REC/'EXCLUDED_REBUILDABLE_FILES.json')['files']}
    deleted=[]
    roots=[R/'runs/v999_search_resolution_diagnosis',R/'runs/v1000_local_progress_reference']
    for root in roots:
        assert root.is_relative_to(R/'runs')and not root.is_symlink()
        size=0
        for p in t.packer(cloud)['walk'](root):
            rel=str(p.relative_to(R));row=catalog.get(rel,excluded.get(rel));assert row is not None,rel
            assert sha(p)==row['sha256']and p.stat().st_size==row['bytes'],rel;size+=p.stat().st_size
        for row in read(REC/'SYMLINKS_MANIFEST.json')['links']:
            p=R/row['path']
            if p.is_relative_to(root):
                assert p.is_symlink()and os.readlink(p)==row['target'];p.unlink()
        assert not any(p.is_symlink()for p in root.rglob('*')),'UNEXPECTED_SYMLINK_CLEANUP'
        shutil.rmtree(root);deleted.append(dict(path=str(root.relative_to(R)),bytes=size))
    for root in [cloud,back]:
        size=sum(p.stat().st_size for p in t.packer(cloud)['walk'](root));shutil.rmtree(root)
        deleted.append(dict(path=str(root.relative_to(R)),bytes=size))
    dump(REC/'CLEANUP_RESULT.json',dict(deleted=deleted,deleted_bytes=sum(x['bytes']for x in deleted),verified_remote_before_cleanup=True,models=0))
    receipt(REC/'CLEANUP_RESULT.json')
    dump(REC/'FINALIZED.json',dict(closed=True,scientific_status='TWO_CAUSAL_FINITE_PROGRESS_REFERENCES_SOURCE_QUALIFIED',
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
