"""Actual worker import seams and planner coroutine; zero models and zero ROS servers."""
import argparse,ast,asyncio,importlib.abc,importlib.machinery,importlib.util,inspect,json,sys,time,types
from pathlib import Path
from types import SimpleNamespace as S
R=Path(__file__).resolve().parents[2];O=R/'runs/v972_daytime_binding_probe'
p=argparse.ArgumentParser();p.add_argument('target');p.add_argument('mode',choices=['native','planner']);args=p.parse_args();target=R/'experiments'/args.target
report=dict(target=args.target,mode=args.mode,models=0,integrations=0,passed=False)
class BlockedPhysical(Exception):pass
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name=='physical':
   spec=importlib.machinery.PathFinder.find_spec(name,sys.path);report['physical_source']=None if spec is None else str(Path(spec.origin).resolve().relative_to(R));raise BlockedPhysical()
  if name.split('.')[0]in{'mujoco','torch','vehicle','factory','rclpy'}:raise AssertionError('MODEL_OR_ROS_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(target))
if args.mode=='native':
 import native_worker
 native_worker.engine.authorized=lambda *a:time.time()+60
 native_worker.engine.verify_sources=lambda *a:None
 try:native_worker.engine.run({}, {},'MODEL_FREE_IMPORT_SEAM')
 except BlockedPhysical:pass
 report['physical_declared_delegate']='experiments/v968_rpp_closed_loop_night/physical.py' if (target/'MODULE_BINDINGS.json').exists()else None
 report['passed']=report.get('physical_source')==(str((target/'physical.py').relative_to(R))if (target/'MODULE_BINDINGS.json').exists()else'experiments/v968_rpp_closed_loop_night/physical.py')
else:
 import ros_worker
 engine=ros_worker.engine;tree=ast.parse(Path(inspect.getsourcefile(engine.run)).read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run');bridge=next(n for n in run.body if isinstance(n,ast.ClassDef)and n.name=='Bridge');ctor=next(n for n in bridge.body if isinstance(n,ast.FunctionDef)and n.name=='__init__')
 selected=[]
 for n in ctor.body:
  if isinstance(n,ast.ImportFrom)and n.module in {'motion_publisher','dynamic_proxy'}:selected.append(n)
  elif isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and ast.unparse(n.value.func)=='sys.path.insert':selected.append(n)
  if isinstance(n,ast.ImportFrom)and n.module=='dynamic_proxy':break
 ns=dict(sys=sys,C=engine.C);exec(compile(ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[])),str(target/'ros_bridge.py'),'exec'),ns)
 cls=ns['DynamicPlannerProxy'];report['planner_source']=str(Path(inspect.getsourcefile(cls)).resolve().relative_to(R));report['publisher_source']=str(Path(inspect.getsourcefile(ns['MotionPublisher'])).resolve().relative_to(R))
 class Pose:
  def __init__(self):self.header=S(frame_id='map',stamp=None);self.pose=S(position=S(x=0.,y=0.,z=0.),orientation=S(x=0.,y=0.,z=0.,w=1.))
 geom=types.ModuleType('geometry_msgs');msg=types.ModuleType('geometry_msgs.msg');msg.PoseStamped=Pose;geom.msg=msg;sys.modules['geometry_msgs']=geom;sys.modules['geometry_msgs.msg']=msg
 goal=Pose();goal.pose.position.x=4.;goal.pose.position.y=-2.;start=Pose();start.pose.position.x=-4.;start.pose.position.y=-2.
 packet=dict(body=[-4.,-2.,0.,0.,0.],sent_at=time.monotonic(),native_tick=0)
 source=dict(center_support_bounds=None,periodic=None,source_native_tick=0)
 class Client:
  def server_is_ready(self):return True
  async def send_goal_async(self,query):report['reached_real_planner_call_seam']=True;raise RuntimeError('EXPECTED_MODEL_FREE_SMAC_CALL_BOUNDARY')
 obj=cls.__new__(cls);obj.node=S(guard_failure=None,send=lambda p:None);obj.use_new=True;obj.refuge_mode=False;obj.force_forward=True;obj.configured_footprint=[[-.44,-.375],[.44,-.375],[.44,.375],[-.44,.375]];obj.forecast=lambda:(None,source,packet);obj.kind=S(Result=lambda:S(error_code=0),Goal=lambda:S());obj.known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text());obj.deadline=time.time()+60;obj.client=Client();obj.rows=[];obj.out=O/(args.target+'_planner');obj.out.mkdir(exist_ok=True)
 handle=S(request=S(goal=goal,start=start,use_start=True,planner_id='GridBased'),abort=lambda:None,succeed=lambda:None)
 asyncio.run(obj.execute(handle));report['actual_coroutine_error']=obj.rows[-1].get('error');report['planner_implementation_source']=str(Path(getattr(cls,'SCIENCE_FILE',inspect.getsourcefile(cls))).resolve().relative_to(R))
 report['passed']=bool(report.get('reached_real_planner_call_seam')and report['planner_implementation_source']=='experiments/v968_rpp_closed_loop_night/dynamic_proxy.py')
(O/(args.target+'_'+args.mode+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));sys.exit(0 if report['passed']else 1)
