"""Freeze the short component, current dependencies, and upstream software proof."""
from common import *


def main():
    assert not (C / 'SOURCE_FREEZE.json').exists(), 'ALREADY_FROZEN'
    software = read(R / 'runs/v1288_baseline_interface/CONTROLLER_RESULT.json')
    passed = [x for x in software['cases'] if x['plugin'] == 'RPP']
    assert len(passed) == 4 and all(x['passed'] for x in passed), 'RPP_SOFTWARE_REQUIRED'
    cfg = read(R / 'experiments/v1288_baseline_interface/params.json')
    parameters = cfg['controller_server']['ros__parameters']; parameters['controller_plugins'] = ['RPP']; parameters.pop('MPPI')
    parameters['goal_checker']['xy_goal_tolerance'] = .08
    parameters['progress_checker']['movement_time_allowance'] = 60.
    cfg['local_costmap']['local_costmap']['ros__parameters']['footprint'] = '[[0.44,0.375],[0.44,-0.375],[-0.44,-0.375],[-0.44,0.375]]'
    dump(C / 'params.json', cfg)
    original = read(R / 'experiments/v1281_partial_reconnection_fixed24/TASK_main_slot01.json'); tasks = []
    for role in ['main', 'repeat']:
        task = dict(original, task_id=role, run_id='v1290-' + role, role=role,
                    output=str(O / role), run_root=str(O), scope='current_adapter_rpp_straight_component',
                    component_goal_xy=[-2.8, -2.], native_limit=6000)
        tasks.append(task)
    dump(C / 'TASKS.json', tasks)
    dump(C / 'TASKS_entry.json', tasks[0])
    parent = read(R / 'experiments/v1281_partial_reconnection_fixed24/WORKER_FREEZE.json')['files']
    paths = [R / p for p in parent if (R / p).is_file()]
    # The source dependency snapshot must remain available after the raw-evidence cleanup.
    source_missing = [p for p in parent if p.startswith(('experiments/', 'runtime/', 'current/')) and not (R / p).is_file()]
    assert not source_missing, 'CURRENT_SOURCE_DEPENDENCY_MISSING ' + str(source_missing[:3])
    paths += [*C.glob('*.py'), C / 'PROTOCOL.md', C / 'params.json', C / 'TASKS.json', C / 'TASKS_entry.json',
              R / 'experiments/v1288_baseline_interface/contract.py',
              R / 'runs/v1288_baseline_interface/CONTROLLER_RESULT.json',
              R / 'experiments/v856_nav2_foundation/ros_environment.py']
    paths += [R / p for p in read(R / 'experiments/v1288_baseline_interface/SOURCE_FREEZE.json')['files']]
    dump(C / 'SOURCE_FREEZE.json', dict(files={str(p.relative_to(R)): sha(p) for p in sorted(set(paths))},
                                       physical_models_before_freeze=0, component_tasks=2,
                                       old_raw_evidence_not_required=True))
    print(json.dumps(dict(prepared=True, frozen_files=len(set(paths)), models=0)))


if __name__ == '__main__':
    main()
