"""Geometry graph and frozen actual-state source access, with model imports blocked."""
import sys,json,hashlib,ctypes,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1138_backup_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'));from geometry import Geometry,REQUIRED,pg
from source import Engine,initial,python_replay,COUNTS
from recovery_source import forecast_packet
import numpy as np

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def library():
 lib=ctypes.CDLL(str(O/'configuration.so'));a=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');lib.configuration_path.argtypes=[a,ctypes.c_int,a,ctypes.c_int,a,ctypes.c_int,ctypes.c_double,a,a,ctypes.c_double,ctypes.c_int,ctypes.c_int,ctypes.c_double,a,ctypes.c_int,ctypes.POINTER(ctypes.c_int),a];lib.configuration_path.restype=ctypes.c_int;return lib

def graph(lib,rect,circles,bounds,root,goal,cycle,cell=.05,headings=72,seconds=90.):
 rect=np.ascontiguousarray(rect,float).reshape(-1,4);circles=np.ascontiguousarray(circles,float).reshape(-1,3);support=np.ascontiguousarray(np.vstack([bounds,bounds]),float);out=np.zeros((20000,3));count=ctypes.c_int();stats=np.zeros(6)
 code=lib.configuration_path(rect,len(rect),circles,len(circles),support,1,2*np.pi/.32,np.array(root,float),np.array(goal,float),cell,headings,int(cycle),seconds,out,len(out),ctypes.byref(count),stats)
 return {'code':code,'found':code==0,'expanded':int(stats[0]),'wall_s':float(stats[1]),'remaining_goal_heuristic':float(stats[2]),'rejected_edges':int(stats[3]),'grid_states':int(stats[4]),'cost':float(stats[5])if code==0 else None},out[:count.value]

def certify(g,path,cycle):
 rho=float(np.hypot(.44,.375));poses=[];reserve=[];rotations=0;lateral=0.
 for a,b in zip(path[:-1],path[1:]):
  angle=float(np.arctan2(np.sin(b[2]-a[2]),np.cos(b[2]-a[2])));dist=float(np.linalg.norm(b[:2]-a[:2]));n=max(1,int(np.ceil((dist+rho*abs(angle))/.002)));t=(np.arange(n)+.5)/n;poses.extend(np.c_[a[:2]+t[:,None]*(b[:2]-a[:2]),a[2]+t*angle]);reserve.extend([(dist+rho*abs(angle))/(2*n)]*n);rotations+=int(dist<1e-10 and abs(angle)>1e-10)
  if dist>1e-10:lateral=max(lateral,abs(float(np.dot((b[:2]-a[:2])/dist,[-np.sin(a[2]),np.cos(a[2])]))))
 poses=np.array(poses);low=g.cycle(poses)if cycle else g.static.clearances(poses)[0];low-=np.array(reserve);return {'passed':bool(low.min()>=REQUIRED),'continuous_interpolation_raw_lower_m':float(low.min()),'samples':len(poses),'rotation_in_place_edges':rotations,'maximum_lateral_fraction':lateral,'car_executable':False}

def prefix(rows,cut):
 assert isinstance(cut,int)and cut>0;out=[];cursor=0
 for t,v,n,m in rows:
  if cursor>=cut:break
  take=min(int(n),cut-cursor);out.append((t,v,take,m));cursor+=take
 assert cursor==cut;return out+[(0.,0.,2200,0)]
