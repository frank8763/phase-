"""Actual native entry denial and original frozen-source integrity checks."""
import ast
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

C = Path(__file__).parent
R = C.resolve().parents[1]
O = R/'runs/v981_tracking_evidence_closure'
sys.path.insert(0, str(C))
from baseline_red import NoModel
sys.meta_path.insert(0, NoModel())


def main():
    checks = {}
    native = subprocess.run([sys.executable, '-B', str(C/'native_worker.py')], cwd=R, capture_output=True, text=True, timeout=5)
    checks['actual_native_worker_denies_before_any_task_or_model_import'] = native.returncode != 0 and 'V981_SOURCE_ONLY_NO_MODEL_AUTHORITY' in native.stderr and 'ModuleNotFoundError' not in native.stderr
    spec = importlib.util.spec_from_file_location('v981_direct_engine_authority', C/'native_loop.py')
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    try:
        engine.run({}, {}, '')
    except PermissionError as error:
        checks['direct_native_engine_authority_denial'] = str(error) == 'V981_SOURCE_ONLY_NO_MODEL_AUTHORITY'
    else:
        checks['direct_native_engine_authority_denial'] = False
    old = {}
    for version in ['v977_state_consistent_recovery', 'v979_state_recovery_physical']:
        frozen = json.loads((R/'experiments'/version/'SOURCE_FREEZE.json').read_text())['files']
        missing, changed = [], []
        for name, digest in frozen.items():
            p=R/name
            if not p.is_file():
                missing.append(name)
            elif hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                changed.append(name)
        assert not changed
        if version.startswith('v977'):
            assert not missing
        else:
            assert len(missing)==13 and all(n.startswith('runs/v979_state_recovery_physical/prior_v974/') for n in missing)
        old[version] = dict(expected=len(frozen), present_unchanged=len(frozen)-len(missing), changed=changed,
                            previously_remote_verified_evicted_inputs=missing)
    checks['frozen_scientific_sources_unchanged'] = True
    for path in C.glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    checks['all_new_python_parses'] = True
    launch=ast.parse((C/'launch_one.py').read_text())
    function=next(n for n in launch.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    tree=ast.unparse(function)
    checks['launcher_calls_bounded_supervision_not_original_group_stop_loop'] = 'supervise_workers(jobs' in tree and 'stop(p)' not in tree
    checks['launcher_cannot_grade_unbound_physical_audit_as_pass'] = 'physical_audit_bound=False' in tree and 'source_only=True' in tree
    checks['guard_original_bytes'] = hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest() == '4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    report = dict(passed=all(checks.values()), checks=checks, original_freezes=old,
                  models=0, actual_native=0, private_native=0, replay_native=0,
                  physical_ready=False, models_authorized=False)
    (O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, old_frozen_sources_unchanged=True)))
    assert report['passed']


if __name__=='__main__':
    main()
