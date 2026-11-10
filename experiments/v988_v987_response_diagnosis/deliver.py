"""Verified supplemental response diagnosis; no second V987 push or models."""
import fcntl,importlib.util,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v988_v987_response_diagnosis';REC=R/'records/nav2_v987_20261110'
spec=importlib.util.spec_from_file_location('v988_storage',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
TAG='phase-rpccr-bounded-startup-v987-20261110';GROUP='v988-v987-saved-response-diagnosis'
def gh(args):return t.run([str(t.GH),*args,'--repo',t.REPO],30)
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert t.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC/'FINALIZED.json').read_text())['remote_verified']
    frozen=json.loads((R/'experiments/v987_bounded_startup_components/SOURCE_FREEZE.json').read_text())
    for n,h in frozen['files'].items():assert t.sha(R/n)==h,n
    assert not t.run(['git','diff','--cached','--name-only']).strip()
    with(O/'DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,no_git_push=True),f)
    cloud=O/'cloud';cloud.mkdir();pack=t.packer(cloud)
    files=list(pack['walk'](C))+[O/n for n in ['DIAGNOSIS.json','RESTORE_RECEIPT.json','DELIVERY_CLAIM.json']]
    stage=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_BOUNDED_STARTUP_V987_REPORT.md','experiments/v988_v987_response_diagnosis','records/nav2_v987_20261110']
    files+=[R/n for n in stage[:3]]+[REC/'V988_RESPONSE_DIAGNOSIS.json']
    files+=[R/'runs/v987_bounded_startup_components'/n for n in ['campaign.console','finalize.console','USER_APPROVAL.json','COMPLETION.json']]
    group=pack['archive'](GROUP,files)
    index=dict(repository=t.REPO,release_tag=TAG,models=0,integrations=0,no_git_push=True,raw_trace_not_duplicated=True,
        original_raw_index='records/nav2_v987_20261110/RECORD_INDEX.json',archives=[{k:v for k,v in group.items()if k!='files'}])
    ix=REC/'V988_POSTMORTEM_INDEX.json';t.dump(ix,index);assets=list(cloud.iterdir())+[ix]
    gh(['release','upload',TAG,*map(str,assets)])
    back=O/'readback';back.mkdir()
    for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert t.sha(p)==t.sha(back/p.name)
    t.verifier()(back,index)
    verified=REC/'V988_REMOTE_VERIFIED.json';t.dump(verified,dict(passed=True,all_asset_and_member_sha_verified=True,models=0,integrations=0,
        no_git_push=True,original_physical_outcome='V987_NOT_PASSED'))
    gh(['release','upload',TAG,str(verified)]);gh(['release','download',TAG,'--pattern',verified.name,'--dir',str(back)]);assert t.sha(verified)==t.sha(back/verified.name)
    for row in json.loads((O/'RESTORE_RECEIPT.json').read_text())['files']:assert t.sha(R/row['path'])==row['sha256']
    removed=sum(p.stat().st_size for p in pack['walk'](O));shutil.rmtree(O)
    cleanup=REC/'V988_CLEANUP.json';t.dump(cleanup,dict(deleted_cache_bytes=removed,models=0,no_git_push=True,
        original_raw_in_verified_v987_release=True,new_analysis_remote_member_sha_verified=True))
    tmp=R/'runs/v987_bounded_startup_components/v988_receipt_readback';tmp.mkdir()
    gh(['release','upload',TAG,str(cleanup)]);gh(['release','download',TAG,'--pattern',cleanup.name,'--dir',str(tmp)]);assert t.sha(cleanup)==t.sha(tmp/cleanup.name);shutil.rmtree(tmp)
    t.run(['git','add','--',*stage]);t.run(['git','diff','--cached','--check'])
    for name in t.run(['git','diff','--cached','--name-only']).splitlines():assert(R/name).lstat().st_size<90*1024**2
    t.run(['git','commit','-m','Record actual rear-yaw response, complete stop tracking failure and exact accounting'])
    print(json.dumps(dict(remote_verified=True,models=0,no_git_push=True,deleted_cache_bytes=removed)))
if __name__=='__main__':main()
