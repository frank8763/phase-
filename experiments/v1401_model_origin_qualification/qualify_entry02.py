"""Once-only real isolated CLI entry, with zero model construction budget."""
import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback
import owner

R=owner.R;C=owner.C;O=owner.O


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));O.mkdir(exist_ok=True)
    parent=owner.read(owner.DAY/'LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    origin=R/'runs/v858_nav2_verified/v1376/capture_main/FINAL_PACKET.json';setup=origin.parent/'physics/SETUP.json'
    owner.write(O/'FIXED_INPUTS.json',dict(origin_file=str(origin.relative_to(R)),origin_sha256=owner.sha(origin),setup_file=str(setup.relative_to(R)),setup_sha256=owner.sha(setup),second_case_explicit_modeled_memory_fixture=True,physical_admission=False))
    owner.write(O/'ENTRY_QUALIFICATION02_CLAIM.json',dict(started_unix=time.time(),maximum_model_constructions=0,maximum_model_steps=0))
    proof=dict(passed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,physical_admission=False)
    try:
        for p in C.glob('*.py'):
            if p.name!='entry.py':ast.parse(p.read_text())
        (R/'REVIEW_PENDING').unlink()
        try:
            p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'entry02.py').relative_to(R)),'--entry-check'],cwd=R,env=owner.env(),capture_output=True,text=True,timeout=60)
        finally:(R/'REVIEW_PENDING').write_bytes(saved)
        (O/'entry_check02.console').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-2000:]
        entry=owner.read(O/'ENTRY_CHECK02.json');assert entry['passed']and entry['models_constructed']==0 and entry['actual_cpu']==[2]
        # Preserve the already-qualified constructor/step/source/memory chain.
        files=owner.read(R/'experiments/v1396_rpp_rpc_retirement/SOURCE_FREEZE.json')['files']
        for n in ['runs/v1398_current_event_witness/CPU2_ENTRY_SOURCE_FREEZE.json','runs/v1398_current_event_witness/INPUT_PEER_SOURCE_FREEZE.json']:
            for name,h in owner.read(R/n)['files'].items():
                assert name not in files or files[name]==h;files[name]=h
        for path in [*C.glob('*.py'),C/'PROTOCOL.md',O/'FIXED_INPUTS.json',origin,setup]:files[str(path.relative_to(R))]=owner.sha(path)
        assert all(owner.sha(R/name)==h for name,h in files.items())
        owner.write(O/'SOURCE_FREEZE.json',dict(files=files,models=0,maximum_numeric_qualification_steps=804,physical_admission=False))
        proof.update(passed=True,real_run_phase_CPU2_entry=True,constructor_profile_gate=True,production_guard_and_model_source_binding=True,source_freeze_sha256=owner.sha(O/'SOURCE_FREEZE.json'),numerical_models_not_yet_qualified=True)
    except BaseException as exc:proof.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        (R/'REVIEW_PENDING').write_bytes(saved);proof['review_pending_restored']=(R/'REVIEW_PENDING').read_bytes()==saved;owner.write(O/'PRELAUNCH_QUALIFICATION02.json',proof)
    print(json.dumps({k:v for k,v in proof.items()if k!='traceback'}));return 0 if proof['passed']else 1


if __name__=='__main__':raise SystemExit(main())
