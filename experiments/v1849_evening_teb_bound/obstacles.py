"""Only current public static geometry for reference internal point cost."""
import math
def make(known):
 points=set()
 def segment(a,b):
  n=max(1,math.ceil(math.dist(a,b)/.1))
  for i in range(n+1):points.add(tuple(a[j]+i/n*(b[j]-a[j])for j in range(2)))
 for x,y,hx,hy in known['known_rectangles']:
  corners=[[x-hx,y-hy],[x+hx,y-hy],[x+hx,y+hy],[x-hx,y+hy]]
  for a,b in zip(corners,corners[1:]+corners[:1]):segment(a,b)
 for x,y,radius in known['known_circles']:
  n=max(12,math.ceil(math.tau*radius/.1))
  for i in range(n):points.add((x+radius*math.cos(math.tau*i/n),y+radius*math.sin(math.tau*i/n)))
 corners=[[-5.,-5.],[5.,-5.],[5.,5.],[-5.,5.]]
 for a,b in zip(corners,corners[1:]+corners[:1]):segment(a,b)
 assert 0<len(points)<=4096
 return [list(p)for p in sorted(points)]
