"""Saved actual9390 input, exact gear history, fresh numerical round disabled."""
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
from types import SimpleNamespace

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def exact(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
io=exact('v1408_prepare_json',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert read(O/'QUALIFICATION.json')['passed']and not(O/'FIXED_INPUTS.json').exists()
    parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
    raw=R/'runs/v858_nav2_verified/v1376/capture_main';origin=read(raw/'COMPONENT_INITIAL_PACKET.json');assert origin['native_tick']==9390 and not origin['coupled_episode']and not origin['steering_motion_active'];origin['parked_target']=None
    task=read(R/'experiments/v1376_prepared_capture_component/ENTRY.json');segment=task['target_segment']
    gear_type=exact('v1408_saved_original_gear',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py').GearHandoff;gear=gear_type();rows=read(raw/'APPLIED_JOURNAL.json')[:9390]
    for i,row in enumerate(rows):
        assert i==row['before_native']and row['applied']and row.get('parked_target')is None
        v,w,proof=gear.select(*row['upstream_request'][:2],native_tick=i,body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders']);assert [v,w,False]==row['request']and proof==row['gear_handoff']
    b=origin['body'];rear=[b[0]-.3*math.cos(b[2]),b[1]-.3*math.sin(b[2]),b[2]];first=segment['poses'][0]
    geometry=dict(start_distance_m=math.dist(rear[:2],first[:2]),start_heading_rad=abs(math.atan2(math.sin(rear[2]-first[2]),math.cos(rear[2]-first[2]))))
    dispatch=exact('v1408_current_fixed_dispatch',R/'experiments/v1404_route_bridge_session/method_dispatch.py')
    gear_memory=dict(gear=gear.gear,brake_start=gear.brake_start,last_tick=gear.last_tick)
    spec=dispatch.choose(dict(event=dict(body=b,geometry=geometry),next_segment=segment,actual=dict(feedback=dict(gear_memory=gear_memory))))
    assert spec['method']=='ORIGINAL_TWO_ARC_CAPTURE_THEN_ORIGINAL_RPP'
    current=dict(origin=origin,gear_memory=gear_memory,next_segment=segment,event_geometry=geometry,method_spec=spec,
                 bridge_forecast=dict(center=task['causal_all_future_ball'][:2],radius_m=task['causal_all_future_ball'][2],periodic_source_tick=9360,
                                      invariant_for_all_future_under_declared_class=True,source_entry_sha256=sha(R/'experiments/v1376_prepared_capture_component/ENTRY.json')),
                 saved_actual_input_not_new_fresh_wire=True,physical_admission=False)
    current['input_sha256']=hashlib.sha256(json.dumps(current,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    out=O/'model';out.mkdir(exist_ok=False);io.atomic(out/'CURRENT_INPUT.json',current);io.atomic(out/'SETUP.json',read(raw/'physics/SETUP.json'));io.atomic(out/'AUDIT_APPROVAL.json',dict(mode='ZERO_MODEL_AUDIT_ENTRY'))
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    saved=(R/'REVIEW_PENDING').read_bytes()
    try:
        (R/'REVIEW_PENDING').unlink()
        p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'audit_entry.py').relative_to(R)),'--entry-check'],cwd=R,env=env,capture_output=True,text=True,timeout=60)
    finally:(R/'REVIEW_PENDING').write_bytes(saved)
    (out/'audit_entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-1800:]
    hashes=read(O/'SOURCE_FREEZE.json')['files']
    # Ensure old method/geometry/allocator dependencies and saved scientific
    # origin are frozen, while not copying historical raw for this new round.
    for freeze in ['runs/v1401_model_origin_qualification/SOURCE_FREEZE.json','runs/v1407_lossless_branch_stream/SOURCE_FREEZE.json']:
        for name,h in read(R/freeze)['files'].items():assert name not in hashes or hashes[name]==h;hashes[name]=h
    for p in [*C.glob('*'),raw/'COMPONENT_INITIAL_PACKET.json',raw/'APPLIED_JOURNAL.json',raw/'physics/SETUP.json',R/'experiments/v1376_prepared_capture_component/ENTRY.json',out/'CURRENT_INPUT.json',out/'SETUP.json']:
        if p.is_file():hashes[str(p.relative_to(R))]=sha(p)
    assert all(sha(R/n)==h for n,h in hashes.items())
    io.atomic(O/'NUMERIC_SOURCE_FREEZE.json',dict(files=hashes,physical_admission=False,maximum_generation_steps=904500,maximum_independent_audit_steps=904500))
    fixed=dict(origin_file=str((raw/'COMPONENT_INITIAL_PACKET.json').relative_to(R)),origin_sha256=sha(raw/'COMPONENT_INITIAL_PACKET.json'),input_sha256=current['input_sha256'],historical_gear_rows=len(rows),causal_source_tick=9360,method=spec['method'],models_during_preparation=0)
    io.atomic(O/'FIXED_INPUTS.json',fixed);print(json.dumps(fixed))


if __name__=='__main__':main()
