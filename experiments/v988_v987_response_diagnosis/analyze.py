"""Closed V987 actual response/complete stop tracking, zero new model work."""
import gzip,hashlib,importlib.abc,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v988_v987_response_diagnosis'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v987_bounded_startup_components'))
from independent_tracking import check
def read(n):return json.loads((O/n).read_text())
def main():
    for row in read('RESTORE_RECEIPT.json')['files']:assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256']
    n=read('RESULT.json');origin=n['historical_prefix_replay_native'];plan=read('COMPONENT_REFERENCE.json')['proposal'];fault=read('ONLINE_TRACKING_FAULT.json')
    with np.load(O/'physics/NATIVE_TRACE.npz')as z:
        q=z['qpos'];v=z['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
        body=np.c_[q[:,:2],yaw,v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw),v[:,5]]
    tracking=check(plan,body[origin:,:3]);fault_tracking=check(plan,[fault['packet']['body'][:3]])
    cut=fault['packet']['native_tick'];before_fault=check(plan,body[origin:cut-1,:3]);after_fault=check(plan,body[cut-1:,:3])
    travel=float(np.linalg.norm(np.diff(q[origin-1:,:2],axis=0),axis=1).sum())
    tubes=json.loads(gzip.decompress((O/'COMMAND_TUBES.json.gz').read_bytes()));act=read('ACTUATION_AUDIT.json');ros=read('ROS_RESULT.json')
    assert len(body)==n['actual_native']==6431 and n['new_branch_native']==348 and not tracking['passed']
    assert act['passed']and act['new_control_rows']==348 and act['feedback_rows']>0
    assert 'ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED'in ros['error']
    result=dict(models=0,integrations=0,original_outcome='V987_NOT_PASSED',primary_failure=ros['error'],
        exact_counts=dict(vehicle_tasks_initialized=1,historical_restore_native=6083,new_branch_native=348,whole_own_trace_replay_native=6431,private_native=0,second_component_unexecuted=True,new_navigation_trials=0,new24=0),
        startup_factory_and_restore_wall_s=n['timing_profile']['summaries']['factory_initialize']['inclusive_wall_s'],
        new_map_independently_reconstructed=act,full_new_branch_tracking=tracking,fault_tracking=fault_tracking,
        before_fault_tracking=before_fault,from_fault_through_complete_stop_tracking=after_fault,
        fault_native_tick=fault['packet']['native_tick'],fault_new_branch_tick=fault['packet']['native_tick']-origin,
        fault_body=fault['packet']['body'],fault_steering=fault['packet']['steering'],actual_new_branch_travel_m=travel,
        minimum_actual_clearance_m=n['minimum_actual_clearance_m'],bad_contacts=n['bad_contacts'],
        whole_replay=n['replay'],maximum_wall_lag_s=n['maximum_wall_lag_s'],maximum_observation_age_s=ros['maximum_observation_age_s'],
        alternate_motion_selections=sum(x.get('recovery')is not None for x in tubes),
        measured_new_step_p99_s=n['timing_profile']['summaries']['step_and_native_safety']['p99_s'],
        original_limits=dict(heading_rad=.035,position_m=.04,actual_clearance_m=.15),
        conclusion='Startup completed and V984 feedback was actually applied, with motor-map reconstruction and whole executed-state replay passing. Heading envelope still fails, including the complete stop tail. Rear-only yaw feedback alone is insufficient in this fixed state; unique plant/reference cause remains unproven. No new model, repair or repeat follows this closure.')
    (O/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
