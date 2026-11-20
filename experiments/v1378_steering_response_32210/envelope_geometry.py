"""Original footprint and polygon geometry; no truth or physical model input."""
import ast
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2]
path=R/'experiments/v934_rpccr_certified_recovery/polygon_geometry.py'
node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='distances')
env=dict(np=np,math=math);exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),env);distances=env['distances']
s=importlib.util.spec_from_file_location('v1378_original_static_footprint',R/'experiments/v855_renewal_worker/exact_footprint.py');geometry=importlib.util.module_from_spec(s);s.loader.exec_module(geometry)
def field(known):return SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
def bounds(task,body,known):
    rear=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]]
    dynamic=float(distances(np.asarray([body[:3]]),np.asarray(task['causal_all_future_polygon']))[0]);static=float(geometry.pose_values(field(known),[rear])[0])
    translation=math.dist(body[:2],task['origin_body'][:2]);turn=abs(math.atan2(math.sin(body[2]-task['origin_body'][2]),math.cos(body[2]-task['origin_body'][2])))
    return min(dynamic,static),translation,turn
