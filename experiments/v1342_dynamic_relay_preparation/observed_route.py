"""Causal observed-ball route proposals with exact original full-footprint search."""
import importlib.util
import math
from pathlib import Path
from types import MethodType,SimpleNamespace
import sys
import numpy as np

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v855_renewal_worker'))
from task_planner import search
spec=importlib.util.spec_from_file_location('route_exact_footprint',R/'experiments/v855_renewal_worker/exact_footprint.py')
geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)


def nominal_clearance(body,center,radius):
    dx,dy=np.asarray(center)-np.asarray(body[:2]);c,s=math.cos(body[2]),math.sin(body[2])
    local=np.array([dx*c+dy*s,-dx*s+dy*c]);residual=abs(local)-[.44,.375]
    distance=max(residual) if max(residual)<=0 else float(np.linalg.norm(np.maximum(residual,0)))
    return float(distance-radius)


def propose(known,body,goal,ball,guard=.22):
    circles=list(known['known_circles'])
    if ball is not None:circles.append([*ball[0],ball[1]])
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.array(known['known_rectangles']),circles=np.array(circles),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.,resolution=.05),clearance=np.ones((201,201)))
    field.pose_values=MethodType(geometry.pose_values,field)
    rear=np.array([body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]])
    rear_goal=np.asarray(goal)-[.3,0.]
    path,report=search(field,rear,rear_goal,.6,.42722137342572125,guard=guard,budget=15.,dense_requested_guard=True)
    if path is None:return None,report
    # Proposal may be a partial safe progress course, never claim whole goal.
    if len(path)<20 or np.linalg.norm(path[-1,:2]-path[0,:2])<.5:return None,dict(report,rejection='PREFIX_TOO_SHORT')
    return path,report
