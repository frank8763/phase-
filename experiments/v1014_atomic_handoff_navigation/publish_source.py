"""One bounded source push and immutable prelaunch software/source evidence."""
import json,shutil,subprocess,time
from pathlib import Path
from archive import walk,sha,package,verify
C=Path(__file__).resolve().parent;R=C.parents[1];ROOT=R/'runs/atomic_handoff_night_20261110';O=R/'runs/v1014_atomic_handoff_navigation';REC=R/'records/nav2_v1014_20261110'
GH=R/'tools/phase_storage_20261107/vendor/gh';TAG='phase-rpccr-atomic-handoff-night-v1014-20261110'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def run(args,cap=30):
    p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=cap);assert p.returncode==0,(p.stdout+p.stderr)[-1200:];return p.stdout
def main():
    assert not read(ROOT/'APPROVAL.json')['models_authorized']
    assert not(ROOT/'GIT_SYNC_CLAIM.json').exists()and not(ROOT/'GIT_SYNC_RESULT.json').exists()
    for rel,digest in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/rel)==digest,rel
    REC.mkdir(exist_ok=True)
    for p in O.glob('*QUALIFICATION.json'):(REC/p.name).write_bytes(p.read_bytes())
    (REC/'USER_AUTHORIZATION.json').write_bytes((ROOT/'USER_AUTHORIZATION.json').read_bytes())
    paths=[str(C.relative_to(R)),'experiments/v1013_atomic_handoff_software','records/nav2_v1013_20261110',str(REC.relative_to(R)),'CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_ATOMIC_HANDOFF_NIGHT_20261110_PLAN.md']
    run(['git','add','--',*paths]);run(['git','diff','--cached','--check','--',*paths]);review=run(['git','diff','--cached','--stat','--',*paths]);dump(ROOT/'SOURCE_DIFF_REVIEW.json',dict(stat=review,paths=paths,models=0))
    run(['git','commit','--only','-m','Freeze atomic stopped handoff and bounded offline three-route/fixed24 night','--',*paths]);head=run(['git','rev-parse','HEAD']).strip()
    with(ROOT/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),source_commit=head,push_s=30,remote_head_s=5),f)
    sync=dict(source_commit=head,push_attempted=True,remote_verified=False)
    try:run(['git','push','origin','HEAD:main'],30);remote=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync.update(remote_head=remote,remote_verified=remote==head)
    except BaseException as error:sync['error']=repr(error)
    dump(ROOT/'GIT_SYNC_RESULT.json',sync);dump(REC/'SOURCE_SYNC_RESULT.json',sync)
    files=[]
    for folder in [C,R/'experiments/v1013_atomic_handoff_software',R/'runs/v1013_atomic_handoff_software/saved',REC,R/'records/nav2_v1013_20261110']:
        files.extend(walk(folder))
    files.extend([C/'SOURCE_FREEZE.json',ROOT/'USER_AUTHORIZATION.json',ROOT/'HANDOFF.md',R/'runs/v1013_atomic_handoff_software/RESTORE_RECEIPT.json'])
    record,catalog=package(R,files,ROOT/'source_cloud','v1014-prelaunch-source-software')
    index=dict(repository='frank8763/phase-',release_tag=TAG,source_sync=sync,models=0,integrations=0,archives=[record]);ip=REC/'PRELAUNCH_SOURCE_INDEX.json';dump(ip,index)
    def gh(args):return run([str(GH),*args,'--repo','frank8763/phase-'],30)
    try:
        gh(['release','create',TAG,'--target','main','--title','V1014 atomic stopped handoff offline night','--notes','Frozen source/software qualification first; actual results only in later closed-night evidence. Fixed cutoff2026-11-11 08:00+08.'])
        assets=list((ROOT/'source_cloud').iterdir())+[ip];gh(['release','upload',TAG,*map(str,assets)])
        back=ROOT/'source_readback';back.mkdir(exist_ok=False)
        for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert sha(p)==sha(back/p.name)
        verify(record,catalog,lambda part:(back/part['name'],False))
        dump(REC/'SOURCE_REMOTE_VERIFIED.json',dict(passed=True,all_source_and_decompressed_member_sha=True,models=0))
        # Preparation fixtures have no runtime role. Preserve qualifications and
        # verified restore indices; clear only these archived original bytes.
        saved=R/'runs/v1013_atomic_handoff_software/saved';mapping={x['path']:x for x in catalog}
        for p in walk(saved):assert sha(p)==mapping[str(p.relative_to(R))]['sha256']
        shutil.rmtree(saved)
        for p in [ROOT/'source_cloud',back,R/'runs/v1013_atomic_handoff_software/readback']:
            if p.exists():shutil.rmtree(p)
    except BaseException as error:dump(ROOT/'SOURCE_REMOTE_PENDING.json',dict(error=repr(error),models=0,unverified_source_evidence_retained=True,no_push_retry=True))
    print(json.dumps(dict(source_commit=head,source_push_remote_verified=sync['remote_verified'],source_archive_remote_verified=(REC/'SOURCE_REMOTE_VERIFIED.json').exists(),models=0)),flush=True)
if __name__=='__main__':main()
