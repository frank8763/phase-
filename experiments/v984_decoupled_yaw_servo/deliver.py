"""Bounded new source-stage sync, verified incremental archive and scoped cleanup."""
import fcntl,importlib.util,json,shutil,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v984_decoupled_yaw_servo';S=R/'runs/v983_saved_transient_diagnosis';REC=R/'records/nav2_v984_20261110'
spec=importlib.util.spec_from_file_location('v984_storage',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
TAG='phase-rpccr-rear-yaw-v984-20261110';GROUP='v984-source-saved-diagnosis-control-map'
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_DECOUPLED_YAW_V984_REPORT.md','experiments/v984_decoupled_yaw_servo','records/nav2_v984_20261110']
def gh(args):return t.run([str(t.GH),*args,'--repo',t.REPO],30)
def verify():
    assert t.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert freeze['model_authority']is False
    for rel,h in freeze['files'].items():assert t.sha(R/rel)==h,rel
    old=R/freeze['previous_physical_manifest'];assert t.sha(old)==freeze['previous_physical_manifest_sha256']
    for rel,h in json.loads(old.read_text())['files'].items():assert t.sha(R/rel)==h,rel
def prepare():
    assert not t.run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    assert json.loads((REC/'FINAL_ZERO_MODEL_AUDIT.json').read_text())['passed']
    with(O/'PREPARE_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    cloud=O/'cloud';cloud.mkdir();pack=t.packer(cloud)
    files=list(pack['walk'](C))+list(pack['walk'](REC))+[p for p in pack['walk'](O)if cloud not in p.parents]+[R/n for n in STAGE[:3]]
    # The raw native traces already have their original verified Release. Only
    # fresh analysis and its restore receipt are included in this new archive.
    files += [S/'DIAGNOSIS.json',S/'REMOTE_RESTORE_RECEIPT.json',S/'v982-two-fixed-recovery-components.INVENTORY.json']
    assert all(not p.is_symlink()and p.resolve().is_relative_to(R)for p in files)
    assert sum(p.stat().st_size for p in set(files))<64*1024**2
    group=pack['archive'](GROUP,files)
    index=dict(repository=t.REPO,release_tag=TAG,release_url=f'https://github.com/{t.REPO}/releases/tag/{TAG}',
        models=0,integrations=0,physical_ready=False,raw_not_duplicated=True,
        original_raw_index='records/nav2_v982_20261110/RECORD_INDEX.json',
        raw_restore_command='python3 -B experiments/v983_saved_transient_diagnosis/restore.py',
        archives=[{k:v for k,v in group.items()if k!='files'}])
    t.dump(REC/'RECORD_INDEX.json',index)
    t.run(['git','add','--',*STAGE]);t.run(['git','diff','--cached','--check'])
    for name in t.run(['git','diff','--cached','--name-only']).splitlines():assert(R/name).lstat().st_size<90*1024**2
    t.dump(O/'PREPARED.json',dict(passed=True,files=group['source_files'],models=0))
    print(json.dumps(dict(prepared=True,source_files=group['source_files'],archive_bytes=group['archive_bytes'])),flush=True)
def publish():
    assert(O/'PREPARED.json').exists()
    with(O/'PUBLISH_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0),f)
    t.run(['git','diff','--cached','--check'])
    t.run(['git','commit','-m','Add bounded rear-only yaw feedback candidate and saved actuator diagnosis'])
    commit=t.run(['git','rev-parse','HEAD']).strip();sync=dict(commit=commit,one_attempt=True,push_limit_s=30,remote_read_limit_s=5)
    with(REC/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    try:t.run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as e:sync['push_error']=repr(e)
    try:sync['remote_head']=t.run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync['remote_head_verified']=sync['remote_head']==commit
    except Exception as e:sync['verify_error']=repr(e)
    t.dump(REC/'GIT_SYNC_RESULT.json',sync)
    assert sync.get('remote_head_verified'),'SOURCE_REMOTE_UNKNOWN_KEEP_RAW_NO_PUSH_RETRY'
    index=json.loads((REC/'RECORD_INDEX.json').read_text())
    gh(['release','create',TAG,'--target',commit,'--title','Rear-only yaw feedback: source and control-map qualification',
        '--notes','Zero new models or integrations. Saved V982 evidence supports an actuator/body transient hypothesis. Bounded rear-only feedback passes algebraic mapping checks; closed-loop tracking and dynamic navigation remain unqualified. Original failures retained.','--draft'])
    assets=list((O/'cloud').iterdir())+[REC/'RECORD_INDEX.json'];gh(['release','upload',TAG,*map(str,assets)])
    back=O/'readback';back.mkdir()
    for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert t.sha(p)==t.sha(back/p.name)
    t.verifier()(back,index)
    catalog={r['path']:r for r in json.loads((back/(GROUP+'.INVENTORY.json')).read_text())['files']}
    original=json.loads((S/'REMOTE_RESTORE_RECEIPT.json').read_text());original_map={r['path']:r for r in original['files']}
    # Check every raw file against either its already-verified original member
    # hash or the newly downloaded/decompressed member inventory before deletion.
    for p in t.packer(O/'cloud')['walk'](S):
        row=original_map.get(str(p.relative_to(R)))or catalog.get(str(p.relative_to(R)))
        assert row and t.sha(p)==row['sha256'],'UNVERIFIED_CACHE '+str(p)
    gh(['release','edit',TAG,'--draft=false'])
    t.dump(REC/'REMOTE_VERIFIED.json',dict(passed=True,source_commit=commit,all_assets_and_decompressed_member_sha_verified=True,
         models=0,integrations=0,physical_ready=False,release_url=index['release_url']))
    receipts=O/'receipt_readback';receipts.mkdir()
    def receipt(p):
        gh(['release','upload',TAG,str(p)]);gh(['release','download',TAG,'--pattern',p.name,'--dir',str(receipts)]);assert t.sha(p)==t.sha(receipts/p.name)
    for p in [REC/'GIT_SYNC_RESULT.json',REC/'REMOTE_VERIFIED.json']:receipt(p)
    removed=[]
    for folder in [S,O/'cloud',back]:
        assert not folder.is_symlink()and folder.resolve().is_relative_to(R/'runs')
        size=sum(p.stat().st_size for p in t.packer(O)['walk'](folder));shutil.rmtree(folder);removed.append(dict(path=str(folder.relative_to(R)),bytes=size))
    # Keep only small operating receipts; the source/map qualification copies
    # reside in Git and every full result is in the verified incremental archive.
    for p in list(O.glob('*.json')):
        if p.name in {'PREPARED.json','PREPARE_CLAIM.json','PUBLISH_CLAIM.json'}:continue
        row=catalog.get(str(p.relative_to(R)));assert row and t.sha(p)==row['sha256']
        size=p.stat().st_size;p.unlink();removed.append(dict(path=str(p.relative_to(R)),bytes=size))
    t.dump(REC/'CLEANUP_RESULT.json',dict(removed=removed,deleted_bytes=sum(r['bytes']for r in removed),verified_remote_before_cleanup=True,models=0))
    receipt(REC/'CLEANUP_RESULT.json')
    t.dump(REC/'FINALIZED.json',dict(closed=True,status='SOURCE_AND_CONTROL_MAP_QUALIFIED_ONLY',models=0,integrations=0,
        remote_verified=True,raw_cache_cleaned=True,models_authorized=False,physical_ready=False,release_url=index['release_url']))
    receipt(REC/'FINALIZED.json');shutil.rmtree(receipts)
    print(json.dumps(dict(finalized=True,release_url=index['release_url'],deleted_bytes=sum(r['bytes']for r in removed),models=0)),flush=True)
if __name__=='__main__':
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    verify()
    try:{'prepare':prepare,'publish':publish}[sys.argv[1]]()
    except Exception as e:
        t.dump(O/(sys.argv[1].upper()+'_ERROR.json'),dict(error=repr(e),models=0,integrations=0,unverified_raw_retained=True,no_push_retry=True));raise
