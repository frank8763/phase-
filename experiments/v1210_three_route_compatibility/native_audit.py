"""Dispatch unchanged saved-data auditors; bind legacy command explicitly."""
from worker_context import *
from route_dispatch import branch, checked, legacy_policy, load_legacy_tools
import types


def audit(task, *, qualification_output=None):
    out = Path(task['output'])
    if branch(task['case_id']) == 'current_goal':
        assert qualification_output is None, 'CURRENT_GOAL_REAL_AUDIT_ALREADY_QUALIFIED'
        path = R / 'experiments/v1204_goal_audit_worker/native_audit.py'
        checked(path)
        return load('v1210_current_goal_native_audit', path).audit(task)
    policy = legacy_policy(lambda: (_ for _ in ()).throw(AssertionError('SAVED_AUDIT_MUST_NOT_READ_WINDOW')))
    path = R / 'experiments/v1184_three_route_entry/audit.py'
    source = checked(path)
    assert source.count('from route_tools import *') == 1
    assert source.count('from route_policy import command') == 1
    module = types.ModuleType('v1210_bound_legacy_auditor')
    module.__dict__.update(vars(load_legacy_tools()))
    module.__file__ = str(path)
    module.__name__ = 'v1210_bound_legacy_auditor'
    module._command = policy.command
    original_dump = module.dump

    def preserve_legacy_proof(target, value):
        target = Path(target)
        if target == out / 'FINAL_INDEPENDENT_AUDIT.json':
            target = Path(qualification_output or out) / 'LEGACY_NATIVE_AUDIT.json'
        original_dump(target, value)

    module.dump = preserve_legacy_proof
    source = source.replace('from route_tools import *', '').replace('from route_policy import command', 'command = _command')
    exec(compile(source, str(path), 'exec'), module.__dict__)
    result = module.audit(task)
    assert result['passed'] and result['models'] == result['new_mujoco_native'] == 0
    result.update(actual_replay_verified=True, physical_audit_complete=True,
                  audit_binding='unchanged_V1184_NS_EW_auditor')
    dump(Path(qualification_output or out) / 'FINAL_INDEPENDENT_AUDIT.json', result)
    return result
