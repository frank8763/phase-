"""Generate a fixed two-factor software study without modifying frozen V1288."""
import copy
import hashlib
import json
from pathlib import Path
R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
B = R / 'experiments/v1288_baseline_interface'


def write(path, x):
    path.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    assert not (C / 'SOURCE_FREEZE.json').exists(), 'ALREADY_FROZEN'
    for name in ['contract.py', 'qualify_contract.py', 'run_software.py']:
        (C / name).write_bytes((B / name).read_bytes())
    source = (B / 'controller_probe.py').read_text()
    before = "len(result['cases']) == 8"
    assert source.count(before) == 1
    (C / 'controller_probe.py').write_text(source.replace(before, "len(result['cases']) == len(cases)"))
    cfg = json.loads((B / 'params.json').read_text())
    p = cfg['controller_server']['ros__parameters']
    original = copy.deepcopy(p.pop('MPPI'))
    p.pop('RPP')
    variants = [('MPPI_original', False, 1.4), ('MPPI_threshold', False, .1),
                ('Adapted_original', True, 1.4), ('Adapted_threshold', True, .1)]
    p['controller_plugins'] = [x[0] for x in variants]
    tasks = []
    fixtures = [t for t in json.loads((B / 'TASKS.json').read_text()) if t['plugin'] == 'MPPI']
    for name, adapted, threshold in variants:
        params = copy.deepcopy(original)
        if adapted:
            params['plugin'] = 'phase_predictive/ExecutableMPPI'
        params['PathFollowCritic']['threshold_to_consider'] = threshold
        p[name] = params
        for t in fixtures:
            task = copy.deepcopy(t)
            task['id'], task['plugin'] = name + '_' + t['kind'], name
            tasks.append(task)
    write(C / 'TASKS.json', tasks)
    write(C / 'params.json', cfg)
    # Only library discovery changes; algorithms/fixture/validator remain explicit.
    runner = (C / 'run_software.py').read_text()
    anchor = "env = envmod.environment()"
    assert runner.count(anchor) == 1
    runner = runner.replace(anchor, anchor + "\n        env['AMENT_PREFIX_PATH'] = str(R / 'runs/v929_executable_mppi/install') + ':' + env['AMENT_PREFIX_PATH']\n        env['LD_LIBRARY_PATH'] = str(R / 'runs/v929_executable_mppi/install/lib') + ':' + env['LD_LIBRARY_PATH']")
    (C / 'run_software.py').write_text(runner)
    previous = json.loads((R / 'experiments/v929_executable_mppi/SOURCE_FREEZE.json').read_text())['files']
    installed = list((R / 'runs/v929_executable_mppi/install').rglob('*'))
    installed = [f for f in installed if f.is_file()]
    for f in installed:
        assert hashlib.sha256(f.read_bytes()).hexdigest() == previous[str(f.relative_to(R))], 'OLD_ADAPTER_BINARY_OR_DESCRIPTOR_CHANGED'
    parents = [R / path for path in json.loads((B / 'SOURCE_FREEZE.json').read_text())['files']]
    paths = sorted(set([*C.glob('*.py'), C / 'PROTOCOL.md', C / 'TASKS.json', C / 'params.json', *installed, *parents]))
    write(C / 'SOURCE_FREEZE.json', dict(files={str(f.relative_to(R)): hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},
                                        parent_harness_changes=['case count compares with explicit task table length'],
                                        variants=variants, physical_models=0))
    print(json.dumps(dict(prepared=True, configurations=4, software_actions=len(tasks), models=0)))


if __name__ == '__main__':
    main()
