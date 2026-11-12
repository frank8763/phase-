"""Finite measured-state recovery with full stop; never a substitute for arrival."""
import sys,json,math,importlib.util
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];CORE=R/'experiments/rpccr_execution_core'
sys.path.insert(0,str(CORE));import live_reference as live
from kernel import REQUIRED,checks,ref
def planner(output):
 s=importlib.util.spec_from_file_location('registered_coarse_corridor',R/'experiments/v1090_gear_prefix_reference/static_planner.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.O=Path(output);return m
def proof(setup,packet,source,requests):
 ss,uu,p=live.run_requests(setup,packet,requests);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[:,:3]);low=float(np.minimum(a,b).min());cc,_=checks(ss,uu,np.array(requests),packet,setup,ss[-1,:2],low,REQUIRED)
 cc['complete2200stop']=bool(len(requests)>=2200 and np.array_equal(requests[-2200:],np.zeros((2200,3))))
 cc['terminal_full_cycle_hold']=bool(min(a[-1],b[-1])>=REQUIRED)
 return dict(passed=bool(all(cc.values())),checks={k:bool(v)for k,v in cc.items()},minimum_full_cycle_raw_m=low,native=len(requests),finite_corridor_not_original_goal=True,endpoint_xy=ss[-1,:2].tolist()),ss,uu
def construct(setup,packet,source,output,goal):
 static=planner(output).construct(setup,packet,None,goal,wall_s=30.,max_expansions=20000);assert static['passed']and static.get('functional_goal_source'),'NO_COMPLETE_STATIC_TOPOLOGY_FOR_RECOVERY'
 rr=np.array(static['planned_body_requests']);positive=np.flatnonzero(rr[:,0]>.005);negative=np.flatnonzero(rr[:,0]<-.005);assert len(positive),'NO_FORWARD_RETURN_IN_CORRIDOR';start=int(positive[0]);assert not len(negative)or negative[-1]<start,'MULTIPLE_REVERSE_EPISODES_UNQUALIFIED';pre=rr[:start]
 if len(negative):
  k=len(pre)
  while k and np.array_equal(pre[k-1],np.zeros(3)):k-=1
  assert len(pre)-k>=200;pre=np.vstack([pre[:k],np.zeros((2200,3))])
 rows=[]
 for forward in [2000,1500,1000,500,0]:
  suffix=rr[start:start+forward]
  if forward and(len(suffix)!=forward or np.any(suffix[:,0]<0)):continue
  requests=np.vstack([pre,suffix,np.zeros((2200,3))]);q,ss,uu=proof(setup,packet,source,requests);q['forward_native']=forward;q['static_complete_goal_not_executed']=True;rows.append(q)
  if q['passed']:
   distance=float(np.linalg.norm(ss[-1,:2]-np.array(packet['body'][:2])));q['predicted_motion_m']=distance
   if distance>=.05:return dict(proof=q,candidates=rows,requests=requests,states=ss,controls=uu,static_actions=static['actions'])
 raise AssertionError(('NO_FULLY_CERTIFIED_FINITE_RECOVERY_CORRIDOR',rows))
