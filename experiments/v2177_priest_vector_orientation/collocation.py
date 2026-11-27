"""Ideal geometric projection equations only; no optimizer or plant imports."""
from pathlib import Path
import importlib.util,math
import numpy as np
R=Path(__file__).resolve().parents[2]
p=R/'experiments/v2176_sccr_common_plant_component/geometry.py';spec=importlib.util.spec_from_file_location('C2177_oriented_geometry',p);geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)
VMAX=.1;AMAX=.1;KMAX=1/1.32;OFFSET=.3

def sinc(a):
 if abs(a)<1e-4:
  s=1-a*a/6+a**4/120-a**6/5040
  ds=-a/3+a**3/30-a**5/840
 else:s=math.sin(a)/a;ds=(a*math.cos(a)-math.sin(a))/(a*a)
 return s,ds

def arc(pose,v0,v1,k,h):
 """Exact arc for constant curvature and linearly varying ideal speed.
 Returns value, derivative wrt pose(3), v0, v1, k; smooth at v=k=0.
 """
 x,y,t=map(float,pose);d=.5*(v0+v1)*h;a=.5*k*d;s,ds=sinc(a);length=d*s;mid=t+a;c=math.cos(mid);sn=math.sin(mid)
 value=np.array([x+length*c,y+length*sn,t+k*d],float)
 jp=np.eye(3);jp[:,2]=[-length*sn,length*c,1.]
 ld=s+d*ds*k*.5
 jd=np.array([ld*c-length*sn*k*.5,ld*sn+length*c*k*.5,k])
 lk=d*d*ds*.5
 jk=np.array([lk*c-length*sn*d*.5,lk*sn+length*c*d*.5,d])
 return value,jp,jd*(h*.5),jd*(h*.5),jk

def bernstein_reference(t,H=10.):
 # Degree10 position coefficients integrated from the preregistered degree9
 # velocity control polygon. This is a reference, not an optimizer result.
 b=[0.,0.,.1,.1,.1,.1,.1,.1,0.,0.];c=[0.]
 for value in b:c.append(c[-1]+H/10*value)
 u=t/H;return sum(math.comb(10,i)*u**i*(1-u)**(10-i)*z for i,z in enumerate(c))

class Projection:
 def __init__(self,known,N=20,H=10.):
  assert N==20 and H==10.
  self.known=known;self.N=N;self.H=H;self.h=H/N;self.pose_count=3*(N+1);self.speed_start=self.pose_count;self.curvature_start=self.speed_start+N+1;self.total=self.curvature_start+N
  coarse=np.array([0.,0.,.1,.1,.1,.1,.1,.1,0.,0.,0.]);self.initial_speeds=np.interp(np.linspace(0,10,N+1),np.arange(11),coarse)
  poses=[np.array([-4.3,-2.,0.])]
  for i in range(N):poses.append(arc(poses[-1],self.initial_speeds[i],self.initial_speeds[i+1],0.,self.h)[0])
  self.initial_full=np.r_[np.array(poses).ravel(),self.initial_speeds,np.zeros(N)]
  assert abs(poses[-1][0]-(-4.3+.6))<1e-12
  # Fixed actual reference endpoint poses, rest, endpoint acceleration and
  # curvature of identically stationary first/last intervals.
  fixed=list(range(3))+list(range(3*N,3*N+3))+[self.speed_start+i for i in [0,1,N-1,N]]+[self.curvature_start,self.curvature_start+N-1]
  self.free=np.array([i for i in range(self.total)if i not in fixed],int);self.initial=self.initial_full[self.free].copy()
  self.reference=self.initial_full.copy()
  for i,t in enumerate(np.linspace(0,H,N+1)):self.reference[3*i]=-4.3+bernstein_reference(float(t),H)
 def full(self,z):
  a=np.asarray(z,float);assert a.shape==self.initial.shape and np.isfinite(a).all();x=self.initial_full.copy();x[self.free]=a;return x
 def bounds(self):
  lo=np.full(self.total,-np.inf);hi=np.full(self.total,np.inf)
  lo[self.speed_start:self.curvature_start]=0.;hi[self.speed_start:self.curvature_start]=VMAX
  lo[self.curvature_start:]=-KMAX;hi[self.curvature_start:]=KMAX
  return lo[self.free],hi[self.free]
 def evaluate(self,z):
  x=self.full(z);p=x[:self.pose_count].reshape(-1,3);v=x[self.speed_start:self.curvature_start];k=x[self.curvature_start:];eq=[];je=[];ineq=[];ji=[];clear=[]
  def shape(pose,jpose):
   t=pose[2];body=np.array([pose[0]+OFFSET*math.cos(t),pose[1]+OFFSET*math.sin(t),t]);transform=np.array([[1.,0.,-OFFSET*math.sin(t)],[0.,1.,OFFSET*math.cos(t)],[0.,0.,1.]])
   values,jac,_=geometry.feature(body,self.known);values=np.asarray(values);clear.extend(values.tolist());ineq.extend(((values-geometry.REQUIRED)/geometry.REQUIRED).tolist())
   ji.extend((np.asarray(jac)@transform@jpose/geometry.REQUIRED).tolist())
  for i in range(self.N+1):
   jpose=np.zeros((3,self.total));jpose[:,3*i:3*i+3]=np.eye(3);shape(p[i],jpose)
  for i in range(self.N):
   value,jp,jv0,jv1,jk=arc(p[i],v[i],v[i+1],k[i],self.h);res=p[i+1]-value;eq.extend(res.tolist())
   jac=np.zeros((3,self.total));jac[:,3*i:3*i+3]=-jp;jac[:,3*(i+1):3*(i+1)+3]=np.eye(3);jac[:,self.speed_start+i]=-jv0;jac[:,self.speed_start+i+1]=-jv1;jac[:,self.curvature_start+i]=-jk;je.extend(jac.tolist())
   # Exact half-time pose under the same linear speed/constant-curvature arc.
   mid,jp,jv0,jv1,jk=arc(p[i],v[i],.5*(v[i]+v[i+1]),k[i],.5*self.h)
   jmid=np.zeros((3,self.total));jmid[:,3*i:3*i+3]=jp;jmid[:,self.speed_start+i]=jv0+.5*jv1;jmid[:,self.speed_start+i+1]=.5*jv1;jmid[:,self.curvature_start+i]=jk;shape(mid,jmid)
   acceleration=(v[i+1]-v[i])/self.h;ineq.append(1-(acceleration/AMAX)**2)
   ja=np.zeros(self.total);ja[self.speed_start+i]=2*acceleration/(AMAX**2*self.h);ja[self.speed_start+i+1]=-2*acceleration/(AMAX**2*self.h);ji.append(ja.tolist())
  return dict(equalities=np.array(eq),equality_jacobian=np.asarray(je)[:,self.free],inequalities=np.asarray(ineq),inequality_jacobian=np.asarray(ji)[:,self.free],minimum_sampled_clearance=float(min(clear)),speeds=v.copy(),curvatures=k.copy(),poses=p.copy(),all_sampled_clearances=np.array(clear))
 def objective(self,z):
  x=self.full(z);diff=x-self.reference;scales=np.ones(self.total);scales[:self.pose_count]=np.tile([.6,.6,1.],self.N+1);scales[self.speed_start:self.curvature_start]=VMAX;scales[self.curvature_start:]=KMAX
  normalized=diff/scales
  return float(.5*np.dot(normalized,normalized)),(diff/(scales*scales))[self.free]
