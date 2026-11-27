"""Proposal-only conservative body geometry and analytic pose derivatives."""
import math
HX=.44; HY=.375; RHO=math.hypot(HX,HY)
SPATIAL=.04+RHO*.035+.1*(.13+RHO*.16)+.02*(.13+RHO*.16+.08)
REQUIRED=.155+SPATIAL
def sign(x):return 1. if x>0 else -1. if x<0 else 0.
def add(a,b):return [x+y for x,y in zip(a,b)]
def scale(a,z):return [x*z for x in a]
def feature(pose,known,support=None):
 x,y,t=pose;c=math.cos(t);s=math.sin(t);ac=abs(c);ass=abs(s);dc=-s*sign(c);ds=c*sign(s)
 ex=HX*ac+HY*ass;ey=HX*ass+HY*ac;dex=HX*dc+HY*ds;dey=HX*ds+HY*dc
 values=[x+5-ex,5-x-ex,y+5-ey,5-y-ey]
 jac=[[1.,0.,-dex],[-1.,0.,-dex],[0.,1.,-dey],[0.,-1.,-dey]]
 labels=['wall_xlow','wall_xhigh','wall_ylow','wall_yhigh']
 for i,(rx,ry,a,b)in enumerate(known['known_rectangles']):
  dx=rx-x;dy=ry-y;u=dx*c+dy*s;v=-dx*s+dy*c;su=sign(u);sv=sign(v)
  candidates=[(abs(dx)-a-ex,[-sign(dx),0.,-dex]),(abs(dy)-b-ey,[0.,-sign(dy),-dey]),(abs(u)-HX-a*ac-b*ass,[-su*c,-su*s,su*(-dx*s+dy*c)-a*dc-b*ds]),(abs(v)-HY-a*ass-b*ac,[sv*s,-sv*c,sv*(-dx*c-dy*s)-a*ds-b*dc])]
  value,g=max(candidates,key=lambda z:z[0]);values.append(value);jac.append(g);labels.append('rectangle_'+str(i))
 for i,(cx,cy,r)in enumerate(known['known_circles']):
  dx=cx-x;dy=cy-y;u=dx*c+dy*s;v=-dx*s+dy*c
  a=abs(u)-HX;b=abs(v)-HY;ga=[-sign(u)*c,-sign(u)*s,sign(u)*(-dx*s+dy*c)];gb=[sign(v)*s,-sign(v)*c,sign(v)*(-dx*c-dy*s)]
  if max(a,b)<=0:value,g=(a,ga)if a>=b else(b,gb)
  else:
   aa=max(a,0.);bb=max(b,0.);value=math.hypot(aa,bb);g=add(scale(ga,aa/value),scale(gb,bb/value))
  values.append(value-r);jac.append(g);labels.append('circle_'+str(i))
 if support is not None:
  assert len(support)==16
  candidates=[]
  for i,h in enumerate(support):
   a=i*math.pi/8;nx=math.cos(a);ny=math.sin(a);u=c*nx+s*ny;v=-s*nx+c*ny
   value=x*nx+y*ny-HX*abs(u)-HY*abs(v)-h-.1
   g=[nx,ny,-HX*sign(u)*(-s*nx+c*ny)-HY*sign(v)*(-c*nx-s*ny)]
   candidates.append((value,g))
  value,g=max(candidates,key=lambda z:z[0]);values.append(value);jac.append(g);labels.append('causal_support')
 assert all(math.isfinite(z)for z in values)and all(math.isfinite(z)for row in jac for z in row)
 return values,jac,labels

def support_at(snapshot,t,whole_cycle=False):
 assert snapshot['omega']==.32 and snapshot['amplitude']==.25 and len(snapshot['vertices'])==8
 pairs=[]
 for points in snapshot['vertices']:
  assert len(points)>=1 and all(len(v)==3 and all(math.isfinite(x)for x in v)for v in points)
  if whole_cycle:upper=max(a+math.hypot(b,c)for a,b,c in points);lower=min(a-math.hypot(b,c)for a,b,c in points)
  else:
   values=[a+b*math.sin(.32*t)+c*math.cos(.32*t)for a,b,c in points];upper=max(values);lower=min(values)
  pairs.append((upper+2e-7,-lower+2e-7))
 return [x[0]for x in pairs]+[x[1]for x in pairs]
