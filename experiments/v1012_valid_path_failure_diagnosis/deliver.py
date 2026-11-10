"""Software/failure-diagnosis increment only; never repeat V1009's Git push."""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v1012_valid_path_failure_diagnosis';REC=R/'records/nav2_v1009_20261110'
TAG='phase-rpccr-valid-path-v1009-20261110';GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='frank8763/phase-'
RAW=[R/'runs/v1008_nav2_normal_action_software',R/'runs/v1010_valid_path_software']
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args):
    p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=30);assert p.returncode==0,(p.stdout+p.stderr)[-1200:];return p.stdout
def gh(args):return run([str(GH),*args,'--repo',REPO])
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    root=R/'runs/explicit_checker_20261110';assert read(root/'FINALIZED.json')['all_remote_source_member_SHA_verified']and not read(root/'APPROVAL.json')['models_authorized']
    assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    with(O/'INCREMENT_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),models=0,no_second_push=True),f)
    spec=importlib.util.spec_from_file_location('v1012_archive_helpers',R/'experiments/v978_source_only_closure/deliver.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    cloud=O/'cloud';cloud.mkdir(exist_ok=False);pack=h.packer(cloud);files=[]
    for folder in [*RAW,C,R/'experiments/v1008_nav2_normal_action_software',R/'experiments/v1010_valid_path_software',REC,R/'records/nav2_v1010_20261110',root]:
        files.extend(p for p in pack['walk'](folder)if'__pycache__'not in p.parts and p.suffix!='.lock')
    files.extend([O/'RESTORE_RECEIPT.json',O/'saved/COMMAND_OBSERVATION_FAULT.json',O/'saved/PROFILE_EXECUTION.json',R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'docs/RPCCR_VALID_PATH_NAVIGATION_V1009_REPORT.md',R/'docs/RPCCR_NAV2_VALID_PATH_V1008_V1010_REPORT.md'])
    assert sum(p.stat().st_size for p in set(files))*3<256*1024**2,'SMALL_INCREMENT_BUDGET_EXCEEDED'
    archive=pack['archive']('v1010-software-and-v1012-saved-diagnosis',files)
    index=dict(repository=REPO,release_tag=TAG,base_remote_source_commit='f013984143ef15df6ad3f0bf285188c0e8216871',
        scope='V1008 original/checker-only non-successes, V1010 full installed software success, V1012 saved-only V1009 diagnosis. No new physical model or replay.',
        models=0,new_integrations=0,no_second_git_push=True,archives=[{k:v for k,v in archive.items()if k!='files'}])
    ip=REC/'V1010_V1012_INCREMENT_INDEX.json';dump(ip,index);assets=[p for p in cloud.iterdir()if p.is_file()]+[ip]
    gh(['release','upload',TAG,*map(str,assets)]);back=O/'increment_readback';back.mkdir(exist_ok=False)
    for p in assets:
        gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert sha(p)==sha(back/p.name)
    h.verifier()(back,index);catalog={x['path']:x for x in read(back/(archive['group']+'.INVENTORY.json'))['files']}
    removed=[]
    for folder in RAW:
        rows=list(pack['walk'](folder))
        for p in rows:
            if'__pycache__'in p.parts:continue
            row=catalog[str(p.relative_to(R))];assert sha(p)==row['sha256']and p.stat().st_size==row['bytes']
        assert not any(p.is_symlink()for p in folder.rglob('*')),'UNEXPECTED_LINK_KEEP_RAW'
        size=sum(p.stat().st_size for p in rows);shutil.rmtree(folder);removed.append(dict(path=str(folder.relative_to(R)),bytes=size))
    # Restored diagnosis trace bytes are already in the fully verified V1009
    # physical archive. Verify unchanged selected hashes before clearing them.
    receipt=read(O/'RESTORE_RECEIPT.json')
    for item in receipt['selected']:
        p=R/item['path'];assert sha(p)==item['sha256']and p.stat().st_size==item['bytes']
    restored_size=sum(p.stat().st_size for p in pack['walk'](O/'saved'));shutil.rmtree(O/'saved');removed.append(dict(path=str((O/'saved').relative_to(R)),bytes=restored_size))
    for folder in [cloud,back,O/'readback']:
        if folder.exists():shutil.rmtree(folder)
    final=dict(closed=True,software_complete_action_passed=True,physical_navigation_NOT_PASSED_preserved=True,all_increment_part_source_member_SHA_remote_verified=True,
        deleted=removed,models=0,new_integrations=0,no_second_git_push=True,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}')
    fp=REC/'V1010_V1012_INCREMENT_FINALIZED.json';dump(fp,final);gh(['release','upload',TAG,str(fp)])
    paths=['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_VALID_PATH_NAVIGATION_V1009_REPORT.md','records/nav2_v1009_20261110','experiments/v1012_valid_path_failure_diagnosis']
    run(['git','add','--',*paths]);run(['git','diff','--cached','--check','--',*paths]);run(['git','commit','--only','-m','Diagnose fresh-state failure after two complete recovery profiles; archive software contrasts','--',*paths])
    print(json.dumps(final),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:dump(O/'INCREMENT_ERROR.json',dict(error=repr(e),models=0,no_second_push=True,unverified_raw_retained=True,no_automatic_retry=True));raise
