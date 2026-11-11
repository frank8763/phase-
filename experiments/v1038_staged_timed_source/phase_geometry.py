import math
import numpy as np
from time_geometry import interval_support
from geometry_model import ref
NORMALS=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
class Geometry:
 def __init__(self,known,prior,start):
  self.static=ref._old.Geometry(known,None);self.prior=prior;self.start=start;self.period=2*math.pi/.32;self.bin=.025
  edges=np.arange(0,self.period,self.bin);self.edges=edges
  self.support=interval_support(prior['vertices'],edges-.075,edges+self.bin+.075)
 def clearances(self,poses,ticks,half_s=.025):
  assert half_s<=.025+1e-12
  t=(self.start+np.asarray(ticks)*.01)%self.period;indices=np.minimum((t/self.bin).astype(int),len(self.edges)-1);b=self.support[indices]
  p=np.asarray(poses);c=np.cos(p[:,2]);s=np.sin(p[:,2]);front=np.c_[c,s];left=np.c_[-s,c];low=p[:,:2]@NORMALS.T-.44*abs(front@NORMALS.T)-.375*abs(left@NORMALS.T)
  dynamic=(low-b-.1).max(axis=1);static=self.static.clearances(p)[0];return np.minimum(static,dynamic)
 def complete(self,states):
  lowest=math.inf
  for start in range(0,len(states),2048):q=states[start:start+2048];lowest=min(lowest,float(self.clearances(q[:,:3],np.arange(start,start+len(q)),.005).min()))
  return lowest

