"""Entry02 zero-model policy-bootstrap continuation; original closure preserved."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def write(path,value):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not (O/'CPU2_PREPARATION02_CLAIM.json').exists()
    parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
    assert parent['active_round'] is None and not parent['models_now_authorized'] and time.time()<1795395600-300
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    modes=['entry','producer','guard'];started=time.monotonic();end=min(started+300,parent['hard_stop_monotonic']-20)
    registration=dict(scope='three zero-model production CPU2 entries only',entry_modes=modes,maximum_model_constructions=0,maximum_model_steps=0,
                      physical_admission=False,started_unix=time.time(),started_monotonic=started,hard_stop_monotonic=end,
                      absolute_deadline_unix=min(time.time()+300,1795395600),boot_id=parent['boot_id'])
    write(O/'CPU2_PREPARATION02_REGISTRATION.json',registration);write(O/'CPU2_PREPARATION02_CLAIM.json',dict(started_unix=time.time(),one_attempt=True,maximum_entries=3,models=0))
    output=O/'cpu2_preparation02';output.mkdir(exist_ok=False)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,physical_admission=False,entries=[])
    environment=dict(os.environ);mesa=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
    environment.update(LD_LIBRARY_PATH=str(mesa),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');environment.pop('LD_PRELOAD',None)
    try:
        for mode in modes:
            assert time.monotonic()<end-65 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==parent['boot_id']
            (R/'REVIEW_PENDING').unlink()
            try:
                process=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'qualify_generator_entry02.py').relative_to(R)),'--mode',mode],cwd=R,env=environment,capture_output=True,text=True,timeout=60)
            finally:(R/'REVIEW_PENDING').write_bytes(saved)
            (output/(mode+'.console')).write_text(process.stdout+process.stderr)
            assert process.returncode==0,mode+' '+process.stderr[-2200:]
            proof=json.loads(process.stdout.strip().splitlines()[-1]);assert proof['passed'] and proof['actual_cpu']==[2] and proof['model_constructions']==0
            result['entries'].append(proof)
        result['passed']=True
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        (R/'REVIEW_PENDING').write_bytes(saved)
        # This exact intentional escape-test symlink is a disposable fixture.
        link=output/'readonly_source_link'
        if link.is_symlink():assert link.readlink()==C;link.unlink()
        result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved,
                      full_model_generator_qualified=False)
        write(O/'CPU2_PREPARATION02_QUALIFICATION.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['entries','traceback']}))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
