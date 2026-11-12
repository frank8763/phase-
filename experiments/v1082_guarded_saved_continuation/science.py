"""One fixed dual-front predictor, original field/limits and complete stop gates."""
import numpy as np,math,json
from pathlib import Path
from common import R,C,O,RAW,paths,load,sha,dump
paths()
from kernel import PARAMETERS,Geometry,REQUIRED,checks,ref,law,virtual
from transient_model import Predictor,initial
ARCH=R/'runs/v858_nav2_verified/v1078/saved_NS_complete_goal';REC=R/'records/nav2_v1077_v1078_20261112/v1079_dual_steering_qualification'
def contracts(task,gate=True):
 assert task in json.loads((C/'TASKS.json').read_text())and Path(task['output'])==RAW/task['task_id'];assert task['case_id']=='NORTH_SOUTH'and task['seed']==10010002
 return Path(task['output'])
def requests(task):
 if task['kind']=='turn_return':return np.vstack([np.tile([.125,0.,0.],(200,1)),np.tile([.125,.125*math.tan(task['target'])/.6,0.],(80,1)),np.tile([.125,0.,0.],(125,1)),np.zeros((2200,3))])
 x=np.load(REC/'REMAINDER_SOURCE.npz')['requests'];assert x.shape==(3555,3)and np.array_equal(x[-2200:],np.zeros((2200,3)));return x

def plan(setup,packet,source,rr,task):
 p=Predictor(setup,initial(packet),PARAMETERS);ss=[p.state.copy()];ff=[p.front.copy()];uu=[]
 for req in rr:s,u=p.step(*req);ss.append(s);ff.append(p.front.copy());uu.append(u)
 ss=np.asarray(ss);uu=np.asarray(uu);ff=np.asarray(ff)
 if source is None:low=float(ref._old.Geometry(setup['known'],None).clearances(ss[:,:3])[0].min())
 else:low=Geometry(setup['known'],source['periodic'],packet['sim_time']).complete(ss)
 cc,upper=checks(ss,uu,rr,packet,setup,np.asarray(task['goal_xy']),low,REQUIRED)
 if task['kind']=='turn_return':
  cc.pop('goal_upper');cc['return_while_moving']=bool(abs(ff[405]).max()<=.02 and ss[405,3]>=.10)
 else:cc['continuation_over1m']=bool(np.linalg.norm(ss[-1,:2]-ss[0,:2])>=1.)
 cc['complete2200_stop']=bool(np.array_equal(rr[-2200:],np.zeros((2200,3))));cc={k:bool(v)for k,v in cc.items()}
 return dict(passed=all(cc.values()),checks=cc,minimum_raw_m=low,goal_upper_m=upper,states=ss,controls=uu,requests=rr,front_states=ff)
