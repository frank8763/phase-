"""Original32600 packet, contiguous mode/gear reconstruction; zero models."""
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not O.exists();O.mkdir()
    assert read(R/'runs/v1411_native_guarded_execution/CLI_QUALIFICATION.json')['passed']
    parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    base=R/'runs/v858_nav2_verified/v1383/timed_handoff_main';packet=read(base/'COMPONENT_INITIAL_PACKET.json');rows=read(base/'APPLIED_JOURNAL.json');assert packet['native_tick']==32600
    mode=exact('v1413_canonical_mode_history',R/'experiments/v1398_current_event_witness/mode_memory.py').ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False)
    gear=exact('v1413_original_gear_history',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py').GearHandoff()
    for i,row in enumerate(rows[:32600]):
        assert row['before_native']==i and row['applied']and mode.snapshot(i)['steering_motion_active']==row['steering_motion_active_before']
        vr,wr,proof=gear.select(*row['upstream_request'][:2],native_tick=i,body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders']);assert [vr,wr,False]==row['request']and proof==row['gear_handoff']
        mode.applied(before_native=i,v=vr,w=wr,parked_target=row['parked_target'],steering_motion_active_after=rows[i+1]['steering_motion_active_before'])
    current=rows[32600];assert current['body']==packet['body']and current['encoders']==[*packet['steering']['position'],*packet['steering']['velocity']]and current['last_ctrl']==packet['controller_memory']['last_ctrl']
    original=copy.deepcopy(packet);modes=mode.snapshot(32600)
    for key in ['coupled_episode','steering_motion_active','parked_target']:packet[key]=modes[key]
    snapshot=R/'runs/v858_nav2_verified/v1370/rpp_default_horizon_m1_s01_main/CAUSAL_PREDICTION_MODEL.json';assert read(snapshot)['periodic']['source_tick']==32200
    fixed=dict(origin=packet,original_reported_packet=original,mode_history=modes,gear_memory=dict(gear=gear.gear,brake_start=gear.brake_start,last_tick=gear.last_tick),canonical_history_rows=32600,raw_packet_sha256=sha(base/'COMPONENT_INITIAL_PACKET.json'),journal_sha256=sha(base/'APPLIED_JOURNAL.json'),mode_defaults_not_used_as_current_history=True,saved_actual_input_not_fresh_wire=True)
    (O/'FIXED_INPUTS.json').write_text(json.dumps(fixed,indent=2)+'\n');(O/'SETUP.json').write_bytes((base/'physics/SETUP.json').read_bytes());(O/'CAUSAL_SNAPSHOT.json').write_bytes(snapshot.read_bytes())
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    try:
        (R/'REVIEW_PENDING').unlink();p=subprocess.run(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'entry.py').relative_to(R)),'--entry-check'],cwd=R,env=env,capture_output=True,text=True,timeout=60)
    finally:(R/'REVIEW_PENDING').write_bytes(saved)
    (O/'entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-2000:]
    hashes=read(R/'runs/v1411_native_guarded_execution/SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in hashes.items())
    for p in [*C.iterdir(),base/'COMPONENT_INITIAL_PACKET.json',base/'APPLIED_JOURNAL.json',base/'physics/SETUP.json',snapshot,O/'FIXED_INPUTS.json',O/'SETUP.json',O/'CAUSAL_SNAPSHOT.json']:
        if p.is_file():hashes[str(p.relative_to(R))]=sha(p)
    (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=hashes,qualification='runs/v1413_current_reserve_qualification/ENTRY_CHECK.json',maximum_analytical_native=400,maximum_vehicle_tasks=0),indent=2)+'\n')
    print(json.dumps(dict(prepared=True,models=0,physical_native=0,derived_mode=modes,original_reported_mode=original['coupled_episode'])))


if __name__=='__main__':main()
