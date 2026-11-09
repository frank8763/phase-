"""New media-only publication; no old scientific sync retry or new simulation."""
import fcntl
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent
OUT=ROOT/'runs/report_materials_v945_20261109';VIDEO=OUT/'render02'
REC=ROOT/'records/nav2_v945_media_20261109'
GH=ROOT/'tools/phase_storage_20261107/vendor/gh'
REPO='frank8763/phase-';TAG='phase-rpccr-v945-path-replay-20261109'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def run(command,limit=30):
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=limit)
    assert p.returncode==0,(p.stderr or p.stdout)[-1200:]
    return p.stdout


def gh(args,limit=120):return run([str(GH),*args,'--repo',REPO],limit)


def main():
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sha(ROOT/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert json.loads((REC/'MEDIA_QA.json').read_text())['passed']
    with(REC/'PUBLICATION_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),stage='NEW_SAVED_MEDIA_ONLY',new_integrations=0),f)
    for name in ['RENDER_LAUNCH.json','RENDER_LAUNCH02.json','RENDER_STOP_REASON.json']:(REC/name).write_bytes((OUT/name).read_bytes())
    (REC/'final_with_paths.png').write_bytes((VIDEO/'final.png').read_bytes())
    media=[*sorted(VIDEO.glob('*.mp4')),REC/'v945_paths_and_last2m.png',REC/'final_with_paths.png',
           *[REC/name for name in ['MEDIA_QA.json','RENDER_PROVENANCE.json','PATH_VISUALIZATION.json',
                                 'LAST_WINDOW_CONTROL_SOURCES.json','RENDER_LAUNCH.json','RENDER_LAUNCH02.json','RENDER_STOP_REASON.json']]]
    media.extend([OUT/'v947_saved_direction_selections.json.gz',ROOT/'records/nav2_v947_20261109/QUALIFICATION.json'])
    manifest=dict(repository=REPO,release_tag=TAG,release_url=f'https://github.com/{REPO}/releases/tag/{TAG}',
                  scientific_outcome='V945_NOT_PASSED',new_integrations=0,
                  assets=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p))for p in media])
    dump(REC/'MEDIA_INDEX.json',manifest);media.append(REC/'MEDIA_INDEX.json')
    assert not run(['git','diff','--cached','--name-only']).strip(),'UNRELATED_STAGING'
    names=[str(CODE.relative_to(ROOT)),str(REC.relative_to(ROOT)),'docs/RPCCR_V945_PATH_REPLAY.md',
           'experiments/v947_rpccr_forward_commitment','records/nav2_v947_20261109',
           'CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md']
    run(['git','add','--',*names]);run(['git','diff','--cached','--check'])
    staged=run(['git','diff','--cached','--name-only']).splitlines()
    assert all((ROOT/p).stat().st_size<90*1024**2 for p in staged)
    run(['git','commit','-m','Visualize saved V945 paths, reversals and last two-meter failure'])
    head=run(['git','rev-parse','HEAD']).strip()
    sync=dict(commit=head,one_attempt=True,push_limit_s=30,remote_read_limit_s=5)
    with(REC/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(sync,f)
    try:run(['git','push','origin','main'],30);sync['push_succeeded']=True
    except Exception as error:sync['push_error']=repr(error)
    try:
        sync['remote_head']=run(['git','ls-remote','origin','refs/heads/main'],5).split()[0]
        sync['remote_head_verified']=sync['remote_head']==head
    except Exception as error:sync['verify_error']=repr(error)
    dump(REC/'GIT_SYNC_RESULT.json',sync)
    assert sync.get('remote_head_verified'),'SOURCE_NOT_REMOTE_VERIFIED_KEEP_RAW'
    gh(['release','create',TAG,'--target',head,'--title','V945 saved path replay: final two meters and direction switching',
        '--notes','Saved native-state visualization only. Blue actual trajectory, green last published reference, purple recovery segment. Last22.31s moved1.135m including0.493m reverse,16 commanded direction changes, only0.143m net goal progress. Final1.857m, scientific NOT_PASSED. New physics/navigation/prediction/training integrations0.','--draft'])
    gh(['release','upload',TAG,*map(str,media)])
    downloaded=OUT/'media_readback';downloaded.mkdir(exist_ok=False)
    gh(['release','download',TAG,'--dir',str(downloaded)])
    for p in media:assert sha(p)==sha(downloaded/p.name)
    gh(['release','edit',TAG,'--draft=false'])
    proof=dict(passed=True,release_url=manifest['release_url'],source_commit=head,assets=len(media),
               full_download_sha_verified=True,new_integrations=0,at=time.time())
    dump(REC/'REMOTE_VERIFIED.json',proof)
    for p in [REC/'REMOTE_VERIFIED.json',REC/'GIT_SYNC_RESULT.json']:
        gh(['release','upload',TAG,str(p)]);gh(['release','download',TAG,'--pattern',p.name,'--dir',str(downloaded)])
        assert sha(p)==sha(downloaded/p.name)
    # Reverify the already remote-verified original record before removing the restored cache.
    run([sys.executable,'-B','experiments/v946_rpccr_regression_closure/restore_selected.py','runs/v858_nav2_verified/v945/main_we'],180)
    raw=ROOT/'runs/v858_nav2_verified/v945'
    assert raw.resolve().is_relative_to(ROOT/'runs')and not raw.is_symlink()
    assert not any(p.is_symlink()for p in raw.rglob('*'))
    deleted=sum(p.stat().st_size for p in raw.rglob('*')if p.is_file());shutil.rmtree(raw)
    discarded=[]
    for pattern in ['*.mp4','*.png','*.encoder.log']:
        for p in OUT.glob(pattern):
            if p.name=='v945_paths_and_last2m.png':continue
            discarded.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),bytes=p.stat().st_size,reason='Superseded incomplete first render or derived preview'))
            deleted+=p.stat().st_size;p.unlink()
    deleted+=sum(p.stat().st_size for p in downloaded.iterdir());shutil.rmtree(downloaded)
    result=dict(restored_raw_reverified_and_cleaned=True,deleted_bytes=deleted,discarded_derived=discarded,
                completed_playable_local_media_retained=True,new_integrations=0,release_url=manifest['release_url'])
    dump(REC/'CLEANUP_RESULT.json',result)
    gh(['release','upload',TAG,str(REC/'CLEANUP_RESULT.json')])
    receipts=OUT/'cleanup_readback';receipts.mkdir(exist_ok=False)
    gh(['release','download',TAG,'--pattern','CLEANUP_RESULT.json','--dir',str(receipts)])
    assert sha(REC/'CLEANUP_RESULT.json')==sha(receipts/'CLEANUP_RESULT.json');shutil.rmtree(receipts)
    run(['git','add','--',str(REC.relative_to(ROOT))]);run(['git','commit','-m','Record verified V945 media delivery and restored-cache cleanup'])
    print(json.dumps(dict(remote=proof,cleanup=result)),flush=True)


if __name__=='__main__':main()
