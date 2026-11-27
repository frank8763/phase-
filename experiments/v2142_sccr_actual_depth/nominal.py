"""Declared shared geometric nominal input, no native backend or clipping."""
import math
SPEED=.08;LOOKAHEAD=.6;KMAX=1/1.32

def command(packet,selected):
 body=packet['body'];assert len(body)==5 and all(math.isfinite(x)for x in body);gear=selected['gear'];assert gear in[-1,1]
 points=selected['poses'];assert len(points)>=2 and all(len(x)>=3 and all(math.isfinite(y)for y in x[:3])for x in points)
 x,y,t=body[:3];rear=[x-.3*math.cos(t),y-.3*math.sin(t)];assert math.dist(rear,points[0][:2])<=1e-6,'NOMINAL_FRESH_ORIGIN_REFUSED'
 arc=0.;target=points[-1][:2]
 for a,b in zip(points,points[1:]):
  d=math.dist(a[:2],b[:2])
  if arc+d>=LOOKAHEAD:
   f=(LOOKAHEAD-arc)/d;target=[a[j]+f*(b[j]-a[j])for j in range(2)];arc=LOOKAHEAD;break
  arc+=d
 dx,dy=target[0]-rear[0],target[1]-rear[1];r2=dx*dx+dy*dy;assert r2>.01**2,'NOMINAL_COMPONENT_ENDPOINT_HOLD'
 longitudinal=math.cos(t)*dx+math.sin(t)*dy;lateral=-math.sin(t)*dx+math.cos(t)*dy;assert gear*longitudinal>0,'NOMINAL_TARGET_OPPOSES_GEAR'
 k=2*lateral/r2;v=gear*SPEED;w=v*k;assert abs(w)<=abs(v)*KMAX+1e-12,'NOMINAL_RAW_CURVATURE_REFUSED'
 return dict(request=[v,w,False],target=target,lookahead_arc_m=arc,gear=gear,source='PUBLIC_ROUTE_FRESH_MEASURED_REAR_ORIGIN',physical_authority=False)


def reanchor(packet,selected):
 """Trim the fixed public route at measured rear projection; never change gear."""
 body=packet['body'];x,y,t=body[:3];rear=[x-.3*math.cos(t),y-.3*math.sin(t)]
 points=selected['poses'];best=None
 for i,(a,b)in enumerate(zip(points,points[1:])):
  dx,dy=b[0]-a[0],b[1]-a[1];dd=dx*dx+dy*dy
  if dd<=1e-16:continue
  f=max(0.,min(1.,((rear[0]-a[0])*dx+(rear[1]-a[1])*dy)/dd));q=[a[0]+f*dx,a[1]+f*dy];distance=math.dist(rear,q)
  if best is None or distance<best[0]:best=(distance,i,f)
 assert best is not None and best[0]<=.1,'NOMINAL_CURRENT_ROUTE_PROJECTION_REFUSED'
 _,i,f=best;tail=[list(z)for z in points[i+1:]]
 while tail and math.dist(rear,tail[0][:2])<=1e-8:tail.pop(0)
 assert tail,'NOMINAL_COMPONENT_ENDPOINT_HOLD'
 result=dict(selected);result['poses']=[[rear[0],rear[1],t]]+tail
 return result
