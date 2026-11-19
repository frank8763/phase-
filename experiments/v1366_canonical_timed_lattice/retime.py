"""Same canonical curves; explicit nominal acceleration and stop-time profiles."""
import copy
import math
import numpy as np
from numpy.polynomial import polynomial as poly


def retime(graph,speed_cap):
    result=copy.deepcopy(graph)
    for edge in result['edges']:
        a=np.array(edge['coefficient']);grid=np.linspace(0,1,4001)
        xy=np.c_[poly.polyval(grid,a[:,0]),poly.polyval(grid,a[:,1])]
        ds=np.linalg.norm(np.diff(xy,axis=0),axis=1);arc=np.r_[0.,np.cumsum(ds)];length=float(arc[-1])
        dx=np.c_[poly.polyval(grid,poly.polyder(a[:,0])),poly.polyval(grid,poly.polyder(a[:,1]))]
        ddx=np.c_[poly.polyval(grid,poly.polyder(a[:,0],2)),poly.polyval(grid,poly.polyder(a[:,1],2))]
        k=edge['gear']*(dx[:,0]*ddx[:,1]-dx[:,1]*ddx[:,0])/np.linalg.norm(dx,axis=1)**3
        angles=np.unwrap(np.arctan2(dx[:,1],dx[:,0])+(math.pi if edge['gear']<0 else 0.))
        initial=edge['samples'][0][2];angles+=round((initial-angles[0])/math.tau)*math.tau
        delta=np.arctan(.6*k);per_metre=float(np.max(abs(np.diff(delta))/np.maximum(ds,1e-12)))
        cap=min(speed_cap,.599/max(per_metre,1e-12))
        peak=min(cap,math.sqrt(2*length/(1/.1+1/.05)));ta=peak/.1;tb=peak/.05
        acceleration_distance=peak*ta/2;braking_distance=peak*tb/2
        cruise=max(0.,(length-acceleration_distance-braking_distance)/peak);moving=ta+cruise+tb
        total=math.ceil((.4+moving+2.)/.2-1e-9)*.2;rows=[]
        for t in np.linspace(0,total,round(total/.05)+1):
            u=max(0.,t-.4)
            if u<=ta:s=.05*u*u;speed=.1*u
            elif u<=ta+cruise:s=acceleration_distance+peak*(u-ta);speed=peak
            elif u<=moving:
                z=u-ta-cruise;s=acceleration_distance+peak*cruise+peak*z-.025*z*z;speed=max(0.,peak-.05*z)
            else:s=length;speed=0.
            parameter=float(np.interp(min(s,length),arc,grid))
            rows.append([float(poly.polyval(parameter,a[:,0])),float(poly.polyval(parameter,a[:,1])),
                         float(np.interp(parameter,grid,angles)),float(t),edge['gear']*speed,
                         float(np.interp(parameter,grid,delta))])
        edge.update(samples=rows,duration_s=total,length_m=length,speed_cap_m_s=cap,
                    peak_speed_m_s=peak,maximum_nominal_steering_rate_rad_s=per_metre*peak)
    result['diagnostic_speed_cap']=speed_cap
    return result
