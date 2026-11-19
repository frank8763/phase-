"""Freeze fixed saved input data and controller configuration; zero models."""
import ast
import gzip
import math
from common import *


def main():
    O.mkdir(exist_ok=False)
    sensor_path = R / 'runs/v858_nav2_verified/v1348/rpp_async_default_dynamic_main/physics/SENSORS.json.gz'
    sensors = json.load(gzip.open(sensor_path, 'rt'))
    grid_path = R / 'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json'
    static = read(grid_path)
    files = [sensor_path, grid_path]
    inputs, tasks = [], []
    rpp_path = R / 'experiments/v1348_recoverable_tracking/rpp_async_default_params.json'
    mppi_path = R / 'experiments/v1341_overnight_baseline_relay/coherent_mppi_params.json'
    rpp, mppi = read(rpp_path), read(mppi_path)
    assert rpp['local_costmap'] == mppi['local_costmap'], 'PREEXISTING_COMMON_MAP_DIFFERENCE'
    common = dict(rpp['controller_server']['ros__parameters'])
    specific_mppi = mppi['controller_server']['ros__parameters']['Deadband']
    mppi['controller_server']['ros__parameters'] = {k: v for k, v in common.items() if k != 'RPP'}
    mppi['controller_server']['ros__parameters'].update(controller_plugins=['Deadband'], Deadband=specific_mppi)
    for method, params in [('rpp', rpp), ('mppi', mppi)]:
        dump(C / (method + '_params.json'), params)
    files += [rpp_path, mppi_path]
    for index in [1, 4, 8]:
        source = R / ('runs/v1350_bounded_complete_search/RESULT_%02d_MODE0.json' % index)
        saved = read(source)
        assert saved['summary']['geometry_passed'] and saved['summary']['same_shape_as_python']
        req, segment = saved['request'], first_segment(saved['path'])
        packet = max((p for p in sensors if p['native_tick'] <= req['native_tick']), key=lambda p: p['native_tick'])
        center = req['body']
        rear = [center[0]-.3*math.cos(center[2]), center[1]-.3*math.sin(center[2]), center[2], 0., 0.]
        assert len(packet['ranges']) == 32 and all(math.isfinite(v) and 0 <= v <= 3 for v in packet['ranges'])
        assert math.dist(rear[:2], segment['poses'][0][:2]) < 1e-10
        grid, cells = raster_ball(static, req['ball'])
        value = dict(saved_request=index, fixture=dict(body=rear, ranges_m=packet['ranges']), segment=segment,
                     map_grid=grid, original_body=center, original_goal=req['goal'], original_goal_radius_m=.45,
                     causal_ball=req['ball'], native_tick=req['native_tick'], original_sim_time=req['sim_time'],
                     source_sensor=dict(native_tick=packet['native_tick'], time=packet['time'], xy=packet['xy'], yaw=packet['yaw']),
                     sensor_age_at_saved_request_s=req['sim_time']-packet['time'], ball_raster_cells=cells,
                     source_result=str(source.relative_to(R)), source_result_sha256=sha(source),
                     source_sensor_archive_sha256=sha(sensor_path), synthetic_stationary_zero_velocity=True,
                     complete_goal_path=False, reused_dense_geometry_audit=saved['summary']['numpy_validation'])
        value['common_input_sha256'] = digest(value)
        dump(C / ('INPUT_%02d.json' % index), value)
        inputs.append(value)
        files.append(source)
        for method, plugin in [('rpp', 'RPP'), ('mppi', 'Deadband')]:
            tasks.append(dict(id='saved%02d_%s' % (index, method), saved_request=index, method=method, plugin=plugin,
                              input_file=str((C / ('INPUT_%02d.json' % index)).relative_to(R)), common_input_sha256=value['common_input_sha256']))
    dump(C / 'TASKS.json', tasks)
    # Focused changed-boundary checks; unchanged legacy contract is reused by SHA.
    sample = dict(resolution=1., width=3, height=3, origin=[0., 0.], data=[0]*9)
    painted, count = raster_ball(sample, [1.5, 1.5, .51])
    assert count == 5 and painted['data'][4] == 100 and sample['data'] == [0]*9
    assert first_segment([[0,0,0,1],[1,0,0,1],[2,0,0,-1]]) == dict(gear=1, poses=[[0,0,0],[1,0,0]])
    for bad in [[], [[0,0,0,1]], [[0,0,0,1],[1,0,0,0]]]:
        try: first_segment(bad)
        except AssertionError: pass
        else: raise AssertionError('MALFORMED_PATH_NOT_REJECTED')
    for value in inputs:
        original = value['common_input_sha256']
        clone = dict(value); clone.pop('common_input_sha256')
        assert digest(clone) == original
        clone['causal_ball'] = [*clone['causal_ball'][:2], clone['causal_ball'][2]+.01]
        assert digest(clone) != original
    for p in C.glob('*.py'): ast.parse(p.read_text(), filename=str(p))
    dump(O / 'INPUT_QUALIFICATION.json', dict(passed=True, fixed_inputs=3, cases=6, conservative_cell_intersection=True,
         first_incoming_gear_segment=True, malformed_path_negative_cases=3, causal_ball_mutation_detected=3,
         same_common_costmap_parameters=True, models=0, physical_native=0))
    files += [R/'experiments/v1288_baseline_interface/contract.py', R/'experiments/v856_nav2_foundation/ros_environment.py',
              R/'runs/v1340_overnight_preparation/install/lib/libphase_executable_rpp.so',
              R/'runs/v931_deadband_consistent_mppi/install/lib/libphase_deadband_mppi.so',
              R/'runs/v1319_mppi_coherent_sampling/libcoherent.so',
              R/'runs/v1351_speed_comparison_plan/CPU_TOPOLOGY_RECEIPT.json']
    for install in ['v1340_overnight_preparation', 'v931_deadband_consistent_mppi']:
        files += [p for p in (R/'runs'/install/'install/share').rglob('*') if p.is_file()]
    files += [p for p in C.iterdir() if p.is_file() and p.name != 'SOURCE_FREEZE.json']
    dump(C / 'SOURCE_FREEZE.json', dict(scope='six stationary software cases; no models', files={str(p.relative_to(R)): sha(p) for p in sorted(set(files))}))
    print(json.dumps(dict(prepared=True, inputs=3, tasks=6, models=0, physical_native=0)))


if __name__ == '__main__': main()
