"""Fixed quintic endpoint-matching nominal graph edges. No vehicle imports."""
import hashlib
import json
import math
import os
from pathlib import Path
import time
import numpy as np
from numpy.polynomial import polynomial as poly

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
DIRECTIONS=np.array([[1,0],[2,1],[1,1],[1,2],[0,1],[-1,2],[-1,1],[-2,1],[-1,0],[-2,-1],[-1,-1],[-1,-2],[0,-1],[1,-2],[1,-1],[2,-1]],float)
HEADINGS=np.arctan2(DIRECTIONS[:,1],DIRECTIONS[:,0])
STEP=.2


def bounded_minimum(function,lower,upper):
    ratio=(math.sqrt(5)-1)/2
    a=upper-ratio*(upper-lower);b=lower+ratio*(upper-lower);fa=function(a);fb=function(b)
    for _ in range(40):
        if upper-lower<1e-7:break
        if fa<fb:upper=b;b=a;fb=fa;a=upper-ratio*(upper-lower);fa=function(a)
        else:lower=a;a=b;fa=fb;b=lower+ratio*(upper-lower);fb=function(b)
    return a if fa<fb else b


def coeff(end,theta0,theta1,gear,distance,k0):
    first=gear*distance*np.array([math.cos(theta0),math.sin(theta0)])
    last=gear*distance*np.array([math.cos(theta1),math.sin(theta1)])
    second=k0*distance**2*np.array([-math.sin(theta0),math.cos(theta0)])
    a=np.zeros((6,2));a[1]=first;a[2]=second/2
    a[3]=10*end-6*first-4*last-1.5*second
    a[4]=-15*end+8*first+7*last+1.5*second
    a[5]=6*end-3*first-3*last-.5*second
    return a


def properties(a):
    dx=poly.polyder(a[:,0]);dy=poly.polyder(a[:,1]);ddx=poly.polyder(dx);ddy=poly.polyder(dy)
    numerator=poly.polysub(poly.polymul(dx,ddy),poly.polymul(dy,ddx));denominator=poly.polyadd(poly.polymul(dx,dx),poly.polymul(dy,dy))
    extremum=poly.polysub(poly.polymul(poly.polyder(numerator),denominator),1.5*poly.polymul(numerator,poly.polyder(denominator)))
    roots=poly.polyroots(extremum) if abs(extremum).max()>1e-12 else []
    points=[0.,1.]+[float(x.real) for x in roots if abs(x.imag)<1e-7 and 0<x.real<1]
    speedroots=poly.polyroots(poly.polyder(denominator));speedpoints=[0.,1.]+[float(x.real) for x in speedroots if abs(x.imag)<1e-7 and 0<x.real<1]
    minimum=float(np.min(poly.polyval(speedpoints,denominator)))
    if minimum<1e-10:return 1e6,None
    curvature=poly.polyval(points,numerator)/np.maximum(poly.polyval(points,denominator),1e-30)**1.5
    return float(abs(curvature).max()),(dx,dy,ddx,ddy,numerator,denominator)


