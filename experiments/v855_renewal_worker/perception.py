"""Censoring-aware reconstruction using only measured ranges and declared sensor metadata."""
import math
import numpy as np

def measured_points(env,bounded=True):
    origin=np.asarray(env.robot_xy,dtype=float);yaw=float(env.robot_yaw);world=[];local=[];stats={}
    channels=[('lidar',np.asarray(env.phase17c_last_lidar,float),float(env.phase17c_lidar_max_range),.06),('depth',np.asarray(env.phase17c_last_depth,float),float(env.phase17c_depth_max_range),.09)]
    for name,values,maximum,clip_bound in channels:
        values=np.clip(values.reshape(-1),0.,1.);ranges=values*maximum
        angles=(np.arange(len(values))*2*np.pi/len(values) if name=='lidar' else np.linspace(-math.radians(35),math.radians(35),len(values)))
        old=(ranges>.05)&(ranges<.985*maximum)
        # A no-hit return R corrupted by eps >= -b cannot be smaller than R-b.
        # These rays remain censored, rather than being inserted as occupied endpoints.
        hit=(ranges>.05)&(ranges<maximum-clip_bound-1e-5) if bounded else old
        stats[name]={'measured_rays':len(ranges),'legacy_hits':int(old.sum()),'retained_hits':int(hit.sum()),'censored_legacy_hits':int(np.sum(old&~hit)),'noise_clip_m':clip_bound}
        d=ranges[hit];alpha=angles[hit]
        local.append(np.column_stack((d*np.cos(alpha),d*np.sin(alpha))))
        world.append(origin+np.column_stack((d*np.cos(yaw+alpha),d*np.sin(yaw+alpha))))
    return np.concatenate(world).reshape(-1,2),np.concatenate(local).reshape(-1,2),stats
