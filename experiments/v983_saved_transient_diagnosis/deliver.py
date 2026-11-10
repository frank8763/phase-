"""Upload new diagnosis only; raw traces remain in the original V982 archive."""
import fcntl,importlib.util,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v983_saved_transient_diagnosis';REC=R/'records/nav2_v982_20261110'
spec=importlib.util.spec_from_file_location('v983_no_push_transport',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
TAG='phase-rpccr-precise-recovery-v982-20261110'
def gh(args):return t.run([str(t.GH),*args,'--repo',t.REPO],30)
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert t.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC/'FINALIZED.json').read_text())['remote_verified']
    with(O/'DELIVERY_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,no_git_push=True),f)
    cloud=O/'cloud';cloud.mkdir();pack=t.packer(cloud)
    new_names=['DIAGNOSIS.json','REMOTE_RESTORE_RECEIPT.json','COPIED_SAVED_INPUTS.json','ANALYSIS_PREPARATION_FAILURES.json','V982_SAVED_TRACKING.png','V982_SAVED_TRACKING.pdf','DELIVERY_CLAIM.json']
    files=[O/name for name in new_names]+list(pack['walk'](C))+[REC/'CLOSED_LEDGER.json',REC/'SAVED_TRANSIENT_DIAGNOSIS.json',R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'docs/RPCCR_PRECISE_RECOVERY_V982_REPORT.md']
    for name in ['finalize.console','campaign.console','LEDGER.json','USER_APPROVAL.json']:
        files.append(R/'runs/v982_precise_recovery_gate'/name)
    group=pack['archive']('v983-saved-transient-postmortem',files)
    index=dict(repository=t.REPO,release_tag=TAG,models=0,integrations=0,no_git_push=True,
               original_raw_trace_index='records/nav2_v982_20261110/RECORD_INDEX.json',raw_trace_not_duplicated=True,
               restore_command='python3 -B experiments/v983_saved_transient_diagnosis/restore.py',
               analyze_command='python3 -B experiments/v983_saved_transient_diagnosis/analyze.py',
               archives=[{k:v for k,v in group.items()if k!='files'}])
    ix=REC/'TRANSIENT_POSTMORTEM_INDEX.json';t.dump(ix,index)
    assets=[p for p in cloud.iterdir()if p.is_file()]+[ix];gh(['release','upload',TAG,*map(str,assets)])
    back=O/'readback';back.mkdir()
    for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert t.sha(p)==t.sha(back/p.name)
    t.verifier()(back,index)
    verified=REC/'TRANSIENT_POSTMORTEM_REMOTE_VERIFIED.json';t.dump(verified,dict(passed=True,all_asset_and_member_sha_verified=True,models=0,integrations=0,no_git_push=True,old_physical_outcome='V982_NOT_PASSED'))
    gh(['release','upload',TAG,str(verified)]);gh(['release','download',TAG,'--pattern',verified.name,'--dir',str(back)]);assert t.sha(verified)==t.sha(back/verified.name)
    # Each restored original input already has its own verified source archive;
    # no duplicate physics archive is created for this zero-model diagnosis.
    original=json.loads((O/'REMOTE_RESTORE_RECEIPT.json').read_text())
    for row in original['files']:assert t.sha(R/row['path'])==row['sha256']
    removed=sum(p.stat().st_size for p in pack['walk'](O));shutil.rmtree(O)
    cleanup=REC/'TRANSIENT_POSTMORTEM_CLEANUP.json';t.dump(cleanup,dict(deleted_bytes=removed,raw_already_in_original_verified_archive=True,new_analysis_remote_member_sha_verified=True,models=0))
    receipt=R/'runs/v982_precise_recovery_gate/postmortem_receipt_readback';receipt.mkdir()
    gh(['release','upload',TAG,str(cleanup)]);gh(['release','download',TAG,'--pattern',cleanup.name,'--dir',str(receipt)]);assert t.sha(cleanup)==t.sha(receipt/cleanup.name);shutil.rmtree(receipt)
    print(json.dumps(dict(remote_verified=True,deleted_bytes=removed,new_models=0,no_second_push=True)))
if __name__=='__main__':main()
