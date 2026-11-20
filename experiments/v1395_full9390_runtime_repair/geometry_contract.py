"""Frozen predicted response membership and full saved causal-ball geometry."""
import importlib.util
import math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
Base=load('original_full9390_geometry',R/'experiments/v1393_full9390_preparation/geometry.py').Geometry
exact=load('original_actual_full_footprint',R/'experiments/v855_renewal_worker/exact_footprint.py')
class Geometry(Base):
    def __init__(self,known,ball):
        super().__init__(known,ball)
        from types import SimpleNamespace
        self.field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray([*known['known_circles'],ball]),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    def actual(self,body,tick=None):
        r=rear(body);return float(exact.pose_values(self.field,[r])[0])
    def tube(self,states,tick=None):return super().tube(states)
def rear(body):return np.asarray([body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]])
def membership(body,tick,states,previous=0):
    i=tick-10775;actual=rear(body);best=None
    for j in range(max(previous,0,i-20),min(len(states)-1,i+20)+1):
        ref=rear(states[j]);position=float(np.linalg.norm(actual[:2]-ref[:2]));yaw=abs(math.atan2(math.sin(actual[2]-ref[2]),math.cos(actual[2]-ref[2])))
        if position<=.02+1e-8 and yaw<=.1+1e-8:
            value=(abs(i-j),j,position,yaw)
            if best is None or value<best:best=value
    assert best is not None,'ACTUAL_RESPONSE_OUTSIDE_FIXED_TIME_POSE_TUBE'
    return dict(reference_index=best[1],rear_error_m=best[2],yaw_error_rad=best[3],time_error_s=best[0]*.01)
def errors(body,segment):
    r=rear(body);goal=segment['poses'][-1];return math.dist(r[:2],goal[:2]),abs(math.atan2(math.sin(r[2]-goal[2]),math.cos(r[2]-goal[2])))
