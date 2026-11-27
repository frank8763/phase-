"""Frozen pure function ASTs only; no environment constructors or learned models."""
from pathlib import Path
import ast,hashlib,math,types,sys
R=Path(__file__).resolve().parents[2]
P6=R/'runtime/mk-mini/training/phase6_clean/envs/sensor_utils.py'
P14=R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py'
P7=R/'runtime/mk-mini/training/phase7_camera_depth/envs/camera_depth_utils.py'
P17=R/'runtime/mk-mini/training/phase17_fusion_safety_sac_nav/envs/mkmini_phase17c_lidar_camera_fusion_env.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def functions(path,names,np):
 tree=ast.parse(path.read_text());selected=[]
 for name in names:
  nodes=[x for x in ast.walk(tree)if isinstance(x,ast.FunctionDef)and x.name==name];assert len(nodes)==1;selected.append(nodes[0])
 space=dict(np=np,math=math);exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),space)
 return types.SimpleNamespace(**{n:space[n]for n in names}),space,{n:hashlib.sha256(ast.dump(x,include_attributes=False).encode()).hexdigest()for n,x in zip(names,selected)}
def original_sensors(np):
 names=['wrap_angle','point_in_obstacle','ray_cast_distance','get_lidar_features','get_camera_goal_features']
 p6,s6,a6=functions(P6,names,np);p14,s14,a14=functions(P14,names,np)
 p7,s7,a7=functions(P7,['get_front_depth_camera_features','get_front_depth_summary'],np);s7['ray_cast_distance']=p6.ray_cast_distance
 p17,s17,a17=functions(P17,['_phase17c_get_depth','_phase17c_depth_summary'],np)
 # This exact pure sensor import is needed by the unchanged method body.
 module=types.ModuleType('training.phase14_lidar_depth_nav.envs.phase14_sensor_utils')
 for n in names:setattr(module,n,getattr(p14,n))
 sys.modules[module.__name__]=module
 return types.SimpleNamespace(p6=p6,p14=p14,p7=p7,p17=p17,AST_SHA=dict(phase6=a6,phase14=a14,phase7=a7,phase17=a17))
