"""Freeze the qualified complete snapshot/method input; zero model entry first."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not O.exists();O.mkdir();parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==3
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    source=R/'runs/v1415_unified_causal_witness/entry02';assert read(source/'QUALIFICATION.json')['passed']
    fixed=read(source/'FIXED_INPUTS.json');assert fixed['current_input']['geometry_kind']=='ORIGINAL_CAUSAL_TIME_POLYGONS'
    (O/'FIXED_INPUTS.json').write_text(json.dumps(dict(current_input=fixed['current_input'],source_input_file=str((source/'FIXED_INPUTS.json').relative_to(R)),source_input_sha256=sha(source/'FIXED_INPUTS.json'),saved_actual_input_not_fresh_wire=True),indent=2)+'\n')
    (O/'SETUP.json').write_bytes((source/'entry/SETUP.json').read_bytes())
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    try:
        (R/'REVIEW_PENDING').unlink()
        p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'entry.py').relative_to(R)),'--entry-check'],cwd=R,env=env,capture_output=True,text=True,timeout=60)
    finally:(R/'REVIEW_PENDING').write_bytes(saved)
    (O/'entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-2500:]
    assert read(O/'ENTRY_CHECK.json')['passed']
    hashes=read(source/'SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in hashes.items())
    for p in [*C.iterdir(),O/'FIXED_INPUTS.json',O/'SETUP.json']:
        if p.is_file():hashes[str(p.relative_to(R))]=sha(p)
    (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=hashes,qualification='runs/v1416_timed_reserve_qualification/ENTRY_CHECK.json',maximum_analytical_native=400,maximum_vehicle_tasks=0),indent=2)+'\n')
    print(json.dumps(dict(prepared=True,models=0,physical_native=0,maximum_future_analytical_native=400,geometry_kind=fixed['current_input']['geometry_kind'])))


if __name__=='__main__':main()
