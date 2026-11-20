"""Original causal interval polygon/static geometry, complete actual footprint."""
import ast
import copy
import sys
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1397_event_handoff_integration'))
from causal_bridge_field import all_future
def load(n,p):
    s=importlib.util.spec_from_file_location(n,R/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def function(path,name):
    node=next(x for x in ast.parse((R/path).read_text()).body if isinstance(x,ast.FunctionDef) and x.name==name)
    env=dict(np=np,math=math);exec(compile(ast.Module(body=[node],type_ignores=[]),str(R/path),'exec'),env);return env[name]
swept=load('handoff_original_support','experiments/v1020_terminal_two_route_development/periodic_support.py')
geometry=load('handoff_original_static','experiments/v855_renewal_worker/exact_footprint.py')
clipped=function('experiments/v1366_canonical_timed_lattice/build_polygons.py','clipped')
distances=function('experiments/v934_rpccr_certified_recovery/polygon_geometry.py','distances')
def rear(body):return np.array([body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]])
class Geometry:
    def __init__(self,known,model,*,origin_native,origin_sim_time):
        assert type(origin_native)is int and origin_native>=0 and math.isfinite(origin_sim_time)
        all_future(model,current_native=origin_native,current_sim_time=origin_sim_time)
        observed=model['last_observed_time'];assert math.isfinite(observed)and 0<=observed<=origin_sim_time+1e-8,'TIMED_GEOMETRY_FUTURE_SOURCE_TIME'
        offset=round((origin_sim_time-observed)/.01)
        assert offset>=0 and abs(origin_sim_time-observed-offset*.01)<=1e-8,'TIMED_GEOMETRY_CLOCK_NOT_NATIVE_ALIGNED'
        self.origin_native=origin_native;self.origin_sim_time=origin_sim_time;self.offset_native=offset
        self.model=copy.deepcopy(model);self.normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];self.cache={}
        self.field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    def cell(self,tick):
        assert type(tick)is int and tick>=self.origin_native,'TIMED_GEOMETRY_NATIVE_BEFORE_BOUND_ORIGIN'
        return (tick-self.origin_native+self.offset_native)//10
    def polygon(self,tick):
        cell=self.cell(tick)
        if cell not in self.cache:
            lo=self.model['last_observed_time']+max(0,cell*.1-.22);hi=self.model['last_observed_time']+(cell+1)*.1+.22
            b=swept.swept_bounds(self.model['periodic']['vertices'],lo,hi)+.1;self.cache[cell]=clipped(self.normals,b)
        return self.cache[cell]
    def actual(self,body,tick):
        a=rear(body);dynamic=float(distances(np.array([body[:3]]),self.polygon(tick))[0]);static=float(geometry.pose_values(self.field,[a])[0]);return min(dynamic,static)
    def predicted_path(self,states,tick):
        a=np.asarray(states);rearposes=np.c_[a[:,0]-.3*np.cos(a[:,2]),a[:,1]-.3*np.sin(a[:,2]),a[:,2]]
        static=geometry.pose_values(self.field,rearposes);values=np.empty(len(a))
        for index in range(len(a)):values[index]=float(distances(a[index:index+1,:3],self.polygon(tick+index))[0])
        movement=np.linalg.norm(np.diff(rearposes[:,:2],axis=0),axis=1)+math.hypot(.74,.375)*abs(np.diff(rearposes[:,2]))
        allowance=float(movement.max()) if len(movement) else 0.
        return float(np.minimum(static,values).min())-allowance
    def tube(self,states,tick):
        a=np.asarray(states);rp=np.c_[a[:,0]-.3*np.cos(a[:,2]),a[:,1]-.3*np.sin(a[:,2]),a[:,2]]
        normals=np.c_[np.cos(np.arange(64)*math.tau/64),np.sin(np.arange(64)*math.tau/64)]
        cs=np.cos(rp[:,2]);sn=np.sin(rp[:,2]);maximum=np.full((len(rp),64),-math.inf)
        for x,y in [(-.14,-.375),(-.14,.375),(.74,-.375),(.74,.375)]:
            X=x*cs-y*sn;Y=x*sn+y*cs;A=X[:,None]*normals[:,0]+Y[:,None]*normals[:,1];B=-Y[:,None]*normals[:,0]+X[:,None]*normals[:,1]
            value=A*math.cos(.1)+abs(B)*math.sin(.1);value=np.where(abs(np.arctan2(B,A))<=.1,np.hypot(A,B),value);maximum=np.maximum(maximum,value)
        robot=rp[:,:2]@normals.T+maximum+.02;dynamic=np.empty(len(rp))
        assert type(tick)is int and tick>=self.origin_native
        indices=(tick-self.origin_native+self.offset_native+np.arange(len(rp)))//10
        for index in np.unique(indices):
            mask=indices==index;first=int(np.flatnonzero(mask)[0]);poly=self.polygon(tick+first)
            dynamic[mask]=np.max(np.min(poly@normals.T,axis=0)-robot[mask],axis=1)
        radius=math.hypot(.74,.375);static=geometry.pose_values(self.field,rp)-.02-2*radius*math.sin(.05)
        movement=np.linalg.norm(np.diff(rp[:,:2],axis=0),axis=1)+radius*abs(np.diff(rp[:,2]));allowance=float(movement.max()) if len(movement) else 0.
        return float(np.minimum(static,dynamic).min())-allowance
