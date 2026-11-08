"""Same legacy sampled rays; batch point tests without changing ray steps or rounding."""
import math
import numpy as np
def get_lidar_features(env,num_rays=16,max_range=3.0):
    origin=np.asarray(env.robot_xy,dtype=np.float32)
    yaw=float(env.robot_yaw)
    directions=np.asarray([[math.cos(yaw+2.*math.pi*i/num_rays),math.sin(yaw+2.*math.pi*i/num_rays)]for i in range(num_rays)],dtype=np.float32)
    distances=[];distance=0.
    while distance<=max_range:distances.append(distance);distance+=.08
    # A scalar multiplication for each original d preserves NumPy's weak-scalar
    # float32 rounding exactly; a float64 broadcast grid would change the sensor.
    points=np.stack([origin+d*directions for d in distances],axis=0).astype(np.float64)
    x,y=points[...,0],points[...,1]
    occupied=(x<float(env.map_min))|(x>float(env.map_max))|(y<float(env.map_min))|(y>float(env.map_max))
    if hasattr(env,'rect_obstacles'):
        for cx,cy,hx,hy in np.asarray(env.rect_obstacles,dtype=np.float32).reshape(-1,4).astype(np.float64):
            occupied|=(abs(x-cx)<=hx)&(abs(y-cy)<=hy)
    if hasattr(env,'circle_obstacles'):
        for ox,oy,r in np.asarray(env.circle_obstacles,dtype=np.float32).reshape(-1,3).astype(np.float64):
            dx=x-ox;dy=y-oy;squared=dx**2+dy**2;radius=float(r)**2
            inside=squared<=radius
            # Python float **2 and NumPy square need not share a libm path.
            # Re-evaluate any roundoff-near boundary using the original scalar formula.
            near=np.abs(squared-radius)<=8*np.finfo(float).eps*np.maximum(1.,np.maximum(abs(squared),abs(radius)))
            for i,j in np.argwhere(near):inside[i,j]=(float(x[i,j])-float(ox))**2+(float(y[i,j])-float(oy))**2<=float(r)**2
            occupied|=inside
    found=np.any(occupied,axis=0);first=np.argmax(occupied,axis=0)
    values=np.where(found,np.asarray(distances,dtype=float)[first],float(max_range))/max_range
    return np.asarray(values,dtype=np.float32)
