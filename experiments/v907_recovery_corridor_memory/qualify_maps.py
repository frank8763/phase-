"""Real publisher on original measured scans; zero ROS and vehicle imports."""
import copy,gzip,hashlib,importlib.abc,json,sys,threading,types
from pathlib import Path
from unittest.mock import patch
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v907_recovery_corridor_memory'
sys.path.insert(0,str(C))
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,*args):
        if fullname.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('FORBIDDEN_MODEL_OR_ROS')
sys.meta_path.insert(0,Block())
import motion_publisher as production
from support_envelope import SupportEnvelope,raster_support,polygon,HORIZON,MAP_LATENCY_RESERVE
from exact_lidar import get_lidar_features
known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
source=R/'runs/v858_nav2_verified/v903/main_we'
scans=json.loads(gzip.decompress((source/'physics/SENSORS.json.gz').read_bytes()))
tracker=SupportEnvelope(known,get_lidar_features)
for scan in scans:
    if scan['time']>52.27:break
    if tracker.when is None or scan['time']>tracker.when:tracker.update({k:scan[k]for k in ['native_tick','time','xy','yaw','ranges']})
def message():return types.SimpleNamespace(header=types.SimpleNamespace(stamp=None,frame_id=None),info=types.SimpleNamespace(resolution=0.,width=0,height=0,origin=types.SimpleNamespace(position=types.SimpleNamespace(x=0.,y=0.),orientation=types.SimpleNamespace(w=1.))),data=None)
local=[];global_=[];p=production.MotionPublisher.__new__(production.MotionPublisher)
p.tracker=tracker;p.lock=threading.RLock();p.scan_monotonic=99.98;p.running=True;p.publications=[];p.msg_type=message
p.publisher=types.SimpleNamespace(publish=lambda x:local.append(copy.deepcopy(x)));p.reference_publisher=types.SimpleNamespace(publish=lambda x:global_.append(copy.deepcopy(x)))
p.node=types.SimpleNamespace(get_clock=lambda:types.SimpleNamespace(now=lambda:types.SimpleNamespace(to_msg=lambda:0)))
with patch.object(production.time,'monotonic',lambda:100.):
    p.publish();poly,meta=p.forecast_for_planner()
    bounds=tracker.forecast(tracker.when+.02);expected=raster_support(bounds)
    a=np.asarray(local[0].data,dtype=np.int8).reshape(1000,1000);b=np.asarray(global_[0].data,dtype=np.int8).reshape(1000,1000)
    checks=dict(actual_module=Path(production.__file__).parent==C,one_hard_and_one_soft=len(local)==len(global_)==1,
                local_original_future_array_exact=np.array_equal(a,expected),global_identical_support=np.array_equal(a>0,b>0),global_cost50=np.array_equal(b,a//2),
                source_support_preserved=np.allclose(meta['center_support_bounds'],tracker.support),same_original_horizon=meta['reference_horizon_s']==HORIZON,
                planner_polygon_exact=np.allclose(poly,polygon(bounds)),reference_not_execution_certificate=meta['reference_is_execution_certificate']is False,
                local_role=p.publications[0]['map_role']=='LOCAL_EXECUTION',global_role=p.publications[1]['map_role']=='GLOBAL_REFERENCE',
                sha_local=hashlib.sha256(a.tobytes()).hexdigest()==p.publications[0]['map_sha256'],sha_global=hashlib.sha256(b.tobytes()).hexdigest()==p.publications[1]['map_sha256'])
    p.scan_monotonic=99.
    try:p.publish()
    except RuntimeError:checks['reject_stale_actual_scan']=True
    else:checks['reject_stale_actual_scan']=False
old=json.loads((R/'experiments/v903_retained_exit_reference/A_motion.yaml').read_text());new=json.loads((C/'A_motion.yaml').read_text())
checks['local_configuration_byte_values_unchanged']=old['local_costmap']==new['local_costmap']
checks['controller_unchanged']=old['controller_server']==new['controller_server']
checks['smac_limits_unchanged']=old['planner_server']==new['planner_server']
checks['global_raw_scan_layer_unchanged']=old['global_costmap']['global_costmap']['ros__parameters']['obstacle_layer']==new['global_costmap']['global_costmap']['ros__parameters']['obstacle_layer']
checks['genuine_master_and_route_probe']=json.loads((R/'runs/v904_reference_map_qualification/ros_soft_verified/RESULT.json').read_text())['passed']
result=dict(passed=all(checks.values()),checks={k:bool(v)for k,v in checks.items()},models=0,integrations=0,occupied_cells=int(np.count_nonzero(a)),scope='Exact production publish and causal source with real saved scans; separate genuine Smac/master readback qualification. No physical arrival claim.')
(O/'MAP_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
