"""Shared complete-source prediction and retained original safety gates."""
import json,math
from pathlib import Path
import numpy as np
from kernel import PARAMETERS,Geometry,REQUIRED,checks,ref
from prediction import Predictor,initial
R=Path(__file__).resolve().parents[2]
REC=R/'records/nav2_v1077_v1078_20261112/v1079_dual_steering_qualification'
ARCH=R/'runs/v858_nav2_verified/v1078/saved_NS_complete_goal'
def requests():
 rr=np.load(REC/'REMAINDER_SOURCE.npz')['requests'];assert rr.shape==(3555,3)and np.array_equal(rr[-2200:],np.zeros((2200,3)));return rr

def complete(setup,packet,source):
 rr=requests();p=Predictor(setup,initial(packet),PARAMETERS);ss=[p.state.copy()];uu=[];reserve=[]
 for r in rr:
  s,u=p.step(*r);ss.append(s);uu.append(u);reserve.append(p.adapter.last_braking_reserve)
 ss=np.array(ss);uu=np.array(uu);low=Geometry(setup['known'],source['periodic'],packet['sim_time']).complete(ss);cc,upper=checks(ss,uu,rr,packet,setup,np.array(setup['case']['goal_xy']),low,REQUIRED);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[-1:,:3]);cc.update(terminal_hold_full_cycle=min(a[0],b[0])>=REQUIRED,complete2200zero=np.array_equal(rr[-2200:],np.zeros((2200,3))),over1m=np.linalg.norm(ss[-1,:2]-ss[0,:2])>=1.);cc={k:bool(v)for k,v in cc.items()};return dict(passed=all(cc.values()),checks=cc,minimum_raw_m=low,goal_upper_m=upper),ss,uu,rr
