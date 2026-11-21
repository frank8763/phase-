"""Saved-array component gates; never a fresh-wire/physical/goal certificate."""
import hashlib
import importlib.util
from pathlib import Path

R=Path(__file__).resolve().parents[2]
GEOMETRY='experiments/v1415_unified_causal_witness/geometry_binding.py'


def geometry(method,setup,guard):
    guard.check()
    path=R/GEOMETRY
    assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[GEOMETRY]
    spec=importlib.util.spec_from_file_location('v1552_original_causal_disk',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base=method['base_method']
    snapshot=base['physical_source']['causal_snapshot']
    forecast=module.all_future(snapshot,current_native=base['fixed_origin_native'],current_sim_time=base['fixed_origin_sim_time'])
    assert forecast['coefficient_snapshot_sha256']==method['causal_snapshot_sha256']==base['causal_snapshot_sha256']
    assert method['geometry_kind']=='FULL_PERIOD_DISK'
    return module.Periodic(setup['known'],[*forecast['center'],forecast['radius_m']]),forecast


def evaluate(arrays,method,setup,geom,*,expected_native,zero_suffix,raw_current_only):
    import numpy as np
    s,u,m=arrays['states'],arrays['ctrl'],arrays['memory']
    n=expected_native
    assert s.shape==(n+1,8) and u.shape==(n,4) and m.shape==(n+1,5)
    assert zero_suffix==2200 and n>=2200
    assert set(arrays)=={'states','ctrl','memory','modes','gear','encoders','parked','native','sim_time','raw_rows','requested_body','applied_body','gear_proof'}
    widths=dict(modes=3,gear=3,encoders=4,parked=2,raw_rows=3,requested_body=2,applied_body=2,gear_proof=10)
    assert all(arrays[k].shape==(n+1 if k in {'modes','gear','encoders','parked'}else n,v)for k,v in widths.items())
    base=method['base_method']
    origin=base['fixed_origin_native']
    first=int(arrays['native'][0])
    assert first>=origin and np.array_equal(arrays['native'],first+np.arange(n+1))
    expected_clock=base['fixed_origin_sim_time']+.01*(arrays['native']-origin)
    limits=np.asarray(setup['limits'])
    rates=np.asarray(setup['slew_per_second'])*.01
    differences=np.diff(np.vstack([m[0,:4],u]),axis=0)
    raw=arrays['raw_rows']
    requested=arrays['requested_body']
    filtered=arrays['applied_body']
    gear=arrays['gear']
    gp=arrays['gear_proof']
    current_states=arrays['modes'][:,1].astype(bool)
    release=gp[:,8].astype(bool)
    hold=gp[:,7]==1
    lower=float(geom.tube(s,first))
    expected_w=np.where((raw[:,2]!=0)|(raw[:,1]==0),0.,raw[:,1]*np.tan(raw[:,0])/.6)
    same_as_request=(gp[:,7]!=1)
    checks=dict(
        complete_N_actions_Nplus1_states=len(u)==n and len(s)==n+1,
        complete_original2200_tail=bool(np.array_equal(raw[-2200:],np.zeros((2200,3)))),
        complete200minimum=bool(np.array_equal(raw[-200:],np.zeros((200,3)))),
        finite=bool(all(np.isfinite(value).all()for value in arrays.values())),
        source_clock=bool(np.max(abs(arrays['sim_time']-expected_clock))<=1e-8),
        raw_request_body_mapping=bool(np.array_equal(requested[:,0],raw[:,1])and np.max(abs(requested[:,1]-expected_w))<=1e-8),
        filtered_request_accounting=bool(np.max(abs(filtered[hold]))<=1e-8 if hold.any()else True),
        released_or_unchanged_request=bool(np.max(abs(filtered[same_as_request]-requested[same_as_request]))<=1e-8 if same_as_request.any()else True),
        gear_clock_per_native=bool(np.array_equal(gear[1:,1],arrays['native'][:-1])and gear[0,1]==first-1),
        gear200_release_rest=bool((gp[release,6]>=200).all()and (gp[release,5]==1).all()),
        original_gear_states=bool(np.isin(gear[:,0],[-1,0,1]).all()),
        complete_zero_applied_tail=bool(np.array_equal(filtered[-2200:],np.zeros((2200,2)))),
        no_parked_tail=bool(np.array_equal(arrays['parked'][-2200:],np.zeros((2200,2)))),
        controls_in_bounds=bool((u>=limits[:,0]-1e-8).all()and (u<=limits[:,1]+1e-8).all()),
        controls_slew=bool((abs(differences)<=rates+1e-8).all()),
        controls_memory=bool(np.max(abs(m[1:,:4]-u))<=1e-8),
        body_caps=bool((abs(s[:,3:6])<=np.array([.13,.03,.16])+1e-8).all()),
        active_steering_body_caps=bool((abs(s[current_states,3])<=.01+1e-8).all()and (abs(s[current_states,5])<=.16+1e-8).all()),
        mode_flags=bool(np.isin(arrays['modes'],[0,1]).all()and (arrays['modes'][:,1]<=arrays['modes'][:,0]).all()),
        terminal_rest=bool(abs(s[-1,3:6]).max()<=.003 and abs(arrays['encoders'][-1,2:]).max()<=.03 and abs(m[-1,2:4]).max()<=1e-10),
        current_full_footprint_tube=lower>=.22-1e-8)
    if raw_current_only:
        checks['complete_current_zero_requests']=bool(np.array_equal(raw,np.zeros((n,3))))
    return dict(passed=all(checks.values()),checks=checks,causal_tube_lower_m=lower,
                fixed_origin_native=origin,branch_origin_native=first,
                branch_origin_sim_time=float(arrays['sim_time'][0]),complete_native=n,
                response_method_sha256=method['response_method_sha256'],
                geometry_kind='FULL_PERIOD_DISK',causal_snapshot_sha256=method['causal_snapshot_sha256'],
                observation_progress_gate=None,original_refuge_or_navigation_goal_gate=None,
                original_qGeometry_equivalence=False,actual200tail_executed=False,
                physical_permission=False,whole_navigation_passed=False)
