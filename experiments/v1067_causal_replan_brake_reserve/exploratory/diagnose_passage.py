import importlib.abc,sys,json,time
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parents[1];sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C));from planner import library,interval_support
import ctypes
x=json.loads((R/'runs/v1066_actual_route_diagnosis/ns_source_repro/INPUT.json').read_text());lib=library();arr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');lib.straight_best.argtypes=[ctypes.c_double]*4+[arr,ctypes.c_int,ctypes.c_double,arr,ctypes.c_int,arr,ctypes.c_int,arr];lib.straight_best.restype=ctypes.c_int;rect=np.ascontiguousarray(x['setup']['known']['known_rectangles'],float);circles=np.ascontiguousarray(x['setup']['known']['known_circles'],float);period=2*math.pi/.32;dt=.025;edges=np.arange(0,period,dt);support=np.ascontiguousarray(interval_support(x['source']['periodic']['vertices'],edges-.075,edges+dt+.075));rows=[]
for lateral in [-.699,-.70,-.71,-.72,-.74,-.76,-.8,-.85,-.9,-1.0]:
 out=np.zeros(4);lib.straight_best(lateral,-.1,-2.8,.08,support,len(edges),dt,rect,len(rect),circles,len(circles),out);row=dict(x=lateral,best_timed_lower_m=out[0],best_initial_phase_s=out[1],minimum_static_m=out[2],worst_y=out[3],passed=bool(out[0]>=REQUIRED));rows.append(row);print(json.dumps(row),flush=True)
dump(O/'STRAIGHT_PASSAGE_DIAGNOSIS.json',dict(scope='Geometric timing diagnostic only, not an executable source or impossibility proof',rows=rows,models=0,integrations=0))
