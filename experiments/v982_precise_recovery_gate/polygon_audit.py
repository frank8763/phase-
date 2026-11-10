"""Independent scalar feature distance in body coordinates; no online geometry calls."""
import math
import numpy as np
from support_envelope import polygon
from periodic_support import swept_bounds

def distance(pose,q):
    x,y,a=pose;c,s=math.cos(a),math.sin(a);poly=(np.asarray(q)-[x,y])@np.array([[c,-s],[s,c]])
    box=np.array([[-.44,-.375],[.44,-.375],[.44,.375],[-.44,.375]])
    separated=bool(np.any(poly.min(axis=0)>[.44,.375])or np.any(poly.max(axis=0)<[-.44,-.375]))
    for j in range(len(poly)):
        v=poly[(j+1)%len(poly)]-poly[j];n=np.array([-v[1],v[0]]);b=box@n;p=poly@n
        if p.min()>b.max()or b.min()>p.max():separated=True
    if not separated:return 0.
    best=float('inf')
    for v in poly:best=min(best,float(np.linalg.norm(v-np.clip(v,[-.44,-.375],[.44,.375]))))
    for b in box:
        for i,u in enumerate(poly):
            v=poly[(i+1)%len(poly)]-u;z=np.clip(np.dot(b-u,v)/np.dot(v,v),0,1);best=min(best,float(np.linalg.norm(b-u-z*v)))
    return best

def terminal_check(pose,prior,reserve):
    upper=swept_bounds(prior['vertices'],0.,2*math.pi/.32)
    return distance(pose,polygon(upper+1e-6))-.1-reserve-2e-6

def route_check(points,source):
    from snapshot_geometry import dense
    samples=dense(points);upper=swept_bounds(source['vertices'],0.,2*math.pi/.32);q=polygon(upper+1e-6)
    values=[distance(p,q)-.1-.06-2e-6 for p in samples];gap=.005+math.hypot(.44,.375)*.005
    return dict(passed=min(values)-gap>=.155,lower_m=min(values)-gap)
