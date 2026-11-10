"""One new-root source push, immutable preparation archive; zero models."""
import json,shutil,subprocess,time
from pathlib import Path
from archive import walk,sha,package,verify
C=Path(__file__).resolve().parent;R=C.parents[1];ROOT=R/'runs/input_progress_night_20261110';O=R/'runs/v1018_input_progress_night';REC=R/'records/nav2_v1018_20261110'
GH=R/'tools/phase_storage_20261107/vendor/gh';TAG='phase-rpccr-exact-entry-night-v1018-20261110'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def run(args,cap=30):
    p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=cap);assert p.returncode==0,(p.stdout+p.stderr)[-1200:];return p.stdout

def main():
    assert not read(ROOT/'APPROVAL.json')['models_authorized']and not(ROOT/'ROUND_WINDOW.json').exists()
    assert not(ROOT/'GIT_SYNC_CLAIM.json').exists()and not(ROOT/'GIT_SYNC_RESULT.json').exists()
    for rel,h in read(C/'SOURCE_FREEZE.json')['files'].items():assert sha(R/rel)==h,rel
    for p in O.glob('*QUALIFICATION.json'):(REC/p.name).write_bytes(p.read_bytes())
    paths=[str(C.relative_to(R)),str(REC.relative_to(R)),'CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/RPCCR_INPUT_PROGRESS_V1015_V1018_ANALYSIS.md','experiments/v1016_saved_route_diagnosis','experiments/v1017_input_validated_progress','records/nav2_v1016_20261110','records/nav2_v1017_20261110']
    run(['git','add','--',*paths]);run(['git','diff','--cached','--check','--',*paths]);review=run(['git','diff','--cached','--stat','--',*paths]);dump(ROOT/'SOURCE_DIFF_REVIEW.json',dict(stat=review,paths=paths,models=0))
    run(['git','commit','--only','-m','Validate executable input prefixes inside bounded RP-CCR progress search','--',*paths]);head=run(['git','rev-parse','HEAD']).strip()
    with(ROOT/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),source_commit=head,push_s=30,remote_head_s=5,new_root=True),f)
    sync=dict(source_commit=head,push_attempted=True,remote_verified=False)
    try:
        run(['git','push','origin','HEAD:main'],30);remote=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0];sync.update(remote_head=remote,remote_verified=remote==head)
    except BaseException as error:sync['error']=repr(error)
    dump(ROOT/'GIT_SYNC_RESULT.json',sync);dump(REC/'SOURCE_SYNC_RESULT.json',sync)
    files=list(walk(C))+list(walk(REC))+[ROOT/'USER_AUTHORIZATION.json',ROOT/'HANDOFF.md',ROOT/'SUPERSEDED_UNSTARTED_DRAFT.json',ROOT/'REVIEW_PENDING.before',R/'docs/RPCCR_INPUT_PROGRESS_V1015_V1018_ANALYSIS.md']
    files+=list(walk(R/'experiments/v1016_saved_route_diagnosis'))+list(walk(R/'experiments/v1017_input_validated_progress'))+list(walk(R/'records/nav2_v1016_20261110'))+list(walk(R/'records/nav2_v1017_20261110'))+list(walk(R/'runs/v1017_input_validated_progress'))
    record,catalog=package(R,files,ROOT/'source_cloud','v1018-prelaunch-source-software')
    ip=REC/'PRELAUNCH_SOURCE_INDEX.json';dump(ip,dict(repository='frank8763/phase-',release_tag=TAG,source_sync=sync,models=0,archives=[record]))
    def gh(args):return run([str(GH),*args,'--repo','frank8763/phase-'],30)
    try:
        gh(['release','create',TAG,'--target','main','--title','V1018 executable-input progress search and three-route night','--notes','Preparation only. New independent hard model cutoff2026-11-11 09:00+08; old V1014/V1015 failed windows preserved; same original09:00 hard stop. Actual results added only after closure.'])
        assets=list((ROOT/'source_cloud').iterdir())+[ip];gh(['release','upload',TAG,*map(str,assets)])
        back=ROOT/'source_readback';back.mkdir(exist_ok=False)
        for p in assets:gh(['release','download',TAG,'--pattern',p.name,'--dir',str(back)]);assert sha(p)==sha(back/p.name)
        verify(record,catalog,lambda part:(back/part['name'],False))
        dump(REC/'SOURCE_REMOTE_VERIFIED.json',dict(passed=True,all_source_and_decompressed_member_sha=True,models=0))
        shutil.rmtree(ROOT/'source_cloud');shutil.rmtree(back)
    except BaseException as error:dump(ROOT/'SOURCE_REMOTE_PENDING.json',dict(error=repr(error),models=0,unverified_evidence_retained=True,no_push_retry=True))
    print(json.dumps(dict(source_commit=head,source_push_remote_verified=sync['remote_verified'],source_archive_remote_verified=(REC/'SOURCE_REMOTE_VERIFIED.json').exists(),models=0)),flush=True)
if __name__=='__main__':main()
