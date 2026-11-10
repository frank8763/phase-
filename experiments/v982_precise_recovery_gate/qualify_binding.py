"""Check actual worker imports and captured-pose online/audit agreement; zero models."""
import importlib.abc
import inspect
import json
from pathlib import Path
import sys

C=Path(__file__).parent;R=C.resolve().parents[1];O=R/'runs/v982_precise_recovery_gate'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))

def main():
    import ros_worker
    from transaction import TrackingGuard
    saved=R/'runs/v980_recovery_actuation_postmortem'
    plan=json.loads((saved/'COMPONENT_REFERENCE.json').read_text())['proposal']
    packet=json.loads((saved/'ONLINE_TRACKING_FAULT.json').read_text())['packet']
    guard=TrackingGuard(plan);guard.mode='FOLLOW_RECOVERY'
    try:guard.monitor_body(packet);accept=True;error=None
    except AssertionError as e:accept=False;error=str(e)
    checks=dict(actual_ros_bridge_uses_this_source=ros_worker.engine.C.resolve()==C.resolve(),
                actual_guard_declared_precision='tracking.py'==Path(inspect.getsourcefile(TrackingGuard)).name,
                saved_fault_not_refused_by_coarse_guard=accept)
    if '--baseline'not in sys.argv:
        from independent_tracking import check
        import audit
        offline=check(plan,[packet['body'][:3]])
        checks['offline_same_original_limits']=offline['passed']and offline['unchanged_heading_limit_rad']==.035 and offline['unchanged_position_limit_m']==.04
        checks['independent_audit_bound_to_precise_tracking']=audit.dense_tracking is check
    result=dict(passed=all(checks.values()),checks=checks,error=error,models=0,integrations=0)
    name='BASELINE_BINDING_RED.json'if'--baseline'in sys.argv else'BINDING_QUALIFICATION.json'
    (O/name).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    if '--baseline'in sys.argv:assert not result['passed']
    else:assert result['passed']
if __name__=='__main__':main()
