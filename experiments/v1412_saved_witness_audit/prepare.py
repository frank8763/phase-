"""Real guarded CPU2 audit/NumPy output entry; no model calls."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not O.exists();O.mkdir()
    parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert parent['active_round'] is None and not parent['models_now_authorized']
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    result=dict(passed=False,models=0,analytical_native=0,physical_native=0)
    try:
        (R/'REVIEW_PENDING').unlink()
        p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'audit_entry.py').relative_to(R)),'--entry-check'],cwd=R,env=env,capture_output=True,text=True,timeout=60)
        (O/'entry.console').write_text(p.stdout+p.stderr)
        assert p.returncode==0,p.stderr[-2000:]
        assert read(O/'model/ENTRY_CHECK.json')['passed']
        result['passed']=True
    except BaseException as exc:result['error']=repr(exc)
    finally:
        (R/'REVIEW_PENDING').write_bytes(saved);result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved)
        (O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['passed'],result
    hashes=read(R/'runs/v1410_scalar_feedback_witness/NUMERIC_SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in hashes.items())
    for base in [C,R/'runs/v1410_scalar_feedback_witness/model']:
        for p in base.rglob('*'):
            if p.is_file() and '__pycache__'not in p.parts:
                name=str(p.relative_to(R));h=sha(p);assert name not in hashes or hashes[name]==h;hashes[name]=h
    (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=hashes,qualification='runs/v1412_saved_witness_audit/QUALIFICATION.json',maximum_audit_steps=791940,maximum_generation_steps=0,physical_admission=False),indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
