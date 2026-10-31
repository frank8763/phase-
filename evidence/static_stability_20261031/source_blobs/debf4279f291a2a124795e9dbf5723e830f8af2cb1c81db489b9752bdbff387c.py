"""Offline sufficient infeasibility certificate for the central quadrant doorway.
Audit truth never enters online control. The center-space crosscut joins the
north partition tip to an unknown circle and the east partition. For this scene
it connects top/right workspace boundaries; start and goal lie on opposite sides.
If EVERY pose on BOTH connector segments has clearance below the hard floor,
a continuous rectangular-envelope path respecting that floor cannot cross.
A Lipschitz sampling remainder provides a conservative upper bound, not a mere
negative grid-connectivity result. Applies to the specified fixed self envelope.
"""
import argparse,json,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from exact_footprint import pose_values
p=argparse.ArgumentParser();p.add_argument('paired');p.add_argument('--name',required=True);p.add_argument('--admission-domain',action='store_true');a=p.parse_args();root=Path(a.paired);j=json.loads((root/'STATIC_PROTOCOL.json').read_text());b=np.array(j['footprint_bounds']);
if a.admission_domain:
    from geometry_predictor import SELF_DOMAIN
    b=SELF_DOMAIN.copy()
assert np.allclose(b[:2],-b[2:]);chain=np.array([u['xy']for u in sorted(j['physical_unknown_obstacles'],key=lambda x:x['xy'][0])]);circle=chain[-1]
# This audited family has a north wall x=0,y>=1.5, and east wall y=0,x>=1.30.
rect=np.asarray(j['known_rectangles']);north=rect[0];east=rect[3]
assert np.allclose(north[:2],[0,3.25])and np.allclose(east[:2],[3.15,0])
A=np.array([north[0]+north[2],north[1]-north[3]]);C=np.array([circle[0],east[1]+east[3]])
assert C[0]>=east[0]-east[2] and circle[0]>A[0] and circle[1]>C[1]
field=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=rect,circles=np.array(j['known_circles']+[[*x['xy'],x['radius']]for x in j['physical_unknown_obstacles']]),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
polygon=np.array([[0,5],A,*chain,C,[5,C[1]],[5,5]],float)
def inside(point):
    x,y=point;result=False
    for a,bp in zip(polygon,np.roll(polygon,-1,axis=0)):
        if (a[1]>y)!=(bp[1]>y) and x<(bp[0]-a[0])*(y-a[1])/(bp[1]-a[1])+a[0]:result=not result
    return result
start=j['start_qpos'][:2];goal=j['goal_xy'];assert inside(start)!=inside(goal)
started=time.monotonic();rows=[];ds=.002;da=np.deg2rad(.5);angle=np.arange(0,np.pi,da);radius=float(max(np.linalg.norm(x)for x in [[b[0],b[1]],[b[0],b[3]],[b[2],b[1]],[b[2],b[3]]]))
for start,end in zip([A,*chain],[*chain,C]):
    length=float(np.linalg.norm(end-start));n=int(np.ceil(length/ds));positions=start+np.arange(n+1)[:,None]/n*(end-start);best=0.;best_pose=None
    for i in range(0,len(positions),24):
        xy=positions[i:i+24];poses=np.c_[np.repeat(xy,len(angle),axis=0),np.tile(angle,len(xy))];values=np.maximum(pose_values(field,poses),0)
        k=int(values.argmax())
        if values[k]>best:best=float(values[k]);best_pose=poses[k].tolist()
    # Exact set-distance is 1-Lipschitz in translation; robot Hausdorff motion
    # under rotation is bounded by its maximum corner radius times angle.
    remainder=float(length/n/2+radius*da/2)
    rows.append({'start':start.tolist(),'end':end.tolist(),'maximum_sampled_clearance_m':best,'maximizing_sample_pose':best_pose,'sampling_remainder_m':remainder,'continuous_clearance_upper_bound_m':best+remainder,'certified_below_015':bool(best+remainder<.15)})
result={'scope':__doc__,'seed':j['seed'],'audited_envelope_bounds_xy':b.tolist(),'admission_domain_override':a.admission_domain,'separating_polygon':polygon.tolist(),'start_and_goal_opposite_sides':True,'segments':rows,'both_connectors_certified_blocked':all(x['certified_below_015']for x in rows),'elapsed_s':time.monotonic()-started,'simulation_steps':0,'caveat':'certificate is for the prescribed rectangular self envelope and this crosscut geometry, not arbitrary actual-body geometry or all scene families'}
(root/a.name).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
