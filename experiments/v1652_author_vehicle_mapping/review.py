"""Source/text evidence, not optimizer execution or vehicle qualification."""
from pathlib import Path
import hashlib,json,time
R=Path(__file__).resolve().parents[2];D=R/'runs/v1650_comparison_completion/author_intake';O=R/'runs/v1652_author_vehicle_mapping'
def main():
 assert not(O/'REVIEW_ONCE_CLAIM.json').exists()
 (O/'REVIEW_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0))+'\n')
 saved=json.loads((D/'INTERFACE_CAPTURE_RESULT.json').read_text());assert saved['passed']and saved['read_requests']==18
 for row in saved['rows']:
  raw=(R/row['saved_path']).read_bytes();assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
  assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha1']
 def text(label,name):return(D/'upstream'/label/name).read_text()
 common=text('SVG_MPPI','src/mppi_controller/include/mppi_controller/common.hpp')
 state=common.split('namespace STATE_SPACE {',1)[1].split('};',1)[0]
 control=common.split('namespace CONTROL_SPACE {',1)[1].split('};',1)[0]
 assert 'static constexpr int dim = 5;'in state and 'static constexpr int dim = 1;'in control and 'static constexpr int steer = 0;'in control
 params=text('SVG_MPPI','src/mppi_controller/config/mppi_controller.yaml')
 assert 'thread_num: 12'in params and 'reference_speed: 1.5'in params
 teb=text('TEB','include/teb_local_planner/planner_interface.h')
 assert 'getVelocityCommand'in teb
 teb_body=text('TEB','src/optimal_planner.cpp');assert 'EDGE_KINEMATICS_CARLIKE'in teb_body
 rows=[dict(method='TEB',author_commit='9e55af4724310c34bcfa8cbb3b2783478c1a246a',author_has_car_kinematic_edge=True,control_api='getVelocityCommand(vx,vy,omega,look_ahead_poses)',remaining=['exact minimal g2o/ROS dependency build','measured body and actuator-state to planner-start binding','public map/causal obstacle input and full footprint model','raw bodytwist to qualified original executor; no hidden recovery or clipping','full from-t0 safety/stop/capture/replay and fair task budget']),dict(method='SVG-MPPI',author_commit='f4fb7b74f12d4568790213aab26dd6f0538d1925',state=['x','y','yaw','velocity','steer'],control=['steer'],state_dimension=5,control_dimension=1,remaining=['qualify equivalent steering mapping from actual wheel encoders and memory','publish longitudinal speed selection separately from steering optimization','replace author vehicle dimensions/speed/thread config only in explicit frozen adaptation','qualified original actuator response and fullfootprint/causal obstacle maps','exact CPU authorcore build plus actual/replay evidence'])]
 result=dict(closed=True,passed_source_content_review=True,actual_qualified=False,source_members_reverified=18,rows=rows,models=0,FFI_loads=0,compiled=False,numerical_calls=0,physical_native=0,replay_native=0,recorded_unix=time.time())
 (O/'SOURCE_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(source_review=True,methods=2,actual_qualified=False,models=0)))
if __name__=='__main__':main()
