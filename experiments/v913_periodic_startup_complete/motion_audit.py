"""Independent saved causal support and terminal-choice reconstruction; no model."""
import gzip,hashlib,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v887_exact_lidar_software')]
from support_envelope import SupportEnvelope,raster_support,polygon,NORMALS,HORIZON,MAP_LATENCY_RESERVE
from exact_lidar import get_lidar_features
from reference_terminal import terminal_goal
from reproduce import pose
def audit(out):
    out=Path(out);journal=json.loads(gzip.decompress((out/'MOTION_ENVELOPE.json.gz').read_bytes()));setup=json.loads((out/'physics/SETUP.json').read_text());sensors=json.loads(gzip.decompress((out/'physics/SENSORS.json.gz').read_bytes()))
    catalog={p['native_tick']:{k:p[k]for k in ['native_tick','time','xy','yaw','ranges']}for p in sensors}
    tracker=SupportEnvelope(setup['known'],get_lidar_features);states={};covered=0
    from periodic_support import PeriodicSupport,swept_bounds
    periodic=PeriodicSupport();periodic_states={}
    assert len(journal['observations'])==len(journal['states'])
    for packet,expected in zip(journal['observations'],journal['states']):
        assert packet==catalog[packet['native_tick']],'ONLINE_SCAN_NOT_ORIGINAL_MEASUREMENT'
        actual=tracker.update(packet)
        periodic.update(actual['time'],actual['native_tick'],expected['support_bounds'])
        periodic_states[actual['native_tick']]=None if periodic.last is None else periodic.snapshot()
        for key,value in actual.items():
            if key in ['support_bounds','position_polygon']and value is not None:assert np.allclose(value,expected[key],rtol=0,atol=1e-10),'CAUSAL_SUPPORT_CHANGED'
            else:assert value==expected[key],'CAUSAL_METADATA_CHANGED'
        states[packet['native_tick']]=expected
        if actual['information_mode']=='TRACKED':
            c=setup['actor'];xy=np.asarray(c['anchor_xy'])+np.asarray(c['axis_xy'])*c['amplitude_m']*math.sin(c['omega_rad_s']*packet['time']+c['phase_rad'])
            assert np.max(NORMALS@xy-np.asarray(actual['support_bounds']))<=1e-8,'TRUE_CENTER_OUTSIDE_ENCLOSURE';covered+=1
    def rebuild(source):
        state=states[source['source_native_tick']];assert state['time']==source['source_scan_sim_time']
        age=source['forecast_sim_time']-state['time'];assert -.00001<=age<=.25001,'FORECAST_SOURCE_AGE'
        b=state['support_bounds']
        if 'center_support_bounds'in source:
            center=source['center_support_bounds'];assert (center is None and b is None)or(center is not None and b is not None and np.allclose(center,b,rtol=0,atol=1e-10)),'EXIT_SOURCE_CENTER_NOT_CAUSAL'
            assert abs(source['source_age_s']-age)<=1e-8,'EXIT_SOURCE_AGE_NOT_CAUSAL'
        horizon=HORIZON
        latency=MAP_LATENCY_RESERVE
        expected=None if b is None else np.asarray(b)+.1+.08*(max(0.,age)+horizon+latency)
        prior=periodic_states[source['source_native_tick']]
        if expected is not None and prior is not None:
            expected=np.minimum(expected,swept_bounds(prior['vertices'],state['time'],source['forecast_sim_time']+horizon+latency)+.1)
        if 'reference_support'in source:
            current=expected
            assert (current is None and source['reference_support']is None)or np.allclose(current,source['reference_support'],rtol=0,atol=1e-10),'REFERENCE_NOT_CURRENT_CAUSAL'
            assert source['reference_horizon_s']==HORIZON and source['reference_is_execution_certificate']is False
        assert (expected is None and source['forecast_support']is None)or(expected is not None and np.allclose(expected,source['forecast_support'],rtol=0,atol=1e-10)),'FORECAST_NOT_CAUSAL'
        return None if expected is None else np.asarray(source['forecast_support'])
    tubes=json.loads(gzip.decompress((out/'COMMAND_TUBES.json.gz').read_bytes()))
    future_checks=0
    for row in tubes:
        source=row['source'];prior=periodic_states[source['source_native_tick']]
        recorded=source.get('periodic')
        assert (recorded is None)==(prior is None),'PERIODIC_SNAPSHOT_MISSING'
        if prior is not None:
            assert all(recorded[k]==prior[k]for k in ['omega','amplitude','last','source_tick']),'PERIODIC_SNAPSHOT_METADATA'
            assert all(np.asarray(a).shape==np.asarray(b).shape and np.allclose(a,b,rtol=0,atol=1e-9)for a,b in zip(recorded['vertices'],prior['vertices'])),'PERIODIC_SNAPSHOT_NOT_CAUSAL'
        if prior is not None:
            from periodic_support import bounds_from_vertices
            at=source['source_scan_sim_time']+np.arange(0.,2.501,.01)
            high=bounds_from_vertices(prior['vertices'],at)
            c=setup['actor'];truth=np.asarray(c['anchor_xy'])+np.sin(c['omega_rad_s']*at+c['phase_rad'])[:,None]*c['amplitude_m']*np.asarray(c['axis_xy'])
            assert abs(c['omega_rad_s']-.32)<1e-12,'NEW_PERIODIC_CLASS_MISMATCH'
            assert np.max(truth@NORMALS.T-high)<=1e-8,'PERIODIC_FUTURE_COVERAGE_FAILED'
            future_checks+=high.size
    tracked=0
    for row in journal['publications']:
        b=rebuild(row);grid=raster_support(b)
        if row['map_role']=='GLOBAL_REFERENCE':grid[grid>0]=100
        assert hashlib.sha256(grid.tobytes()).hexdigest()==row['map_sha256'],'FORECAST_MAP_SHA'
        tracked+=b is not None
    cfg=json.loads(Path(json.loads((out/'TASK.json').read_text())['nav2_params']).read_text())
    vertices=json.loads(cfg['global_costmap']['global_costmap']['ros__parameters']['footprint'])
    routes=json.loads((out/'ROUTER_REQUESTS.json').read_text());route_checks=0
    for row in routes:
        if 'causal_forecast_source'not in row:continue
        b=rebuild(row['causal_forecast_source']);b=row['causal_forecast_source']['reference_support'];g=row['original_goal'];_,choice=terminal_goal(pose(*g),setup['known'],None if b is None else polygon(b),vertices)
        expected=row['terminal_region_choice']
        if row.get('navigation_role')=='REFUGE':
            assert expected['reason']=='EXACT_CAUSAL_BREADCRUMB_REFUGE'
            if row.get('passed'):
                from refuge_logic import exit_path_ok
                source=row['causal_forecast_source'];age=row['exit_contract_source_age_s'];assert source['source_age_s']<=age<=source['source_age_s']+row['wall_s']+1e-5
                actual=exit_path_ok(row['refuge_returned_path'],source['center_support_bounds'],age,setup['known']);assert actual==row['refuge_path_contract']and actual['passed'],'RETURNED_REFUGE_PATH_NOT_INDEPENDENTLY_ADMITTED'
            route_checks+=1;continue
        assert choice['reason']==expected['reason']
        if 'selected_xy'in choice:assert np.allclose(choice['selected_xy'],expected['selected_xy'],rtol=0,atol=1e-10),'TERMINAL_NOT_CAUSAL'
        if row.get('returned_error_code')==208:assert row['reverse_search']and row['smac_error_code']==205,'ACTUAL_START_ERROR_REMAPPED'
        if row.get('passed'):assert row['endpoint_distance_to_original_goal_m']<=.240000001
        route_checks+=1
    snapshots=json.loads((out/'COSTMAP_SNAPSHOT_INDEX.json').read_text());kinds=set();after={k:0 for k in ['global_costmap','local_costmap']}
    first=min((p['at']for p in journal['publications']if p['forecast_support']is not None),default=float('inf'))
    for row in snapshots:
        assert abs(row['resolution']-.01)<1e-8
        with np.load(out/row['path'])as z:assert len(z['data'])==row['width']*row['height']
        kinds.add(row['kind'])
        if row['at']>first+.5:after[row['kind']]+=1
    assert {r.get('map_role')for r in journal['publications']}=={'GLOBAL_REFERENCE','LOCAL_EXECUTION'},'MISSING_SEPARATE_MAP_ROLES'
    passed=not journal['truth_used']and covered>0 and tracked>0 and kinds==set(after)and all(after.values())and route_checks>0
    result=dict(passed=bool(passed),original_observations_verified=len(journal['observations']),tracked_states_with_offline_true_center_covered=covered,forecast_publications_rebuilt=len(journal['publications']),tracked_forecast_publications=tracked,causal_terminal_decisions_rebuilt=route_checks,actual_costmap_snapshot_kinds=sorted(kinds),postdetection_full_snapshots=after,models=0,integrations=0,periodic_future_support_checks=future_checks,declared_periodic_class_only=True,scope='Causal observation/coefficient-set/forecast/terminal reconstruction and recorded native truth coverage. Known-frequency course only; not arbitrary-speed class or recursive safety')
    (out/'MOTION_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
