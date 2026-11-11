"""Outer polytope for the already-public sinusoidal amplitude disk.

Each directional position is c + a sin(omega*t) + b cos(omega*t).
The existing public <=.25m Euclidean amplitude implies hypot(a,b)<=.25.
64 tangent halfspaces OUTER-approximate this disk; no feasible declared
coefficient is removed. Observation planes and numerical guards are unchanged.
"""
import importlib.util,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1037_unchanged_clipping',R/'experiments/v1029_declared_course_source/fast_periodic.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
FACETS=64;AMPLITUDE=.25;EPS=2e-7
NORMALS=np.c_[np.zeros(FACETS),np.cos(np.arange(FACETS)*2*math.pi/FACETS),np.sin(np.arange(FACETS)*2*math.pi/FACETS)]
class PeriodicSupport(old.PeriodicSupport):
 def __init__(self):
  super().__init__()
  for p in self.polytopes:
   for n in NORMALS:p.clip(n,AMPLITUDE+EPS)
 def snapshot(self):
  snapshot=super().snapshot();snapshot.update(coefficient_norm_outer_facets=FACETS,coefficient_norm_radius=AMPLITUDE,coefficient_norm_roundoff=EPS,public_motion_class_unchanged=True);return snapshot
