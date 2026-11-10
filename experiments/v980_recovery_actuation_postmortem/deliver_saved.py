"""Supplement the same closed release, no Git push or model retry."""
import fcntl,importlib.util,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v980_recovery_actuation_postmortem';REC=R/'records/nav2_v979_20261110'
spec=importlib.util.spec_from_file_location('v980_saved_transport',R/'experiments/v978_source_only_closure/deliver.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
TAG='phase-rpccr-state-recovery-v979-20261110'
def gh(args):return t.gh(args) if False else t.run([str(t.GH),*args,'--repo',t.REPO],30)
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert t.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC/'FINALIZED.json').read_text())['remote_verified']
    with(O/'DELIVERY_CLAIM.json').open('x')as stream:json.dump(dict(at=time.time(),models=0,no_git_push=True),stream)
    (REC/'SAVED_COMMAND_POSTMORTEM.json').write_bytes((O/'DIAGNOSIS.json').read_bytes())
    cloud=O/'cloud';cloud.mkdir(exist_ok=False);pack=t.packer(cloud)
    files=[p for p in pack['walk'](O)if cloud not in p.parents]+list(pack['walk'](C))
    files += [REC/'POSTMORTEM_ACCOUNTING.json',REC/'SAVED_COMMAND_POSTMORTEM.json',R/'docs/RPCCR_STATE_RECOVERY_PHYSICAL_V979_REPORT.md',R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md']
    for name in ['finalize.console','campaign.console']:
        p=R/'runs/v979_state_recovery_physical'/name
        if p.exists():files.append(p)
    group=pack['archive']('v980-closed-saved-command-diagnosis',files)
    index=dict(repository=t.REPO,release_tag=TAG,models=0,integrations=0,old_outcome_unchanged='V979_NOT_PASSED',
               archives=[{k:v for k,v in group.items()if k!='files'}])
    ix=REC/'POSTMORTEM_INDEX.json';t.dump(ix,index);assets=[p for p in cloud.iterdir()if p.is_file()]+[ix]
    gh(['release','upload',TAG,*map(str,assets)])
    readback=O/'readback';readback.mkdir(exist_ok=False)
    for path in assets:gh(['release','download',TAG,'--pattern',path.name,'--dir',str(readback)]);assert t.sha(path)==t.sha(readback/path.name)
    t.verifier()(readback,index)
    receipt=REC/'POSTMORTEM_REMOTE_VERIFIED.json';t.dump(receipt,dict(passed=True,source_and_member_sha_verified=True,models=0,integrations=0,no_git_push_retry=True))
    gh(['release','upload',TAG,str(receipt)]);gh(['release','download',TAG,'--pattern',receipt.name,'--dir',str(readback)]);assert t.sha(receipt)==t.sha(readback/receipt.name)
    old_catalog={x['path']:x for x in json.loads((O/'v979-fixed-recovery-physical-gate.INVENTORY.json').read_text())['files']}
    removed=0;oldroot=R/'runs/v979_state_recovery_physical'
    for folder in list(oldroot.iterdir()):
        if not folder.is_dir()or folder.is_symlink()or not(folder.name.startswith('case')or folder.name.endswith('_ros_logs')):continue
        for path in pack['walk'](folder):
            record=old_catalog[str(path.relative_to(R))];assert t.sha(path)==record['sha256'];removed+=path.stat().st_size
        shutil.rmtree(folder)
    for folder in [cloud,readback]:
        removed+=sum(p.stat().st_size for p in pack['walk'](folder));shutil.rmtree(folder)
    t.dump(REC/'POSTMORTEM_CLEANUP.json',dict(deleted_bytes=removed,verified_remote_before_cleanup=True,models=0))
    print(json.dumps(dict(remote_verified=True,deleted_bytes=removed,new_models=0,no_push_retry=True)),flush=True)
if __name__=='__main__':main()
