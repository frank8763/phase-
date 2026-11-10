"""Closed V991 diagnosis supplement; no model work and no second Git push."""
import fcntl,importlib.util,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v992_coordinated_response_diagnosis'
REC=R/'records/nav2_v991_20261110';B=R/'runs/v991_coordinated_components'
spec=importlib.util.spec_from_file_location('v992_storage',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
TAG='phase-rpccr-coordinated-components-v991-20261110';GROUP='v992-coordinated-actual-response-diagnosis'
STAGE=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_COORDINATED_COMPONENTS_V991_REPORT.md',
       'experiments/v992_coordinated_response_diagnosis',
       'records/nav2_v991_20261110/V992_RESPONSE_DIAGNOSIS.json',
       'records/nav2_v991_20261110/V992_POSTMORTEM_INDEX.json',
       'records/nav2_v991_20261110/V992_REMOTE_VERIFIED.json',
       'records/nav2_v991_20261110/V992_CLEANUP.json']
def gh(args):return t.run([str(t.GH),*args,'--repo',t.REPO],30)

def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert t.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC/'FINALIZED.json').read_text())['remote_verified']
    assert json.loads((REC/'GIT_SYNC_RESULT.json').read_text())['one_attempt']
    for name,h in json.loads((R/'experiments/v991_coordinated_components/SOURCE_FREEZE.json').read_text())['files'].items():
        assert t.sha(R/name)==h,name
    assert not t.run(['git','diff','--cached','--name-only']).strip()
    with(O/'DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,no_git_push=True),f)
    original_index=json.loads((REC/'RECORD_INDEX.json').read_text());original_group=original_index['archives'][0]
    back=O/'readback';back.mkdir()
    inventory=original_group['group']+'.INVENTORY.json'
    gh(['release','download',TAG,'--pattern',inventory,'--dir',str(back)])
    catalog={x['path']:x for x in json.loads((back/inventory).read_text())['files']}
    for row in json.loads((O/'LOCAL_SAVED_COPY.json').read_text())['files']:
        expected=catalog[row['original']]
        assert t.sha(R/row['path'])==expected['sha256']==row['sha256']
        assert (R/row['path']).stat().st_size==expected['bytes']==row['bytes']
    t.dump(O/'ORIGINAL_MEMBER_SHA_VERIFIED.json',dict(passed=True,models=0,all_selected_copies_match_original_remote_members=True,
        original_archive_sha256=original_group['archive_sha256'],original_remote_finalized=str((REC/'FINALIZED.json').relative_to(R))))
    cloud=O/'cloud';cloud.mkdir();pack=t.packer(cloud)
    files=list(pack['walk'](C))+[O/n for n in ['DIAGNOSIS.json','LOCAL_SAVED_COPY.json','ORIGINAL_MEMBER_SHA_VERIFIED.json','DELIVERY_CLAIM.json']]
    files+=[R/n for n in STAGE[:3]]+[REC/'V992_RESPONSE_DIAGNOSIS.json']
    files+=[B/n for n in ['campaign.console','finalize.console','USER_APPROVAL.json','COMPLETION.json','ROUND_WINDOW.json']]
    group=pack['archive'](GROUP,files)
    index=dict(repository=t.REPO,release_tag=TAG,models=0,integrations=0,no_git_push=True,
        physical_outcome='V991_NOT_PASSED',raw_trace_not_duplicated=True,
        original_raw_index='records/nav2_v991_20261110/RECORD_INDEX.json',archives=[{k:v for k,v in group.items()if k!='files'}])
    ix=REC/'V992_POSTMORTEM_INDEX.json';t.dump(ix,index);assets=list(cloud.iterdir())+[ix]
    gh(['release','upload',TAG,*map(str,assets)])
    for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert t.sha(p)==t.sha(back/p.name)
    t.verifier()(back,index)
    verified=REC/'V992_REMOTE_VERIFIED.json';t.dump(verified,dict(passed=True,models=0,integrations=0,
        source_and_all_asset_and_member_sha_verified=True,original_member_sha_for_selected_copies_verified=True,
        no_git_push=True,physical_outcome='V991_NOT_PASSED',no_new_model_authority=True))
    gh(['release','upload',TAG,str(verified)]);gh(['release','download',TAG,'--pattern',verified.name,'--dir',str(back)])
    assert t.sha(verified)==t.sha(back/verified.name)
    assert not O.is_symlink()and O.resolve().is_relative_to(R/'runs')
    for p in O.rglob('*'):assert not p.is_symlink()and p.resolve().is_relative_to(O)
    manifest=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=t.sha(p))for p in pack['walk'](O)]
    for row in manifest:assert t.sha(R/row['path'])==row['sha256']
    removed=sum(x['bytes']for x in manifest);shutil.rmtree(O)
    cleanup=REC/'V992_CLEANUP.json';t.dump(cleanup,dict(deleted_cache_bytes=removed,files=manifest,models=0,
        original_raw_in_verified_release=True,new_diagnosis_remote_verified=True,no_git_push=True))
    tmp=B/'v992_receipt_readback';tmp.mkdir()
    gh(['release','upload',TAG,str(cleanup)]);gh(['release','download',TAG,'--pattern',cleanup.name,'--dir',str(tmp)])
    assert t.sha(cleanup)==t.sha(tmp/cleanup.name);shutil.rmtree(tmp)
    t.run(['git','add','--',*STAGE]);t.run(['git','diff','--cached','--check'])
    for n in t.run(['git','diff','--cached','--name-only']).splitlines():assert(R/n).lstat().st_size<90*1024**2
    print(json.dumps(dict(remote_verified=True,models=0,no_git_push=True,deleted_cache_bytes=removed,staged_for_review=True)))
if __name__=='__main__':main()
