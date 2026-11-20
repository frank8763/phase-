"""Saved actual32210 input and exact canonical memory, never a live wire."""
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    assert not O.exists();O.mkdir();parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==4
    with(R/'runs/v648_static_unknown/execution.lock').open('r')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert read(R/'runs/v1416_timed_reserve_qualification/COMPLETION.json')['passed']
    packet_path=R/'runs/v858_nav2_verified/v1378/steering_response/COMPONENT_INITIAL_PACKET.json';packet=read(packet_path);original=copy.deepcopy(packet);assert packet['native_tick']==32210
    raw=R/'runs/v858_nav2_verified/v1383/timed_handoff_main';journal=read(raw/'APPLIED_JOURNAL.json');row=journal[32210]
    assert row['body']==packet['body']and row['encoders']==[*packet['steering']['position'],*packet['steering']['velocity']]and row['last_ctrl']==packet['controller_memory']['last_ctrl']and row['integral']==packet['controller_memory']['integral']
    mode=exact('v1417_canonical_mode_book',R/'experiments/v1398_current_event_witness/mode_memory.py').ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False)
    gear=exact('v1417_original_native_gear_book',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py').GearHandoff()
    for i,row in enumerate(journal[:32210]):
        assert row['applied']and row['before_native']==i and mode.snapshot(i)['steering_motion_active']==row['steering_motion_active_before']
        v,w,proof=gear.select(*row['upstream_request'][:2],native_tick=i,body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders']);assert [v,w,False]==row['request']and proof==row['gear_handoff']
        mode.applied(before_native=i,v=v,w=w,parked_target=row['parked_target'],steering_motion_active_after=journal[i+1]['steering_motion_active_before'])
    modes=mode.snapshot(32210)
    for key in ['coupled_episode','steering_motion_active','parked_target']:packet[key]=modes[key]
    snapshot_path=R/'runs/v858_nav2_verified/v1370/rpp_default_horizon_m1_s01_main/CAUSAL_PREDICTION_MODEL.json';snapshot=read(snapshot_path)
    assert snapshot['periodic']['source_tick']==32200 and snapshot['last_observed_time']<=packet['sim_time']+1e-8
    setup=read(raw/'physics/SETUP.json');source=exact('v1417_bound_geometry_source',R/'experiments/v1415_unified_causal_witness/geometry_binding.py')
    forecast=source.all_future(snapshot,current_native=packet['native_tick'],current_sim_time=packet['sim_time'])
    sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'));from segments import validate
    segment=read(R/'experiments/v1383_exact_timed_handoff/ENTRY.json')['target_segment'];_,geometry=validate(segment,packet['body'],setup['known'],(forecast['center'],forecast['radius_m']),.22)
    memory=dict(gear=gear.gear,brake_start=gear.brake_start,last_tick=gear.last_tick)
    dispatch=exact('v1417_original_finite_dispatch',R/'experiments/v1404_route_bridge_session/method_dispatch.py');spec=dispatch.choose(dict(event=dict(body=packet['body'],geometry=geometry),next_segment=segment,actual=dict(feedback=dict(gear_memory=memory))))
    assert spec['method']=='ORIGINAL_BOUNDED_STEERING_THEN_GEAR_RELEASE_TIMED_REVERSE'
    current=dict(origin=packet,mode_history=modes,gear_memory=memory,next_segment=segment,event_geometry=geometry,method_spec=spec,causal_snapshot_sha256=source.digest(snapshot),bridge_forecast=forecast,saved_actual_input_not_fresh_wire=True,physical_admission=False)
    current['input_sha256']=source.digest(current);current=source.bind(current,snapshot);source.GeometryBinding(current,setup)
    fixed=dict(packet_file=str(packet_path.relative_to(R)),packet_sha256=sha(packet_path),journal_file=str((raw/'APPLIED_JOURNAL.json').relative_to(R)),journal_sha256=sha(raw/'APPLIED_JOURNAL.json'),historical_mode_gear_rows=32210,original_reported_packet=original,derived_mode=modes,model_input_sha256=current['input_sha256'],causal_source_tick=32200,models=0,physical_admission=False)
    (O/'FIXED_INPUTS.json').write_text(json.dumps(fixed,indent=2)+'\n');model=O/'model';model.mkdir();(model/'CURRENT_INPUT.json').write_text(json.dumps(current,indent=2)+'\n');(model/'SETUP.json').write_text(json.dumps(setup,indent=2)+'\n')
    hashes=read(R/'runs/v1416_timed_reserve_qualification/SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in hashes.items())
    for p in [*C.iterdir(),packet_path,raw/'APPLIED_JOURNAL.json',snapshot_path,O/'FIXED_INPUTS.json',model/'CURRENT_INPUT.json',model/'SETUP.json']:
        if p.is_file():hashes[str(p.relative_to(R))]=sha(p)
    saved=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(saved).hexdigest()==parent['review_pending_original_bytes_sha256']
    env=dict(os.environ);env.update(LD_LIBRARY_PATH=str(R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'),CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');env.pop('LD_PRELOAD',None)
    results=[]
    try:
        for name,flag in [('production_entry','--entry-check'),('production_failure','--injected-early-failure'),('audit','--entry-check')]:
            if name=='audit':command=['taskset','-c','2',str(R/'run_phase.sh'),str((C/'audit_entry.py').relative_to(R)),flag]
            else:
                out=O/name;out.mkdir();(out/'CURRENT_INPUT.json').write_text(json.dumps(current,indent=2)+'\n');(out/'SETUP.json').write_text(json.dumps(setup,indent=2)+'\n')
                a=dict(scope='ZERO_MODEL_PRODUCTION_QUALIFICATION',models_authorized=False,maximum_model_constructions=0,maximum_model_steps=0,current_input_sha256=current['input_sha256'],tested_source_hashes=hashes,boot_id=parent['boot_id'],run_id='v1417-saved-timed-method-entry',absolute_deadline_unix=min(time.time()+240,1795395600),hard_stop_monotonic=min(time.monotonic()+240,parent['hard_stop_monotonic']));(out/'APPROVAL.json').write_text(json.dumps(a,indent=2)+'\n')
                command=['taskset','-c','2',str(R/'run_phase.sh'),str((C/'production_entry.py').relative_to(R)),str(out),flag]
            (R/'REVIEW_PENDING').unlink()
            try:p=subprocess.run(command,cwd=R,env=env,capture_output=True,text=True,timeout=60)
            finally:(R/'REVIEW_PENDING').write_bytes(saved)
            (O/(name+'.console')).write_text(p.stdout+p.stderr)
            if name=='production_failure':assert p.returncode==1 and read(out/'RESULT.json')['analytical_native']==0 and read(out/'RESULT.json')['error']=="RuntimeError('QUALIFIED_INJECTED_BEFORE_ANY_MODEL_CALL')"
            else:assert p.returncode==0,p.stderr[-2200:]
            results.append(dict(entry=name,passed=True,models=0,analytical_native=0))
    finally:(R/'REVIEW_PENDING').write_bytes(saved)
    value=dict(passed=True,models=0,analytical_native=0,physical_native=0,entries=results,full_numerical_launch_not_yet_qualified=True,owner_missing=True,physical_admission=False)
    (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(value,indent=2)+'\n');(O/'INPUT_ENTRY_SOURCE_FREEZE.json').write_text(json.dumps(dict(files=hashes,qualification='runs/v1417_complete_timed_witness/ENTRY_QUALIFICATION.json',models=0,physical_admission=False),indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