def make_edge(start_heading,end_heading,offset,gear,initial_curvature=0.):
    endpoint=np.asarray(offset)*STEP;chord=float(np.linalg.norm(endpoint))
    if chord<.19:return None
    theta0=HEADINGS[start_heading];theta1=HEADINGS[end_heading]
    def objective(scale):
        a=coeff(endpoint,theta0,theta1,gear,chord*scale,initial_curvature)
        maximum,_=properties(a);return maximum
    scale=bounded_minimum(objective,.65,1.7)
    a=coeff(endpoint,theta0,theta1,gear,chord*scale,initial_curvature);maximum,terms=properties(a)
    if maximum>.499 or terms is None:return None
    grid=np.linspace(0,1,2001);dx,dy,ddx,ddy,numerator,denominator=terms
    xy=np.column_stack([poly.polyval(grid,a[:,j]) for j in [0,1]])
    vx=poly.polyval(grid,dx);vy=poly.polyval(grid,dy)
    angle=np.unwrap(np.arctan2(vy,vx)+(math.pi if gear<0 else 0.));angle+=round((theta0-angle[0])/math.tau)*math.tau
    ds=np.hypot(np.diff(xy[:,0]),np.diff(xy[:,1]));arc=np.r_[0.,np.cumsum(ds)];length=float(arc[-1])
    curvature=gear*poly.polyval(grid,numerator)/poly.polyval(grid,denominator)**1.5
    center_steer=np.arctan(.6*curvature)
    rate=float(np.max(abs(np.diff(center_steer))/np.maximum(ds,1e-12))*.1)
    if rate>.599:return None
    assert np.max(abs(xy[0]))<1e-10 and np.max(abs(xy[-1]-endpoint))<1e-9
    assert abs(math.atan2(math.sin(angle[-1]-theta1),math.cos(angle[-1]-theta1)))<1e-8
    assert abs(curvature[0]-initial_curvature)<1e-8 and abs(curvature[-1])<1e-8
    # Distances are assigned a full accelerate/cruise/decelerate/rest profile.
    cruise=max(0.,(length-.15)/.1);moving=1.+cruise+2.;total=math.ceil((.4+moving+2.)/.2-1e-9)*.2
    times=np.linspace(0,total,round(total/.05)+1);rows=[]
    for t in times:
        u=max(0.,t-.4)
        if u<=1.:s=.05*u*u;speed=.1*u
        elif u<=1.+cruise:s=.05+.1*(u-1.);speed=.1
        elif u<=moving:
            b=u-1.-cruise;s=.05+.1*cruise+.1*b-.025*b*b;speed=max(0.,.1-.05*b)
        else:s=length;speed=0.
        parameter=float(np.interp(min(s,length),arc,grid))
        position=[poly.polyval(parameter,a[:,j]) for j in [0,1]]
        heading=float(np.interp(parameter,grid,angle));k=float(np.interp(parameter,grid,curvature))
        rows.append([*position,heading,float(t),gear*speed,math.atan(.6*k)])
    return dict(start_heading=start_heading,end_heading=end_heading,offset=list(map(int,offset)),gear=gear,
                coefficient=a.tolist(),maximum_curvature_m_inv=maximum,maximum_nominal_steering_rate_rad_s=rate,
                length_m=length,duration_s=total,samples=rows,
                endpoint_and_heading_match_m_or_rad=max(float(np.max(abs(xy[-1]-endpoint))),abs(math.atan2(math.sin(angle[-1]-theta1),math.cos(angle[-1]-theta1)))),
                initial_curvature_m_inv=initial_curvature,end_curvature_m_inv=float(curvature[-1]))


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic();O.mkdir(exist_ok=True)
    target=O/'PRIMITIVES.json';assert not target.exists();edges=[]
    # Deterministic neighbors selected before using any failed search result.
    for h in range(16):
        for gear in [1,-1]:
            for count in [2,4]:
                offset=np.rint(DIRECTIONS[h]*gear*count).astype(int)
                edge=make_edge(h,h,offset,gear)
                if edge is not None:edges.append(edge)
            for change in [-1,1]:
                nxt=(h+change)%16;turn=math.atan2(math.sin(HEADINGS[nxt]-HEADINGS[h]),math.cos(HEADINGS[nxt]-HEADINGS[h]))
                radius=4.;local=np.array([math.sin(abs(turn))*radius,(1-math.cos(turn))*radius*(1 if turn>0 else -1)])
                # Reverse changes bodyheading in opposite travel direction.
                if gear<0:local=-local
                theta=HEADINGS[h];rotation=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
                offset=np.rint(rotation@local/STEP).astype(int)
                edge=make_edge(h,nxt,offset,gear)
                if edge is not None:edges.append(edge)
    value=dict(edges=edges,headings=HEADINGS.tolist(),directions=DIRECTIONS.tolist(),grid_step_m=STEP,
               certificate='exact polynomial endpoint constraints, analytic curvature extrema; nominal steering-rate dense bound',
               models=0,physical_native=0,physical_response_qualified=False,wall_s=time.monotonic()-begin)
    target.write_text(json.dumps(value,separators=(',',':'))+'\n')
    print(json.dumps(dict(edges=len(edges),turns=sum(z['start_heading']!=z['end_heading'] for z in edges),wall_s=value['wall_s'],models=0)))


if __name__=='__main__':main()
