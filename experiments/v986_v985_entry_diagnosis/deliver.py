"""Incremental diagnosis Release only; never retry V985 Git push or models."""
import fcntl,importlib.util,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v986_v985_entry_diagnosis';REC=R/'records/nav2_v985_20261110'
spec=importlib.util.spec_from_file_location('v986_no_push_storage',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
TAG='phase-rpccr-rear-yaw-components-v985-20261110';GROUP='v986-v985-startup-diagnosis'
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_REAR_YAW_COMPONENTS_V985_REPORT.md','docs/RPCCR_V985_DIAGNOSIS_AND_NEXT_PLAN.md','experiments/v986_v985_entry_diagnosis','records/nav2_v985_20261110']
def gh(args):return t.run([str(t.GH),*args,'--repo',t.REPO],30)
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert t.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC/'FINALIZED.json').read_text())['remote_verified']
    assert json.loads((O/'DIAGNOSIS.json').read_text())['no_new_physical_authority']
    frozen=json.loads((R/'experiments/v985_rear_yaw_components/SOURCE_FREEZE.json').read_text())
    for n,h in frozen['files'].items():assert t.sha(R/n)==h,n
    assert not t.run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    with(O/'DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,no_git_push=True),f)
    cloud=O/'cloud';cloud.mkdir();pack=t.packer(cloud)
    files=list(pack['walk'](C))+[O/n for n in ['DIAGNOSIS.json','PARENT_WAIT_REPRODUCTION.json','RESTORE_RECEIPT.json','DELIVERY_CLAIM.json']]
    files += [R/n for n in STAGE[:4]]+[REC/'V986_STARTUP_DIAGNOSIS.json',REC/'V986_PARENT_WAIT_REPRODUCTION.json']
    for n in ['campaign.console','finalize.console','USER_APPROVAL.json','COMPLETION.json']:
        p=R/'runs/v985_rear_yaw_components'/n
        if p.exists():files.append(p)
    group=pack['archive'](GROUP,files)
    index=dict(repository=t.REPO,release_tag=TAG,models=0,integrations=0,no_git_push=True,
        original_raw_index='records/nav2_v985_20261110/RECORD_INDEX.json',raw_trace_not_duplicated=True,
        archives=[{k:v for k,v in group.items()if k!='files'}])
    ix=REC/'V986_POSTMORTEM_INDEX.json';t.dump(ix,index)
    assets=list(cloud.iterdir())+[ix];gh(['release','upload',TAG,*map(str,assets)])
    back=O/'readback';back.mkdir()
    for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert t.sha(p)==t.sha(back/p.name)
    t.verifier()(back,index)
    verified=REC/'V986_REMOTE_VERIFIED.json';t.dump(verified,dict(passed=True,all_asset_and_member_sha_verified=True,
        models=0,integrations=0,no_git_push=True,original_outcome='V985_NOT_PASSED',next_plan_only=True))
    gh(['release','upload',TAG,str(verified)]);gh(['release','download',TAG,'--pattern',verified.name,'--dir',str(back)]);assert t.sha(verified)==t.sha(back/verified.name)
    for row in json.loads((O/'RESTORE_RECEIPT.json').read_text())['files']:assert t.sha(R/row['path'])==row['sha256']
    removed=sum(p.stat().st_size for p in pack['walk'](O));shutil.rmtree(O)
    cleanup=REC/'V986_CLEANUP.json';t.dump(cleanup,dict(deleted_cache_bytes=removed,models=0,
        original_metadata_in_verified_v985_release=True,new_analysis_remote_member_sha_verified=True,no_git_push=True))
    tmp=R/'runs/v985_rear_yaw_components/v986_receipt_readback';tmp.mkdir()
    gh(['release','upload',TAG,str(cleanup)]);gh(['release','download',TAG,'--pattern',cleanup.name,'--dir',str(tmp)]);assert t.sha(cleanup)==t.sha(tmp/cleanup.name);shutil.rmtree(tmp)
    t.run(['git','add','--',*STAGE]);t.run(['git','diff','--cached','--check'])
    for name in t.run(['git','diff','--cached','--name-only']).splitlines():assert(R/name).lstat().st_size<90*1024**2
    t.run(['git','commit','-m','Diagnose pre-ARM restore timeout and record bounded next experiment plan'])
    print(json.dumps(dict(remote_verified=True,deleted_cache_bytes=removed,models=0,no_git_push=True)))
if __name__=='__main__':main()
