"""Independent Euclidean full-rectangle geometry, software only."""
import math
SIGNS=[(-1.,-1.),(1.,-1.),(1.,1.),(-1.,1.)]
def corners(pose):
 x,y,t=pose;c=math.cos(t);s=math.sin(t)
 return [(x+a*.44*c-b*.375*s,y+a*.44*s+b*.375*c)for a,b in SIGNS]
def point_segment(p,a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];n=dx*dx+dy*dy;t=max(0.,min(1.,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/n))if n else 0.
 return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
def polygon_distance(a,b):
 # Separation test expressed in polygon edge normals, independent of SAT formula.
 separated=False
 for poly in[a,b]:
  for x,y in zip(poly,poly[1:]+poly[:1]):
   n=(y[1]-x[1],x[0]-y[0]);pa=[p[0]*n[0]+p[1]*n[1]for p in a];pb=[p[0]*n[0]+p[1]*n[1]for p in b]
   if min(pa)>max(pb)or min(pb)>max(pa):separated=True
 if not separated:return 0.
 return min([point_segment(p,x,y)for p in a for x,y in zip(b,b[1:]+b[:1])]+[point_segment(p,x,y)for p in b for x,y in zip(a,a[1:]+a[:1])])
def distances(pose,known):
 body=corners(pose);v=[min(p[0]+5 for p in body),min(5-p[0]for p in body),min(p[1]+5 for p in body),min(5-p[1]for p in body)]
 for x,y,hx,hy in known['known_rectangles']:
  other=[(x+a*hx,y+b*hy)for a,b in SIGNS];v.append(polygon_distance(body,other))
 for x,y,r in known['known_circles']:
  # Distances from circle centre to polygon edges; inside detected by oriented edges.
  cross=[(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])for a,b in zip(body,body[1:]+body[:1])]
  inside=min(cross)>=-1e-14 or max(cross)<=1e-14
  distance=min(point_segment((x,y),a,b)for a,b in zip(body,body[1:]+body[:1]));v.append((-distance if inside else distance)-r)
 return v
