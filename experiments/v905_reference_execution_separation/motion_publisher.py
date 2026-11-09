"""Same causal forecast, soft global reference and unchanged hard local execution."""
import array,hashlib,json,sys,threading,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v887_exact_lidar_software')]
from support_envelope import SupportEnvelope,raster_support,polygon,HORIZON,MAP_LATENCY_RESERVE
from exact_lidar import get_lidar_features
class MotionPublisher:
    def __init__(self,node,out):
        from nav_msgs.msg import OccupancyGrid
        from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
        from rclpy.callback_groups import ReentrantCallbackGroup
        self.node=node;self.out=Path(out);self.msg_type=OccupancyGrid;self.lock=threading.RLock();self.tracker=SupportEnvelope(json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text()),get_lidar_features)
        self.scan_monotonic=None;self.running=False;self.publications=[];self.observations=[];self.known_packets=0
        qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
        self.publisher=node.create_publisher(OccupancyGrid,'phase_dynamic_envelope',qos)
        self.reference_publisher=node.create_publisher(OccupancyGrid,'phase_dynamic_reference',qos)
        self.timer=node.create_timer(.2,self.publish,callback_group=ReentrantCallbackGroup())
    def observe(self,packet):
        with self.lock:
            self.running=packet['phase']!='WAITING'
            self.scan_monotonic=packet['scan_measured_at']if self.running else time.monotonic()
            scan=packet['scan']
            if self.tracker.when is not None and scan['time']==self.tracker.when:return
            clean={k:scan[k]for k in ['native_tick','time','xy','yaw','ranges']};self.tracker.update(clean);self.observations.append(clean);self.known_packets+=1
    def publish(self):
        now=time.monotonic()
        with self.lock:
            if self.tracker.when is None:return
            age=max(0.,now-self.scan_monotonic)
            if self.running and age>.25:raise RuntimeError('MOTION_ENVELOPE_SOURCE_STALE')
            sim=self.tracker.when+(age if self.running else 0.)
            bounds=self.tracker.forecast(sim);reference=bounds;state=dict(self.tracker.latest)
        begun=time.monotonic();grid=raster_support(bounds);payload=grid.tobytes()
        msg=self.msg_type();msg.header.stamp=self.node.get_clock().now().to_msg();msg.header.frame_id='map';msg.info.resolution=.01;msg.info.width=1000;msg.info.height=1000;msg.info.origin.position.x=-5.;msg.info.origin.position.y=-5.;msg.info.origin.orientation.w=1.;msg.data=array.array('b',payload)
        self.publisher.publish(msg)
        self.publications.append(dict(map_role='LOCAL_EXECUTION',at=time.monotonic(),source_scan_sim_time=state['time'],source_native_tick=state['native_tick'],source_age_s=age,forecast_sim_time=sim,forecast_support=None if bounds is None else bounds.tolist(),horizon_s=HORIZON,latency_reserve_s=MAP_LATENCY_RESERVE,map_sha256=hashlib.sha256(payload).hexdigest(),occupied_cells=int(np.count_nonzero(grid)),publish_wall_s=time.monotonic()-begun))
        reference_grid=raster_support(reference);reference_grid[reference_grid>0]=50;reference_payload=reference_grid.tobytes()
        msg.data=array.array('b',reference_payload);self.reference_publisher.publish(msg)
        self.publications.append(dict(map_role='GLOBAL_REFERENCE',at=time.monotonic(),source_scan_sim_time=state['time'],source_native_tick=state['native_tick'],source_age_s=age,forecast_sim_time=sim,forecast_support=None if reference is None else reference.tolist(),horizon_s=HORIZON,latency_reserve_s=MAP_LATENCY_RESERVE,map_sha256=hashlib.sha256(reference_payload).hexdigest(),occupied_cells=int(np.count_nonzero(reference_grid))))
    def forecast_for_planner(self):
        with self.lock:
            if self.tracker.when is None:return None,dict(information_mode='NO_SCAN')
            age=max(0.,time.monotonic()-self.scan_monotonic)if self.running else 0.
            if self.running and age>.25:raise RuntimeError('MOTION_ENVELOPE_SOURCE_STALE')
            at=self.tracker.when+age;bounds=self.tracker.forecast(at);reference=bounds
            source=dict(reference_support=None if reference is None else reference.tolist(),reference_horizon_s=HORIZON,reference_is_execution_certificate=False,center_support_bounds=None if self.tracker.support is None else self.tracker.support.tolist(),source_age_s=age,source_native_tick=self.tracker.latest['native_tick'],source_scan_sim_time=self.tracker.when,forecast_sim_time=at,forecast_support=None if bounds is None else bounds.tolist())
            return None if reference is None else polygon(reference),source
    def save(self):
        import gzip
        with self.lock:states=list(self.tracker.rows)
        with gzip.open(self.out/'MOTION_ENVELOPE.json.gz','wt')as f:json.dump(dict(states=states,observations=self.observations,publications=self.publications,truth_used=False,scope='Causal return enclosure and finite motion forecast only, not full dynamics or recursive safety certificate'),f)
