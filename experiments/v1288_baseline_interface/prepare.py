"""Prepare finite software fixtures and freeze them before actual plugin calls."""
import hashlib
import json
import math
from pathlib import Path

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent


def write(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    assert not (C / 'SOURCE_FREEZE.json').exists(), 'ALREADY_FROZEN'
    old = json.loads((R / 'experiments/v929_executable_mppi/params.yaml').read_text())
    rpp = json.loads((R / 'experiments/v863_rpp_preparation/nav2_params.yaml').read_text())
    params = old['controller_server']['ros__parameters']
    params['controller_plugins'] = ['RPP', 'MPPI']
    params['goal_checker_plugins'] = ['goal_checker']
    params['goal_checker'] = params.pop('general_goal_checker')
    params['enable_stamped_cmd_vel'] = False
    params['MPPI'] = params.pop('FollowPath')
    params['MPPI']['plugin'] = 'nav2_mppi_controller::MPPIController'
    params['RPP'] = rpp['controller_server']['ros__parameters']['FollowPath']
    params['RPP']['desired_linear_vel'] = .1
    params['RPP']['regulated_linear_scaling_min_speed'] = .05
    local = rpp['local_costmap']['local_costmap']['ros__parameters']
    local['plugins'] = ['obstacle_layer', 'inflation_layer']
    local.pop('static_layer', None)
    local.pop('voxel_layer', None)
    cfg = dict(controller_server=dict(ros__parameters=params),
               local_costmap=dict(local_costmap=dict(ros__parameters=local)))
    write(C / 'params.json', cfg)
    fixtures = []
    for plugin in ['RPP', 'MPPI']:
        for kind, turn in [('straight', 0), ('left', 1), ('right', -1), ('goal', 0)]:
            path = []
            for i in range(61):
                t = .6 * i / 60
                path.append([-4. + 2 * math.sin(t), -2. + turn * 2 * (1 - math.cos(t)), turn * t]
                            if turn else [-4. + (0 if kind == 'goal' else 1.2 * i / 60), -2., 0.])
            fixtures.append(dict(id=plugin.lower() + '_' + kind, plugin=plugin, kind=kind, turn=turn, path=path))
    write(C / 'TASKS.json', fixtures)
    paths = [*C.glob('*.py'), C / 'PROTOCOL.md', C / 'TASKS.json', C / 'params.json',
             R / 'experiments/v856_nav2_foundation/ros_environment.py']
    installed = R / 'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy'
    paths += [installed / 'lib/nav2_controller/controller_server', installed / 'lib/libmppi_controller.so',
              installed / 'lib/libnav2_regulated_pure_pursuit_controller.so',
              installed / 'share/nav2_mppi_controller/package.xml',
              installed / 'share/nav2_regulated_pure_pursuit_controller/package.xml']
    write(C / 'SOURCE_FREEZE.json', dict(files={str(p.relative_to(R)): hashlib.sha256(p.read_bytes()).hexdigest()
                                               for p in sorted(paths)},
                                        generated_before_controller_actions=True))
    print(json.dumps(dict(prepared=True, cases=len(fixtures), models=0, physical_native=0)))


if __name__ == '__main__':
    main()
