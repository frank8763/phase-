"""Original causal interval polygon/static geometry, complete actual footprint."""
import ast
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2]
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
    def __init__(self,known,model):
        assert model['periodic']['source_tick']==32200 and abs(model['last_observed_time']-322.1)<1e-7
        self.model=model;self.normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];self.cache={}
        self.field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    def polygon(self,tick):
        cell=int(math.floor(((tick-32210)*.01)/.1+1e-10))
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
        indices=np.floor(((tick-32210+np.arange(len(rp)))*.01)/.1+1e-10).astype(int)
        for index in np.unique(indices):
            mask=indices==index;first=int(np.flatnonzero(mask)[0]);poly=self.polygon(tick+first)
            dynamic[mask]=np.max(np.min(poly@normals.T,axis=0)-robot[mask],axis=1)
        radius=math.hypot(.74,.375);static=geometry.pose_values(self.field,rp)-.02-2*radius*math.sin(.05)
        movement=np.linalg.norm(np.diff(rp[:,:2],axis=0),axis=1)+radius*abs(np.diff(rp[:,2]));allowance=float(movement.max()) if len(movement) else 0.
        return float(np.minimum(static,dynamic).min())-allowance
def membership(body,tick,states):
    i=tick-32600;actual=rear(body);best=None
    for j in range(max(0,i-20),min(len(states)-1,i+20)+1):
        ref=rear(states[j]);pos=float(np.linalg.norm(actual[:2]-ref[:2]));yaw=abs(math.atan2(math.sin(actual[2]-ref[2]),math.cos(actual[2]-ref[2])))
        if pos<=.02+1e-8 and yaw<=.1+1e-8:
            value=(abs(i-j),j,pos,yaw)
            if best is None or value<best:best=value
    assert best is not None,'ACTUAL_RESPONSE_OUTSIDE_DECLARED_TIME_POSE_TUBE'
    return dict(reference_index=best[1],rear_error_m=best[2],yaw_error_rad=best[3],time_error_s=best[0]*.01)
