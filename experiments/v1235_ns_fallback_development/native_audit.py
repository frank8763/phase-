"""Dispatch unchanged saved-data auditors; bind legacy command explicitly."""
from worker_context import *
from route_dispatch import branch, checked, legacy_policy, load_legacy_tools
import types


def audit(task, *, qualification_output=None):
    out = Path(task['output'])
    if branch(task['case_id']) == 'ns_goal':
        return load('v1235_ns_native_audit',C/'ns_audit.py').audit(task,qualification_output=qualification_output)
    if branch(task['case_id']) == 'current_goal':
        assert qualification_output is None, 'CURRENT_GOAL_REAL_AUDIT_ALREADY_QUALIFIED'
        path = R / 'experiments/v1204_goal_audit_worker/native_audit.py'
        checked(path)
        parent=load('v1235_current_goal_native_audit',path)
        original_dump=parent.dump
        def preserve_base(target,value):
            target=Path(target)
            if target==out/'FINAL_INDEPENDENT_AUDIT.json':target=out/'BASE_CURRENT_GOAL_NATIVE_AUDIT.json'
            original_dump(target,value)
        parent.dump=preserve_base
        result=parent.audit(task)
        verify_bundle=load('phase_v1235_admission_auditor',C/'audit_admission.py').verify_bundle
        bundle=parent.load_bundle(out/'CURRENT_GOAL_ENTRY')
        with parent.np.load(out/'LIVE_GOAL_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
        admission=verify_bundle(read(out/'LIVE_GOAL_INPUT.json'),table,bundle,time.monotonic()+100)
        stop_audit=load('v1235_stop_reserve_audit',R/'experiments/v1219_stop_preserving_observer/audit_observer.py').verify_selected(out,time.monotonic()+150)
        exact=load('v1235_independent_exact_selection',R/'experiments/v1221_exact_stop_pruning/audit_selection.py')
        with parent.np.load(out/'LIVE_OBSERVER_TABLE.npz')as z:observer_table={k:z[k].copy()for k in z.files}
        selector=exact.verify(read(out/'LIVE_OBSERVER_INPUT.json'),observer_table,read(out/'LIVE_OBSERVER_SELECTION.json'),time.monotonic()+100)
        result.update(admission=admission,stop_reserve=stop_audit,exact_selection=selector,analytical_cpp_native=result['analytical_cpp_native']+admission['analytical_cpp_native']+stop_audit['analytical_cpp_native']+selector['analytical_cpp_native'])
        dump(out/'FINAL_INDEPENDENT_AUDIT.json',result)
        return result
    policy = legacy_policy(lambda: (_ for _ in ()).throw(AssertionError('SAVED_AUDIT_MUST_NOT_READ_WINDOW')))
    path = R / 'experiments/v1184_three_route_entry/audit.py'
    source = checked(path)
    assert source.count('from route_tools import *') == 1
    assert source.count('from route_policy import command') == 1
    module = types.ModuleType('v1235_bound_legacy_auditor')
    module.__dict__.update(vars(load_legacy_tools()))
    module.__file__ = str(path)
    module.__name__ = 'v1235_bound_legacy_auditor'
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
