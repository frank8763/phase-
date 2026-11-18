"""Freeze four fixed arc component tasks; geometric screening imports no model."""
import importlib.util
from types import SimpleNamespace
from component_context import *


def main():
    assert not (C / 'SOURCE_FREEZE.json').exists(), 'ALREADY_FROZEN'
    import numpy as np
    assert read(R / 'runs/v1294_rpp_output_scope/COMPLETION.json')['passed'], 'PREVIOUS_ACTUAL_COMPONENT_REQUIRED'
    cfg = read(R / 'experiments/v1294_rpp_output_scope/params.json')
    dump(C / 'params.json', cfg)
    original = read(R / 'experiments/v1281_partial_reconnection_fixed24/TASK_main_slot01.json')
    spec = importlib.util.spec_from_file_location('v1296_nominal_geometry', R / 'experiments/v802_exact_rejection_global/exact_footprint.py')
    geo = importlib.util.module_from_spec(spec); spec.loader.exec_module(geo)
    known = read(R / 'experiments/v1067_causal_replan_brake_reserve/KNOWN_FIELD.json')
    field = SimpleNamespace(half=np.array([.44,.375]), center_local=np.zeros(2), rectangles=np.array(known['known_rectangles']), circles=np.array(known['known_circles']), sensor_points=[], sensor_extra=0., config=SimpleNamespace(lower=-5.,upper=5.))
    tasks, screens = [], []
    for turn, sign in [('left', 1), ('right', -1)]:
        angles = np.linspace(0, .3, 1201)
        dense = np.c_[-4. + 4 * np.sin(angles), -2. + sign * 4 * (1 - np.cos(angles)), sign * angles]
        clear = geo.pose_values(field, dense)
        assert float(clear.min()) > .21 and 1.2 / 1200 <= .001000001, 'NOMINAL_ARC_CLEARANCE'
        screens.append(dict(turn=turn, nominal_minimum_clearance_m=float(clear.min()), maximum_arc_sample_spacing_m=.001, samples=len(dense), static_only=True, not_a_tracking_or_dynamic_safety_proof=True))
        angles = np.linspace(0, .3, 121)
        path = np.c_[-4. + 4 * np.sin(angles), -2. + sign * 4 * (1 - np.cos(angles)), sign * angles].tolist()
        for role in ['main','repeat']:
            name = turn + '_' + role
            task = dict(original, task_id=name, run_id='v1296-' + name, role=role, output=str(RAW / name), run_root=str(O),
                        scope='current_adapter_rpp_turn_brake_component', component_goal_xy=path[-1][:2], component_goal_yaw=sign*.3,
                        reference_path=path, arc_center=[-4., -2. + sign*4.], arc_radius_m=4., arc_length_m=1.2, turn_sign=sign, native_limit=6000)
            tasks.append(task)
    dump(C / 'TASKS.json', tasks); dump(C / 'TASKS_entry.json', tasks[0]); dump(C / 'GEOMETRY_QUALIFICATION.json', dict(passed=True, nominal_screens=screens, physical_models=0))
    parent = read(R / 'experiments/v1281_partial_reconnection_fixed24/WORKER_FREEZE.json')['files']
    paths = [R / p for p in parent if (R / p).is_file()]
    assert not [p for p in parent if p.startswith(('experiments/','runtime/','current/')) and not (R / p).is_file()], 'SOURCE_DEPENDENCY_MISSING'
    paths += [*C.glob('*.py'), *C.glob('*.json'), C/'PROTOCOL.md', O/'OUTPUT_SCOPE_QUALIFICATION.json',
              R/'experiments/v1288_baseline_interface/contract.py',R/'experiments/v856_nav2_foundation/ros_environment.py',
              R/'runs/v1294_rpp_output_scope/COMPLETION.json',R/'runs/v1294_rpp_output_scope/PAIR_COMPARISON.json',
              R/'experiments/v802_exact_rejection_global/exact_footprint.py', R/'experiments/v1067_causal_replan_brake_reserve/KNOWN_FIELD.json']
    paths += [R / p for p in read(R / 'experiments/v1288_baseline_interface/SOURCE_FREEZE.json')['files']]
    dump(C/'SOURCE_FREEZE.json',dict(files={str(p.relative_to(R)):sha(p)for p in sorted(set(paths))},physical_models_before_freeze=0,component_tasks=4))
    print(json.dumps(dict(prepared=True,tasks=4,frozen_files=len(set(paths)),nominal_geometry=screens,physical_models=0)))


if __name__ == '__main__':
    main()
