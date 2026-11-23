"""Internal author point-cost map from current public geometry, no authority."""
import math

def make(known,goal):
 rect=known['known_rectangles'];circles=known['known_circles']
 collision=[];distance=[];angle=[];speed=[]
 for ix in range(100):
  x=5.-(ix+.5)*.1
  for iy in range(100):
   y=5.-(iy+.5)*.1
   occupied=any(abs(x-cx)<=hx and abs(y-cy)<=hy for cx,cy,hx,hy in rect)or any(math.hypot(x-cx,y-cy)<=radius for cx,cy,radius in circles)
   collision.append(float(occupied));distance.append(abs(y-goal[1]));angle.append(0.);speed.append(.08)
 return dict(nx=100,ny=100,resolution=.1,center=[0.,0.],collision_layer=collision,distance_field=distance,angle_field=angle,speed_field=speed,point_occupancy_only_not_footprint_certificate=True)
