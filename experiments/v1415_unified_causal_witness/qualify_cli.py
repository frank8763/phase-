"""Once-only new complete backend/geometry/refusal save production checks."""
import copy
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not O.exists();O.mkdir()
    parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
    assert read(R/'runs/v1413_current_reserve_qualification/FULL_REMOTE_VERIFIED.json')['passed']
    assert read(R/'runs/v1414_current_timed_geometry/QUALIFICATION.json')['passed']
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    end=min(time.monotonic()+300,parent['hard_stop_monotonic']-10);assert time.time()<1795395600-400
    (O/'CLAIM.json').write_text(json.dumps(dict(started_unix=time.time(),hard_stop_monotonic=end,maximum_real_production_entries=3,maximum_models=0,maximum_analytical_native=0),indent=2)+'\n')
    old=R/'runs/v1413_current_reserve_qualification';fixed=read(old/'FIXED_INPUTS.json');snapshot=read(old/'CAUSAL_SNAPSHOT.json');setup=read(old/'SETUP.json')
    sys.path.insert(0,str(R/'experiments/v1397_event_handoff_integration'));from causal_bridge_field import all_future
    source=exact('v1415_qualification_causal_geometry',C/'geometry_binding.py');dispatch=exact('v1415_original_method_dispatch',R/'experiments/v1404_route_bridge_session/method_dispatch.py')
    segment=read(R/'experiments/v1383_exact_timed_handoff/ENTRY.json')['target_segment'];origin=fixed['origin'];b=origin['body'];forecast=all_future(snapshot,current_native=origin['native_tick'],current_sim_time=origin['sim_time'])
    sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'));from segments import validate
    _,geometry=validate(segment,b,setup['known'],[*forecast['center'],forecast['radius_m']],.22)
    spec=dispatch.choose(dict(event=dict(body=b,geometry=geometry),next_segment=segment,actual=dict(feedback=dict(gear_memory=fixed['gear_memory']))))
    assert spec['method']=='ORIGINAL_BOUNDED_STEERING_THEN_GEAR_RELEASE_TIMED_REVERSE'
    base=dict(origin=origin,mode_history=fixed['mode_history'],gear_memory=fixed['gear_memory'],next_segment=segment,event_geometry=geometry,method_spec=spec,
              causal_snapshot_sha256=source.digest(snapshot),bridge_forecast=forecast,saved_actual_input_not_fresh_wire=True,physical_admission=False)
    base['input_sha256']=source.digest(base);current=source.bind(base,snapshot);source.GeometryBinding(current,setup)
    (O/'FIXED_INPUTS.json').write_text(json.dumps(dict(current_input=current,saved_source='runs/v1413_current_reserve_qualification/FIXED_INPUTS.json',models=0,new_fresh_actual_source=False),indent=2)+'\n')
    hashes=read(R/'runs/v1411_native_guarded_execution/SOURCE_FREEZE.json')['files']
    for p,h in read(R/'runs/v1414_current_timed_geometry/SOURCE_FREEZE.json')['files'].items():assert p not in hashes or hashes[p]==h;hashes[p]=h
    for p in [*C.iterdir(),old/'FIXED_INPUTS.json',old/'CAUSAL_SNAPSHOT.json',old/'SETUP.json',R/'experiments/v1383_exact_timed_handoff/ENTRY.json',R/'experiments/v1410_scalar_feedback_witness/modeled_peer.py',O/'FIXED_INPUTS.json']:
        if p.is_file():hashes[str(p.relative_to(R))]=sha(p)
    assert all(sha(R/p)==h for p,h in hashes.items())
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,physical_admission=False,entries=[])
    try:
        for mode,flag in [('entry','--entry-check'),('refusal_storage','--storage-check'),('early_failure','--injected-early-failure')]:
            assert time.monotonic()<end-65
            out=O/mode;out.mkdir();(out/'CURRENT_INPUT.json').write_text(json.dumps(current,indent=2)+'\n');(out/'SETUP.json').write_text(json.dumps(setup,indent=2)+'\n')
            a=dict(scope='ZERO_MODEL_PRODUCTION_QUALIFICATION',models_authorized=False,maximum_model_constructions=0,maximum_model_steps=0,current_input_sha256=current['input_sha256'],tested_source_hashes=hashes,boot_id=parent['boot_id'],run_id='v1415-geometry-and-refusal-storage-only',absolute_deadline_unix=min(time.time()+end-time.monotonic(),1795395600),hard_stop_monotonic=end);(out/'APPROVAL.json').write_text(json.dumps(a,indent=2)+'\n')
            (R/'REVIEW_PENDING').unlink()
            try:p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'production_entry.py').relative_to(R)),str(out),flag],cwd=R,env=env,capture_output=True,text=True,timeout=60)
            finally:(R/'REVIEW_PENDING').write_bytes(saved)
            (out/'entry.console').write_text(p.stdout+p.stderr)
            if mode=='early_failure':
                proof=read(out/'RESULT.json');assert p.returncode==1 and proof['error']=="RuntimeError('QUALIFIED_INJECTED_BEFORE_ANY_MODEL_CALL')"and proof['analytical_native']==0 and proof['explicit_predictor_constructions']==0 and not proof['evidence_write_errors']
            else:
                assert p.returncode==0,p.stderr[-2000:];proof=read(out/('ENTRY_CHECK.json'if mode=='entry'else'STORAGE_CHECK.json'));assert proof['passed']and proof['analytical_native']==0
            result['entries'].append(dict(mode=mode,passed=True,models=0,analytical_native=0))
        result.update(passed=True,original_RPP_client_peer_unchanged_and_previously_qualified=True,original_peer_dependency='experiments/v1410_scalar_feedback_witness/modeled_peer.py',new_RPC_or_physical_qualification_claimed=False,old_RPP_qualification_not_repeated=True)
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        (R/'REVIEW_PENDING').write_bytes(saved);result.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==saved);(O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    if result['passed']:(O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=hashes,qualification='runs/v1415_unified_causal_witness/QUALIFICATION.json',models=0,physical_admission=False,full_finite_numerical_witness_not_yet_qualified=True),indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='traceback'}));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
