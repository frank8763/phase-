"""Unchanged complete footprint/error/control/rest gates; no model calls."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def geometry(method,setup):
    # Loading this source preserves original causal coefficient and footprint
    # formulas. No source-tick based geometry or control schedule is selected.
    module=load('v1532_original_causal_geometry_dependency',R/'experiments/v1415_unified_causal_witness/geometry_binding.py')
    physical=method['physical_source'];snapshot=physical['causal_snapshot']
    forecast=module.all_future(snapshot,current_native=method['fixed_origin_native'],current_sim_time=method['fixed_origin_sim_time'])
    assert forecast['coefficient_snapshot_sha256']==method['causal_snapshot_sha256']
    return module.Periodic(setup['known'],[*forecast['center'],forecast['radius_m']]),forecast
def evaluate(arrays,method,setup,geom):
    import numpy as np
    s,u,m=arrays['states'],arrays['ctrl'],arrays['memory'];limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01
    assert s.shape==(2201,8)and u.shape==(2200,4)and m.shape==(2201,5)
    lower=float(geom.tube(s,method['fixed_origin_native']))
    change=np.diff(np.vstack([m[0,:4],u]),axis=0)
    checks=dict(full_original2200=len(u)==2200 and len(s)==len(u)+1,minimum200_preserved=len(u)>=200,finite=bool(all(np.isfinite(v).all()for v in arrays.values())),
                fixed_clock=bool(np.array_equal(arrays['native'],method['fixed_origin_native']+np.arange(2201))and np.max(abs(arrays['sim_time']-(method['fixed_origin_sim_time']+.01*np.arange(2201))))<=1e-8),
                complete_zero_requests=bool(np.array_equal(arrays['requests'],np.zeros((2200,3)))),
                controls_in_bounds=bool((u>=limits[:,0]-1e-8).all()and(u<=limits[:,1]+1e-8).all()),
                controls_slew=bool((abs(change)<=rates+1e-8).all()),
                memory_controls=bool(np.max(abs(m[1:,:4]-u))<=1e-8),
                body_caps=bool((abs(s[:,3:6])<=np.array([.13,.03,.16])+1e-8).all()),
                rest=bool(abs(s[-1,3:6]).max()<=.003 and abs(s[-1,7])<=.03 and abs(m[-1,2:4]).max()<=1e-10),
                current_full_footprint_tube=lower>=.22-1e-8,
                no_mode_transition=bool(np.array_equal(arrays['modes'],np.zeros((2201,3),dtype=np.int64))))
    return dict(passed=all(checks.values()),checks=checks,causal_tube_lower_m=lower,
                complete_native=2200,binding_scope='CURRENT_ORIGIN_STOP_COMPONENT_ONLY',
                physical_or_navigation_passed=False,segment_or_whole_goal_test_executed=False,
                complete200_actual_tail_executed=False,model_variant=method['model_variant'],
                method_input_sha256=method['method_input_sha256'],causal_snapshot_sha256=method['causal_snapshot_sha256'])
def gear_trace(method,states,memory,front):
    import numpy as np
    source=load('v1532_original_zero_request_gear',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py')
    gate=source.GearHandoff();initial=method['physical_source']['gear_memory']
    assert set(initial)=={'gear','brake_start','last_tick'}and initial['last_tick']==method['fixed_origin_native']-1
    for key,value in initial.items():setattr(gate,key,value)
    snapshot=lambda:[gate.gear,gate.last_tick,-1 if gate.brake_start is None else gate.brake_start]
    rows=[snapshot()]
    for i in range(len(states)-1):
        s=states[i];v,w,_=gate.select(0.,0.,native_tick=method['fixed_origin_native']+i,body=[float(s[0]),float(s[1]),float(s[2]),float(s[3]),float(s[5])],last_ctrl=[float(x)for x in memory[i,:4]],encoders=[float(x)for x in front])
        assert v==w==0.;rows.append(snapshot())
    return np.asarray(rows,dtype=np.int64)
