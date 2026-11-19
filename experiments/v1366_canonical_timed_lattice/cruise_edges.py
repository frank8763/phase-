"""Exactly joined canonical boundary speeds with smooth length-matching cruise."""
import copy
import json
import math
import os
from pathlib import Path
import time
import numpy as np
from numpy.polynomial import polynomial as poly
from planner import R,C,O


def variant(edge,incoming,outgoing):
    a=np.array(edge['coefficient']);u=np.linspace(0,1,6001);xy=np.c_[poly.polyval(u,a[:,0]),poly.polyval(u,a[:,1])]
    ds=np.linalg.norm(np.diff(xy,axis=0),axis=1);arc=np.r_[0.,np.cumsum(ds)];length=float(arc[-1])
    dx=np.c_[poly.polyval(u,poly.polyder(a[:,0])),poly.polyval(u,poly.polyder(a[:,1]))];ddx=np.c_[poly.polyval(u,poly.polyder(a[:,0],2)),poly.polyval(u,poly.polyder(a[:,1],2))]
    k=edge['gear']*(dx[:,0]*ddx[:,1]-dx[:,1]*ddx[:,0])/np.linalg.norm(dx,axis=1)**3
    angles=np.unwrap(np.arctan2(dx[:,1],dx[:,0])+(math.pi if edge['gear']<0 else 0.));angles+=round((edge['samples'][0][2]-angles[0])/math.tau)*math.tau
    steering=np.arctan(.6*k)
    accelerate=1. if incoming==0 else 0.;brake=2. if outgoing==0 else 0.
    before=.4 if incoming==0 else 0.;after=2. if outgoing==0 else 0.
    remaining=length-(.05 if accelerate else 0.)-(.1 if brake else 0.);assert remaining>0
    cruising=math.ceil(remaining/.1/.2)*.2;amplitude=max(0.,2*(.1-remaining/cruising))
    assert 0<=amplitude<.1 and amplitude*math.pi/cruising<=.1+1e-8
    total=before+accelerate+cruising+brake+after;rows=[]
    for t in np.linspace(0,total,round(total/.05)+1):
        q=t-before
        if q<=0:s=0.;v=0. if incoming==0 else .1
        elif accelerate and q<=accelerate:s=.05*q*q;v=.1*q
        elif q<=accelerate+cruising:
            z=q-accelerate;s=(.05 if accelerate else 0.)+.1*z-amplitude*(z/2-cruising*math.sin(2*math.pi*z/cruising)/(4*math.pi))
            v=.1-amplitude*math.sin(math.pi*z/cruising)**2
        elif brake and q<=accelerate+cruising+brake:
            z=q-accelerate-cruising;s=(.05 if accelerate else 0.)+remaining+.1*z-.025*z*z;v=max(0.,.1-.05*z)
        else:s=length;v=0. if outgoing==0 else .1
        parameter=float(np.interp(min(max(s,0.),length),arc,u))
        rows.append([float(poly.polyval(parameter,a[:,0])),float(poly.polyval(parameter,a[:,1])),float(np.interp(parameter,u,angles)),float(t),edge['gear']*v,float(np.interp(parameter,u,steering))])
    result=copy.deepcopy(edge);result.update(samples=rows,duration_s=total,incoming_speed_state=incoming,outgoing_speed_state=outgoing,
            rest_budget_ticks=round((before+after)/.2),cruise_dip_amplitude=amplitude,cruise_duration_s=cruising,arc_length_m=length)
    p=np.array(rows);assert abs(p[0,4]-edge['gear']*.1*incoming)<1e-8 and abs(p[-1,4]-edge['gear']*.1*outgoing)<1e-8
    assert abs(p[:,4]).max()<=.1+1e-8 and np.max(abs(np.diff(p[:,4]))/.05)<=.10000001
    assert np.max(abs(np.diff(p[:,5]))/.05)<=.600001
    return result


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'CRUISE_GRAPH.json';assert not target.exists()
    graph=json.loads((O/'GRAPH_INPUT.json').read_text());edges=[]
    for edge in graph['edges']:
        for incoming in [0,1]:
            if edge['start_heading']==16 and incoming:continue
            for outgoing in [0,1]:edges.append(variant(edge,incoming,outgoing))
    graph['edges']=edges;graph.update(continuous_boundary_speeds=True,wall_s=time.monotonic()-begin,models=0,physical_native=0)
    target.write_text(json.dumps(graph,separators=(',',':'))+'\n')
    print(json.dumps(dict(temporal_edges=len(edges),wall_s=graph['wall_s'],models=0)))


if __name__=='__main__':main()
