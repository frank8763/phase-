"""Conservative finite polygon containing rectangle Minkowski-summed with Euclidean radius."""
import json,math
import numpy as np
from pathlib import Path

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def hull(points):
 p=sorted(set(tuple(float(x)for x in v)for v in points));lo=[];hi=[]
 for x in p:
  while len(lo)>=2 and cross(lo[-2],lo[-1],x)<=1e-14:lo.pop()
  lo.append(x)
 for x in reversed(p):
  while len(hi)>=2 and cross(hi[-2],hi[-1],x)<=1e-14:hi.pop()
  hi.append(x)
 return np.asarray(lo[:-1]+hi[:-1])
def polygon(radius,n=32):
 assert radius>0 and n>=16 and n%4==0;r=radius/math.cos(math.pi/n);a=(np.arange(n)+.5)*2*math.pi/n;circle=np.c_[np.cos(a),np.sin(a)]*r;rect=np.array([[.44,.375],[.44,-.375],[-.44,-.375],[-.44,.375]]);return hull((rect[:,None,:]+circle[None,:,:]).reshape(-1,2))
def prove(points,radius):
 p=np.asarray(points);edges=np.roll(p,-1,axis=0)-p;inward=np.c_[-edges[:,1],edges[:,0]];length=np.linalg.norm(inward,axis=1);corners=np.array([[.44,.375],[.44,-.375],[-.44,-.375],[-.44,.375]]);# every halfplane contains every rectangle corner plus the whole radius disk
 values=np.min(np.sum((corners[:,None,:]-p[None,:,:])*inward[None,:,:],axis=2),axis=0)/length
 return float(values.min()),bool(np.all(values>=radius-1e-12))

def cost(pose,pad,maprow,points):
 from collision_witness import line
 x,y,yaw=pose;c,s=math.cos(yaw),math.sin(yaw);poly=np.asarray(points)@np.array([[c,s],[-s,c]])+np.array([x,y]);m=maprow['value'];g=np.asarray(m['data']).reshape(m['height'],m['width']);grid=np.floor((poly-np.asarray(m['origin']))/m['resolution']).astype(int);maximum=0
 for a,b in zip(grid,np.roll(grid,-1,axis=0)):
  for xx,yy in line(*a,*b):
   if not(0<=xx<m['width']and 0<=yy<m['height']):return dict(cost=254,outside_map=True)
   maximum=max(maximum,int(g[yy,xx]))
   if maximum>=254:return dict(cost=maximum,outside_map=False)
 return dict(cost=maximum,outside_map=False)
