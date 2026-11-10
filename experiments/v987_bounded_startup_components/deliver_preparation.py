"""Preparation snapshot only: Release readback/local commit, no Git push/model."""
import fcntl,importlib.util,json,shutil,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v987_bounded_startup_components';REC=R/'records/nav2_v987_20261110'
spec=importlib.util.spec_from_file_location('v987_preparation_storage',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
TAG='phase-rpccr-bounded-startup-v987-preparation-20261110';GROUP='v987-rear-yaw-component-preparation'
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_BOUNDED_STARTUP_V987_REPORT.md','experiments/v987_bounded_startup_components','records/nav2_v987_20261110']
def gh(args):return t.run([str(t.GH),*args,'--repo',t.REPO],30)
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert t.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC/'PREPARATION_AUDIT.json').read_text())['source_qualification_passed']
    frozen=json.loads((C/'SOURCE_FREEZE.json').read_text())
    for name,h in frozen['files'].items():assert t.sha(R/name)==h,name
    assert not(O/'ROUND_WINDOW.json').exists()and not(REC/'GIT_SYNC_CLAIM.json').exists()
    assert not t.run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    with(O/'PREPARATION_DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,git_pushes=0),f)
    cloud=O/'preparation_cloud';cloud.mkdir();pack=t.packer(cloud)
    files=[p for p in pack['walk'](O)if cloud not in p.parents]+list(pack['walk'](C))+list(pack['walk'](REC))+list(pack['walk'](R/'runs/v858_nav2_verified/v987_software'))+[R/n for n in STAGE[:3]]
    assert all(not p.is_symlink()and p.resolve().is_relative_to(R)for p in files)
    assert sum(p.stat().st_size for p in set(files))<2*1024**3
    group=pack['archive'](GROUP,files)
    index=dict(repository=t.REPO,release_tag=TAG,release_url=f'https://github.com/{t.REPO}/releases/tag/{TAG}',
        models=0,integrations=0,git_pushes=0,source_in_archive=True,physical_ready=False,
        archives=[{k:v for k,v in group.items()if k!='files'}])
    t.dump(REC/'PREPARATION_RECORD_INDEX.json',index)
    t.run(['git','add','--',*STAGE]);t.run(['git','diff','--cached','--check'])
    for name in t.run(['git','diff','--cached','--name-only']).splitlines():assert(R/name).lstat().st_size<90*1024**2
    # The archive contains the new source. Target the last verified remote
    # commit because this physical batch's sole push is reserved until closure.
    base=json.loads((R/'records/nav2_v985_20261110/GIT_SYNC_RESULT.json').read_text())
    assert base['remote_head_verified']
    gh(['release','create',TAG,'--target',base['commit'],'--title','V984 rear-yaw entry with bounded startup: preparation only',
        '--notes','Zero physical models/integrations. Bounded180s startup/350s task clocks; two original saved states, exact old/new adapter switch and independent actuator evidence audit, actual installed RPP with nonphysical peers. New source is in the verified archive; no physical qualification claimed.','--draft'])
    assets=list(cloud.iterdir())+[REC/'PREPARATION_RECORD_INDEX.json'];gh(['release','upload',TAG,*map(str,assets)])
    back=O/'preparation_readback';back.mkdir()
    for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert t.sha(p)==t.sha(back/p.name)
    t.verifier()(back,index)
    catalog={r['path']:r for r in json.loads((back/(GROUP+'.INVENTORY.json')).read_text())['files']}
    gh(['release','edit',TAG,'--draft=false'])
    receipts=O/'preparation_receipts';receipts.mkdir()
    def receipt(p):
        gh(['release','upload',TAG,str(p)]);gh(['release','download',TAG,'--pattern',p.name,'--dir',str(receipts)]);assert t.sha(p)==t.sha(receipts/p.name)
    removed=[]
    candidates=[p for p in O.iterdir()if p.is_dir()and p not in [cloud,back,receipts]]
    assert all(p.name.startswith(('case','binding_fixture','advanced_origin_fixture','software_case','budget_','restore_','ros_failure','parent_exception','hung_worker','root_deadline','foreign_stop','prearm_','armed_','clock_'))for p in candidates)
    candidates.append(R/'runs/v858_nav2_verified/v987_software')
    for folder in candidates:
        for p in pack['walk'](folder):
            row=catalog[str(p.relative_to(R))];assert t.sha(p)==row['sha256']
        assert not folder.is_symlink();size=sum(p.stat().st_size for p in pack['walk'](folder));shutil.rmtree(folder)
        removed.append(dict(path=str(folder.relative_to(R)),bytes=size))
    for folder in [cloud,back]:
        size=sum(p.stat().st_size for p in pack['walk'](folder));shutil.rmtree(folder);removed.append(dict(path=str(folder.relative_to(R)),bytes=size))
    result=dict(passed=True,remote_verified=True,all_asset_and_member_sha_verified=True,models=0,integrations=0,
        physical_ready=False,models_authorized=False,git_pushes=0,final_batch_push_reserved=True,
        release_url=index['release_url'],source_in_release_archive=True,removed=removed,deleted_cache_bytes=sum(r['bytes']for r in removed))
    t.dump(REC/'PREPARATION_REMOTE_VERIFIED.json',result);receipt(REC/'PREPARATION_REMOTE_VERIFIED.json');shutil.rmtree(receipts)
    state=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());state['v987_preparation']['storage']=result;t.dump(R/'CURRENT_EXPERIMENT.json',state)
    t.run(['git','add','--',*STAGE]);t.run(['git','diff','--cached','--check'])
    t.run(['git','commit','-m','Qualify bounded startup clocks, restore STOP and failure evidence before two recovery components'])
    print(json.dumps(dict(preparation_remote_verified=True,git_pushes=0,models=0,release_url=index['release_url'],deleted_cache_bytes=result['deleted_cache_bytes'])),flush=True)
if __name__=='__main__':main()
