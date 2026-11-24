"""Bounded once SOURCE owner; restores original review even after failure."""
import fcntl
import hashlib
import json
import os
import selectors
import signal
import subprocess
import time
import traceback
from context import C,O,R
STOP=time.time()+300
def encoded(x):return (json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()


def main():
    start=time.monotonic();now=time.time()
    review=R/'REVIEW_PENDING';original=review.read_bytes()
    assert hashlib.sha256(original).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert now+150<STOP and not(O/'SOURCE_QUALIFICATION.json').exists()
    parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
    assert parent['active_round']is None and not parent['models_now_authorized']
    with(R/'runs/v648_static_unknown/execution.lock').open()as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    seen=set();used=0
    for root,ds,fs in os.walk(R/'runs',followlinks=False):
        for path in [__import__('pathlib').Path(root)]+[__import__('pathlib').Path(root)/n for n in fs]:
            st=path.lstat();key=(st.st_dev,st.st_ino)
            if key not in seen:seen.add(key);used+=st.st_blocks*512
    assert used+(4+8+32+512)*1024**2<15*1024**3
    current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());assert current['active_round']is None and not current['models_now_authorized']
    for case in [r['assignment_id'] for r in json.loads((R/'runs/v1643_formal_parent_metadata/FORMAL_LEDGER.json').read_text())['rows']]:
        base=R/'runs/v1643_formal_parent_metadata/rounds'/case
        barrier=json.loads((base/'POST_ROUND_STORAGE_BARRIER.json').read_text());assert barrier['passed']
        for key,value in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert hashlib.sha256((R/barrier[key]).read_bytes()).hexdigest()==barrier[value]
    with(O/'SOURCE_OUTER_ONCE_CLAIM.json').open('xb')as f:
        f.write(encoded(dict(unix=now,models_authorized=False,allruns_bytes=used,
                             maximum_wall_s=150,absolute_root_stop_unix=STOP)))
    result=dict(passed=False,closed=False,models=0,physical_native=0)
    process=None;console=bytearray()
    try:
        review.unlink()
        env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',
                                       OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        process=subprocess.Popen(['taskset','-c','2','nice','-n','19','ionice','-c','3',
            './run_phase.sh',str((C/'source_target.py').relative_to(R))],cwd=R,env=env,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
        identity=dict(pid=process.pid,pgid=os.getpgid(process.pid),start_ticks=__import__('pathlib').Path('/proc',str(process.pid),'stat').read_text().split()[21],boot_id=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip())
        (O/'SOURCE_OWNED_CHILD.json').write_bytes(encoded(identity))
        selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
        while selector.get_map():
            assert time.time()<min(STOP,now+150)and time.monotonic()<start+150
            for key,_ in selector.select(.2):
                data=os.read(key.fileobj.fileno(),16384)
                if not data:selector.unregister(key.fileobj);continue
                assert len(console)+len(data)<=256*1024
                console.extend(data)
        process.wait(timeout=5)
        inner=json.loads((O/'SOURCE_QUALIFICATION.json').read_text())
        assert process.returncode==0 and inner['passed']and inner['closed']
        assert inner['models']==inner['physical_native']==inner['analytical_native']==0
        frozen=json.loads((O/'SOURCE_FREEZE.json').read_text())['files']
        assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in frozen.items()), 'FINAL_ALL_SOURCE_AFTER_CHILD_EXIT'
        result['all_source_SHA_verified_after_child_exit']=True
        result.update(passed=True,source_API_only=True,complete_runtime_qualified=False)
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        if process is not None and process.poll()is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
        if process is not None:result['returncode']=process.returncode
        (O/'source.console').write_bytes(console)
        review.write_bytes(original)
        result.update(closed=True,wall_s=time.monotonic()-start,review_restored=review.read_bytes()==original)
        (O/'SOURCE_OUTER_CLOSED.json').write_bytes(encoded(result))
    print(json.dumps(result));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
