"""Single CPU5 original witness metadata target; no old modules or model calls."""
import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
import traceback

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name
REVIEW_SHA = '4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def put(path, value):
    raw = json.dumps(value, indent=2, allow_nan=False).encode()+b'\n'
    assert len(raw) <= 128*1024
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_bytes(raw)
    tmp.replace(path)


def main():
    start = time.monotonic()
    now = time.time()
    assert now + 120 < 1795395600
    review = R/'REVIEW_PENDING'
    saved_review = review.read_bytes()
    assert hashlib.sha256(saved_review).hexdigest() == REVIEW_SHA
    parent = json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
    assert parent['active_round'] is None and parent.get('active_math_round') is None and not parent['models_now_authorized']
    assert not (O/'ENTRY_ONCE_CLAIM.json').exists() and not (O/'SOURCE_FREEZE.json').exists()
    with (R/'runs/v648_static_unknown/execution.lock').open() as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    seen=set();usage=0
    for root, dirs, files in os.walk(R/'runs',followlinks=False):
        for p in [Path(root)]+[Path(root)/name for name in files]:
            s=p.lstat();key=s.st_dev,s.st_ino
            if key not in seen:
                seen.add(key);usage+=s.st_blocks*512
    assert usage+(8+10+32+512)*1024**2 < 15*1024**3, 'SOURCE_TARGET_FULL_STORAGE_PEAK'
    source={}
    for p in C.iterdir():
        if p.is_file():
            if p.suffix=='.py':ast.parse(p.read_text())
            source[str(p.relative_to(R))]=sha(p)
    with (O/'ENTRY_OUTER_ONCE_CLAIM.json').open('x') as stream:
        json.dump(dict(unix=now,monotonic=start,absolute_root=1795395600,limit_s=120,
                       allruns_bytes=usage,reserved_peak_bytes=usage+562*1024**2,
                       models_authorized=False,source_sha256=source),stream)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
                Allocator_recomputations=0,optimizer_calls=0,replay_native=0)
    process=None
    console=bytearray()
    try:
        saved_path=O/'SOURCE_REVIEW_ORIGINAL.bin'
        assert not saved_path.exists() and len(saved_review)<=4096
        saved_path.write_bytes(saved_review)
        assert sha(saved_path)==REVIEW_SHA
        review.unlink()
        env=os.environ.copy()
        env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                   CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYTHONDONTWRITEBYTECODE='1')
        command=['ionice','-c','3','taskset','-c','2','nice','-n','19','./run_phase.sh',
                 str((C/'entry.py').relative_to(R))]
        process=subprocess.Popen(command,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
        poll=selectors.DefaultSelector();poll.register(process.stdout,selectors.EVENT_READ)
        while poll.get_map():
            assert time.time()<min(now+120,1795395600) and time.monotonic()<start+120, 'SOURCE_TARGET_DUAL_CLOCK_LIMIT'
            for key,_ in poll.select(.2):
                block=os.read(key.fileobj.fileno(),16384)
                if not block:
                    poll.unregister(key.fileobj)
                    continue
                assert len(console)+len(block)<=256*1024, 'SOURCE_TARGET_CONSOLE_CAP'
                console.extend(block)
        process.wait(timeout=5)
        result['returncode']=process.returncode
        assert process.returncode==0, 'SOURCE_TARGET_PROCESS_REFUSED'
        inner=json.loads((O/'ENTRY_QUALIFICATION.json').read_text())
        assert inner['passed'] and inner['closed'] and inner['models']==inner['analytical_native']==inner['physical_native']==0
        assert all(sha(R/name)==identity for name,identity in source.items())
        result['passed']=True
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
        if process is not None:result['returncode']=process.returncode
        (O/'source_entry.console').write_bytes(console)
        review.write_bytes(saved_review)
        result['review_original_restored']=sha(review)==REVIEW_SHA
        with (R/'runs/v648_static_unknown/execution.lock').open() as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result.update(lock_idle=True,closed=True,wall_s=time.monotonic()-start,closed_unix=time.time())
        put(O/'ENTRY_OUTER_CLOSED.json',result)
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
