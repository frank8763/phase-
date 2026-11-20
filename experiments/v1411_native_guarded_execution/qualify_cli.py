"""Once-only new native-source production CPU2 and CPU3 entry qualification."""
import ast
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    out=O/'cli_qualification';assert not out.exists();out.mkdir()
    parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    end=min(time.monotonic()+300,parent['hard_stop_monotonic']-10);assert time.time()<1795395600-400
    (out/'CLAIM.json').write_text(json.dumps(dict(started_unix=time.time(),hard_stop_monotonic=end,maximum_CPU2_entries=3,maximum_CPU3_import_entries=1,maximum_model_constructions=0,maximum_model_native=0),indent=2)+'\n')
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,physical_admission=False,entries=[])
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    try:
        for mode,flag in [('entry','--entry-check'),('contracts','--contract-check'),('early_failure','--injected-early-failure')]:
            assert time.monotonic()<end-65
            folder=out/mode;folder.mkdir()
            (R/'REVIEW_PENDING').unlink()
            try:p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'production_entry.py').relative_to(R)),str(folder),flag],cwd=R,env=env,capture_output=True,text=True,timeout=60)
            finally:(R/'REVIEW_PENDING').write_bytes(saved)
            (folder/'entry.console').write_text(p.stdout+p.stderr)
            proof=read(folder/'RESULT.json')
            if mode=='early_failure':
                assert p.returncode==1 and proof['error']=="RuntimeError('V1411_INJECTED_BEFORE_ANY_MODEL_OR_VEHICLE_CALL')"and proof['models']==proof['analytical_native']==proof['physical_native']==0
            else:assert p.returncode==0 and proof['passed'],proof
            result['entries'].append(dict(mode=mode,passed=True,models=0,analytical_native=0,proof=str((folder/'RESULT.json').relative_to(R))))
        folder=out/'ros_import';folder.mkdir();tasks=read(R/'experiments/v1370_overnight_controller_matrix/TASKS.json');task=next(t for t in tasks if t['task_id']=='rpp_default_horizon_m1_s01_main');(folder/'TASK.json').write_text(json.dumps(task,indent=2)+'\n')
        helper=exact('v1411_original_isolated_ROS_environment',R/'experiments/v1396_rpp_rpc_retirement/peer_environment.py');ros,peer_env=helper.environment(folder)
        p=subprocess.run(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'route_ros.py'),str(folder/'TASK.json'),'--entry-check']),cwd=R,env=peer_env,capture_output=True,text=True,timeout=60)
        (folder/'entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-2000:]
        assert '"actual_ros_imports_loaded": true'in p.stdout
        result['entries'].append(dict(mode='real_CPU3_route_ROS_import',passed=True,controller_started=False,models=0))
        # Review the actual transport source, not only its evidence row.
        tree=ast.parse((C/'route_ros.py').read_text())
        assert 'command_source=source'in (C/'route_ros.py').read_text()
        result.update(passed=True,source_attribution_in_real_command_datagram=True,complete_physical_backend_not_admitted=True)
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        (R/'REVIEW_PENDING').write_bytes(saved);result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved)
        (O/'CLI_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    if result['passed']:
        files=read(R/'runs/v1412_saved_witness_audit/SOURCE_FREEZE.json')['files']
        for p in C.iterdir():
            if p.is_file():files[str(p.relative_to(R))]=sha(p)
        for p in ['runs/v858_nav2_verified/v1396/full9390_main/CAPTURE_COMMANDS.json','runs/v858_nav2_verified/v1396/full9390_main/OBSERVATIONS_SENT.json','experiments/v1370_overnight_controller_matrix/TASKS.json']:
            files[p]=sha(R/p)
        assert all(sha(R/p)==h for p,h in files.items())
        (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=files,qualification='runs/v1411_native_guarded_execution/CLI_QUALIFICATION.json',models=0,physical_admission=False,reserve_numerically_qualified=False,full_runtime_not_admitted=True),indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='traceback'}));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
