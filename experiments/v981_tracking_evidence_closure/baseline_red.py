"""Exercise the original two bug seams, without model or ROS imports."""
import ast
import importlib.abc
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[2]
C = Path(__file__).parent
O = R/'runs/v981_tracking_evidence_closure'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'torch', 'vehicle', 'physical', 'factory', 'rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


def main():
    sys.meta_path.insert(0, NoModel())
    sys.path.insert(0, str(R/'experiments/v977_state_consistent_recovery'))
    from transaction import TrackingGuard
    saved = R/'runs/v980_recovery_actuation_postmortem'
    plan = json.loads((saved/'COMPONENT_REFERENCE.json').read_text())['proposal']
    fault = json.loads((saved/'ONLINE_TRACKING_FAULT.json').read_text())
    guard = TrackingGuard(plan)
    guard.mode = 'FOLLOW_RECOVERY'
    try:
        guard.monitor_body(fault['packet'])
    except AssertionError as error:
        refusal = str(error)
    else:
        refusal = None
    assert refusal == 'ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED'
    launcher = ast.parse((R/'experiments/v979_state_recovery_physical/launch_one.py').read_text())
    stop = next(n for n in launcher.body if isinstance(n, ast.FunctionDef) and n.name == 'stop')
    source = ast.unparse(launcher)
    assert "'FIRST_WORKER_FAILURE'" in source and 'for p in reversed(jobs):\n            stop(p)' in source
    namespace = dict(os=os, signal=signal, subprocess=subprocess)
    exec(compile(ast.Module(body=[stop], type_ignores=[]), '<original V979 stop>', 'exec'), namespace)
    out = O/'baseline_wrapper'
    out.mkdir(parents=True, exist_ok=False)
    child = subprocess.Popen([sys.executable, str(C/'process_fixture.py'), 'wrapper', str(out)], start_new_session=True)
    try:
        until = time.monotonic()+3
        while not (out/'READY').exists():
            assert child.poll() is None and time.monotonic() < until
            time.sleep(.005)
        namespace['stop'](child)
        saved_native = (out/'NATIVE_SAVED.json').exists()
        assert not saved_native
    finally:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=2)
    result = dict(passed=False, original_tracking_refusal=refusal,
                  original_group_stop_loses_child_evidence=not saved_native,
                  actual_original_functions_exercised=True,
                  models=0, integrations=0, physical_outcome_unchanged='V979_NOT_PASSED')
    (O/'BASELINE_RED.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
