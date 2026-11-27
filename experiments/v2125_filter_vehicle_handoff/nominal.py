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
