"""Genuine ROS executor, original Bridge.read/watchdog AST, synthetic bounded callback work.

Packets are saved observations with fresh software timestamps; no model or actuator exists.
"""
import ast,hashlib,json,math,os,socket,sys,threading,time,traceback
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v883_observation_dispatch'
class NoModels:
    def find_spec(self,fullname,*args):
        if fullname.split('.')[0]in {'mujoco','torch','vehicle','factory'}:raise RuntimeError('NO_VEHICLE_IMPORT '+fullname)
sys.meta_path.insert(0,NoModels());sys.path.insert(0,str(R/'experiments/v862_ready_static'))
from handshake import require
def main():
    import rclpy
    from rclpy.node import Node
    from executor_dispatch import ConcurrentSpin
    from rclpy.callback_groups import ReentrantCallbackGroup
    from geometry_msgs.msg import TransformStamped
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import LaserScan
    os.chdir(R);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:3]));variant=sys.argv[1]if len(sys.argv)>1 else'original';run=sys.argv[2]if len(sys.argv)>2 else'01';source=R/'experiments/v881_timing_accounting_continuation/ros_bridge.py';tree=ast.parse(source.read_text());outer=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='run');bridge=next(x for x in outer.body if isinstance(x,ast.ClassDef)and x.name=='Bridge');read=next(x for x in bridge.body if isinstance(x,ast.FunctionDef)and x.name=='read');watch=next(x for x in ast.walk(outer)if isinstance(x,ast.Call)and any(isinstance(a,ast.Constant)and a.value=='PHYSICS_STOPPED_OR_STALE'for a in x.args));task=dict(run_id='v883_dispatch_probe');globals_=dict(time=time,math=math,json=json,require=require,task=task,TransformStamped=TransformStamped,Odometry=Odometry,LaserScan=LaserScan);exec(compile(ast.Module(body=[read],type_ignores=[]),str(source),'exec'),globals_);watch_code=compile(ast.Expression(watch),str(source),'eval')
    fixture=json.loads((O/'FIXTURES.json').read_text())['175'];address='runs/v883_observation_dispatch/probe-'+variant+'-'+run+'.sock';stop=threading.Event();work_started=threading.Event();work_done=threading.Event();counter=dict(sent=0,published=0);node=None;sender=None;producer=None;error=None;rclpy.init()
    class Sink:
        def publish(self,msg):counter['published']+=1
        def sendTransform(self,msg):pass
    class Probe(Node):
        read=globals_['read']
        def __init__(self):
            super().__init__('phase_v883_dispatch_probe');self.latest=None;self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);self.sock.bind(address);self.sock.setblocking(False);self.odometry_messages=0;self.ages=[];self.scan_ages=[];self.lastscan=-1;self.tf=Sink();self.odom=Sink();self.scan=Sink();self.create_timer(.005,self.read)
    dispatch=ConcurrentSpin(rclpy)if variant!='original'else None
    if dispatch:dispatch.__enter__()
    try:
        node=Probe();sender=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);sender.setblocking(False)
        def produce():
            tick=0
            while not stop.is_set():
                if variant=='source_stopped'and work_started.is_set():stop.wait(.01);continue
                now=time.monotonic();packet=dict(kind='observation',run_id=task['run_id'],phase='RUNNING',native_tick=tick,sim_time=0.,sent_at=now,body_measured_at=now,scan_measured_at=now,body=fixture['body'],scan=dict(native_tick=tick,time=0.,ranges=fixture['scan']['ranges']))
                try:sender.sendto(json.dumps(packet).encode(),address);counter['sent']+=1
                except BlockingIOError:pass
                tick+=1;stop.wait(.01)
        producer=threading.Thread(target=produce);producer.start();end=time.monotonic()+3
        while node.odometry_messages<3 and time.monotonic()<end:rclpy.spin_once(node,timeout_sec=.005)
        require(node.odometry_messages>=3,'PROBE_NOT_RECEIVING')
        def heavy():
            if work_started.is_set():return
            work_started.set();until=time.monotonic()+.35
            while time.monotonic()<until:pass
            work_done.set()
        timer=node.create_timer(.01,heavy,callback_group=ReentrantCallbackGroup());before=node.odometry_messages
        while not work_done.is_set()and time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.005);eval(watch_code,globals_,dict(node=node))
        eval(watch_code,globals_,dict(node=node))
    except BaseException as e:error=repr(e)
    finally:
        stop.set()
        if producer:producer.join(timeout=1)
        if sender:sender.close()
        count=0 if node is None else node.odometry_messages;age=None if node is None or node.latest is None else time.monotonic()-node.latest['sent_at']
        if dispatch:dispatch.close()
        if node:node.sock.close();node.destroy_node()
        Path(address).unlink(missing_ok=True);rclpy.shutdown()
    result=dict(passed=error is None,reproduced_original_watchdog_failure=error=="ProtocolError('PHYSICS_STOPPED_OR_STALE')",error=error,variant=variant,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),original_read_and_watchdog_AST_unchanged=True,packets_sent=counter['sent'],odometry_callbacks=count,cached_age_s=age,work_completed=work_done.is_set(),actual_models=0,model_integrations=0,real_ros_node=True,actuator_commands_executed=0,scope='Original production read/watchdog and same executor callback pattern;350ms synthetic work reproduces starvation, not exclusive timing attribution for the old460ms request')
    (O/('DISPATCH_'+variant+'_'+run+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
