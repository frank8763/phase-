"""Progress/time scheduling of one fixed whole-goal profile, .08/.03/zero only.

The geometry lattice is proposal-only. No sampled graph edge is an execution
certificate; regenerate every actual controller state and full timed geometry.
"""
import sys,importlib.abc,json,math,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1076_complete_goal_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import predict,Predictor,PARAMETERS,initial,Geometry,REQUIRED,checks,ref
from recovery_source import forecast_packet
start=time.monotonic();x=json.loads((R/'runs/v1069_retained_goal_corridor/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());ss,uu,rr,mm=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);packet=forecast_packet(x['packet'],ss[-1],mm[-1],1001);baseline=np.load(O/'PATH_PHASE_DIAGNOSIS.npz');s=baseline['states'];requests=baseline['requests'][:-200];n=len(requests);bounds=np.r_[np.arange(0,n,75),n];g=Geometry(x['setup']['known'],x['source']['periodic'],packet['sim_time']);norm=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];base=s[:,:2]@norm.T-.44*abs(np.c_[np.cos(s[:,2]),np.sin(s[:,2])]@norm.T)-.375*abs(np.c_[-np.sin(s[:,2]),np.cos(s[:,2])]@norm.T)-.1;static=g.static.clearances(s[:,:3])[0];J=160;parents={(0,0):None};goal=None;edges=0;pre=[]
for i,a in enumerate(bounds[:-1]):
 b=bounds[i+1];k=b-a;entries=[('fast',k,np.arange(k+1,dtype=float))]
 if np.all(requests[a:b,0]==.08):entries.append(('slow',k*8//3,np.linspace(0,k,k*8//3+1)))
 for kind,duration,coords in entries:
  coords+=a;bb=np.column_stack([np.interp(coords,np.arange(len(base)),base[:,z])for z in range(16)]);st=np.interp(coords,np.arange(len(static)),static);pre.append((i,kind,duration,bb,st))
by={i:[x for x in pre if x[0]==i]for i in range(len(bounds)-1)}
for j in range(J+1):
 for i,a in enumerate(bounds):
  node=(i,j)
  if node not in parents:continue
  if i==len(bounds)-1:goal=node;break
  for _,kind,duration,bb,st in by[i]:
   extra=duration-(bounds[i+1]-a);assert extra%25==0
   jj=j+extra//25
   if jj>J:continue
   ticks=a+j*25+np.arange(duration+1);indices=np.minimum(((packet['sim_time']+ticks*.01)%g.period/g.bin).astype(int),len(g.support)-1);low=np.minimum(st,(bb-g.support[indices]).max(axis=1));edges+=1
   if low.min()>=REQUIRED:parents.setdefault((i+1,jj),(node,kind))
  if j+8<=J:
   ticks=a+j*25+np.arange(201);indices=np.minimum(((packet['sim_time']+ticks*.01)%g.period/g.bin).astype(int),len(g.support)-1);low=np.minimum(static[a],(base[a]-g.support[indices]).max(axis=1));edges+=1
   if low.min()>=REQUIRED:parents.setdefault((i,j+8),(node,'wait'))
 if goal is not None:break
result=dict(passed=False,complete_goal_passed=False,models=0,integrations=0,graph_nodes=len(parents),graph_edges=edges,furthest_profile_tick=int(bounds[max(i for i,j in parents)]),fixed_profile_only=True,all_old_safety_thresholds_unchanged=True)
if goal is None:result['status']='NO_SPEED_SCHEDULE_ON_FIXED_PROFILE'
else:
 chain=[];q=goal
 while parents[q]is not None:
  previous,kind=parents[q];chain.append((previous,q,kind));q=previous
 chain.reverse();parts=[];schedule=[]
 for a,b,kind in chain:
  begin=int(bounds[a[0]]);end=int(bounds[b[0]])
  if kind=='wait':req=np.zeros((200,3))
  elif kind=='fast':req=requests[begin:end]
  else:
   original=requests[begin:end];k=len(original);count=k*8//3;indices=np.minimum((np.arange(count)*3//8),k-1);req=original[indices].copy();req[:,:2]*=.375
  parts.append(req);schedule.append(dict(kind=kind,profile_begin=begin,profile_end=end,native=len(req)))
 parts.append(np.zeros((2200,3)));candidate=np.vstack(parts);p=Predictor(x['setup'],initial(packet),PARAMETERS);states=[p.state.copy()];controls=[]
 for request in candidate:q,u=p.step(*request);states.append(q);controls.append(u)
 states=np.asarray(states);controls=np.asarray(controls);low=Geometry(x['setup']['known'],x['source']['periodic'],packet['sim_time']).complete(states);cc,upper=checks(states,controls,candidate,packet,x['setup'],np.asarray(x['goal']),low,REQUIRED);aa,bb=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(states[-1:,:3]);cc['terminal_full_cycle_hold']=bool(min(aa[0],bb[0])>=REQUIRED);cc['complete2200_stop']=bool(np.array_equal(candidate[-2200:],np.zeros((2200,3))));cc['qualified_speed_values']=bool(np.all(np.isin(candidate[:,0],[0.,.03,.08])));result.update(passed=all(cc.values()),complete_goal_passed=all(cc.values()),status='ORIGINAL_PYTHON_SPEED_SCHEDULE_COMPLETE_GOAL_PASS'if all(cc.values())else'ORIGINAL_PYTHON_SPEED_SCHEDULE_REJECTED',checks={k:bool(v)for k,v in cc.items()},minimum_raw_m=low,terminal_goal_upper_m=upper,analytical_native=len(candidate),slow_segments=sum(z['kind']=='slow'for z in schedule),wait_segments=sum(z['kind']=='wait'for z in schedule),additional_graph_time_native=goal[1]*25);np.savez_compressed(O/'SPEED_SCHEDULE_SOURCE.npz',states=states,controls=controls,requests=candidate);(O/'SPEED_SCHEDULE.json').write_text(json.dumps(schedule,indent=2)+'\n');(O/'SPEED_SCHEDULE_PACKET.json').write_text(json.dumps(packet)+'\n')
result['wall_s']=time.monotonic()-start;(O/'SPEED_SCHEDULE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
