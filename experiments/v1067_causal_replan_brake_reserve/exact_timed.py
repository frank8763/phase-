"""Euclidean body-to-outer-polygon distance at the original timed margins."""
import importlib.util,math
from pathlib import Path
import numpy as np
from time_geometry import interval_support
from geometry_model import ref,REQUIRED
R=Path(__file__).resolve().parents[2]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
pg=module('v1067_independent_polygon_distance',R/'experiments/v934_rpccr_certified_recovery/polygon_geometry.py')
class ExactTimedGeometry:
 def __init__(self,known,prior,start):
  self.static=ref._old.Geometry(known,None);self.prior=prior;self.start=start;self.period=2*math.pi/.32;self.bin=.025;edges=np.arange(0,self.period,self.bin);self.edges=edges;self.support=interval_support(prior['vertices'],edges-.075,edges+self.bin+.075);self.polygons=[pg.polygon(b)for b in self.support]
 def clearances(self,poses,ticks,half_s=.025):
  assert half_s<=.025+1e-12;p=np.asarray(poses,float);t=(self.start+np.asarray(ticks)*.01)%self.period;ix=np.minimum((t/self.bin).astype(int),len(self.edges)-1);static=self.static.clearances(p)[0];dynamic=np.empty(len(p))
  for row in np.unique(ix):
   use=np.flatnonzero(ix==row);dynamic[use]=pg.distances(p[use],self.polygons[row])-.1
  return np.minimum(static,dynamic)
 def complete(self,states):
  return float(self.clearances(np.asarray(states)[:,:3],np.arange(len(states)),.005).min())
