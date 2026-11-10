"""Original online heading guard and full-stop saved-trace red loop, zero models."""
import hashlib,importlib.abc,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v989_actuation_reference_diagnosis'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v987_bounded_startup_components'))
from tracking import TrackingGuard
from independent_tracking import check
def main():
    for row in json.loads((O/'RESTORE_RECEIPT.json').read_text())['files']:
        assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256']
    plan=json.loads((O/'COMPONENT_REFERENCE.json').read_text())['proposal'];fault=json.loads((O/'ONLINE_TRACKING_FAULT.json').read_text())
    guard=TrackingGuard(plan);guard.mode='FOLLOW_RECOVERY'
    try:guard.monitor_body(fault['packet']);error=None
    except AssertionError as e:error=str(e)
    with np.load(O/'physics/NATIVE_TRACE.npz')as f:
        q=f['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));pose=np.c_[q[:,:2],yaw]
    full=check(plan,pose[6083:]);assert error=='ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED'and not full['passed']
    result=dict(passed=False,original_failure_reproduced=True,models=0,integrations=0,online_error=error,
        online_fault_proof=guard.last_proof,complete_new_native_samples=len(pose)-6083,full_stop_tracking=full,
        scope='Actual frozen guard on original saved packet; no new control response or physical predictions')
    (O/'BASELINE_RED.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
