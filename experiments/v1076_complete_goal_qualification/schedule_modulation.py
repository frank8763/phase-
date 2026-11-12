"""Fixed whole-goal profile with .25s forward braking modulation.

Movement requests remain the complete static source. A wait is200 native zero
requests; final original controller dynamics/timed geometry are regenerated.
No graph sampling is an execution certificate.
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
begun=time.monotonic();x=json.loads((R/'runs/v1069_retained_goal_corridor/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());ss,uu,rr,mm=predict(x['setup'],x['packet'],[dict(kind='wait',gear=0,target=0.,ticks=1001)],tail=False);packet=forecast_packet(x['packet'],ss[-1],mm[-1],1001);baseline=np.load(O/'PATH_PHASE_DIAGNOSIS.npz');s=baseline['states'];requests=baseline['requests'];n=len(requests);boundaries=np.r_[np.arange(0,n,25),n];g=Geometry(x['setup']['known'],x['source']['periodic'],packet['sim_time']);norm=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)];pose=s[:,:3];front=np.c_[np.cos(pose[:,2]),np.sin(pose[:,2])];left=np.c_[-np.sin(pose[:,2]),np.cos(pose[:,2])];base=pose[:,:2]@norm.T-.44*abs(front@norm.T)-.375*abs(left@norm.T)-.1;static=g.static.clearances(pose)[0]
# At most two public actor periods of additional waits. Minimum waiting first.
J=int(math.ceil(2*g.period/.01/25));parents={(0,0):None};goal=None;tested=0
for j in range(J+1):
 for i,a in enumerate(boundaries):
  node=(i,j)
  if node not in parents:continue
  if i==len(boundaries)-1:goal=node;break
  b=boundaries[i+1];ticks=np.arange(a,b+1);indices=np.minimum(((packet['sim_time']+(ticks+j*25)*.01)%g.period/g.bin).astype(int),len(g.support)-1);low=np.minimum(static[a:b+1],(base[a:b+1]-g.support[indices]).max(axis=1));tested+=1
  if low.min()>=REQUIRED:parents.setdefault((i+1,j),node)
  if j<J:
   ticks=np.arange(a+j*25,a+(j+1)*25+1);indices=np.minimum(((packet['sim_time']+ticks*.01)%g.period/g.bin).astype(int),len(g.support)-1);low=np.minimum(static[a],(base[a]-g.support[indices]).max(axis=1));tested+=1
   if low.min()>=REQUIRED:parents.setdefault((i,j+1),node)
 if goal is not None:break
result=dict(passed=False,complete_goal_passed=False,models=0,integrations=0,graph_nodes=len(parents),furthest_profile_tick=int(boundaries[max(i for i,j in parents)]),graph_edges_tested=tested,graph_scope='Fixed complete profile pose-time proposal only',max_wait_native=J*25)
if goal is None:result['status']='NO_MODULATED_TIMING_ON_FIXED_PROFILE_GRID'
else:
 chain=[];q=goal
 while parents[q]is not None:chain.append((parents[q],q));q=parents[q]
 chain.reverse();parts=[];waits=[]
 for a,b in chain:
  if a[0]==b[0]:parts.append(np.zeros((25,3)));waits.append(int(boundaries[a[0]]))
  else:parts.append(requests[boundaries[a[0]]:boundaries[b[0]]])
 # Keep the complete200 tail AND extend to the qualified2200 stop for SAC seam.
 parts.append(np.zeros((2000,3)));candidate=np.vstack(parts);p=Predictor(x['setup'],initial(packet),PARAMETERS);states=[p.state.copy()];controls=[]
 for request in candidate:
  state,u=p.step(*request);states.append(state);controls.append(u)
 states=np.asarray(states);controls=np.asarray(controls);minimum=Geometry(x['setup']['known'],x['source']['periodic'],packet['sim_time']).complete(states);cc,upper=checks(states,controls,candidate,packet,x['setup'],np.asarray(x['goal']),minimum,REQUIRED);aa,bb=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(states[-1:,:3]);cc['terminal_full_cycle_hold']=bool(min(aa[0],bb[0])>=REQUIRED);cc['full2200_stop']=bool(np.array_equal(candidate[-2200:],np.zeros((2200,3))));result.update(passed=all(cc.values()),complete_goal_passed=all(cc.values()),status='ORIGINAL_PYTHON_COMPLETE_GOAL_PASS'if all(cc.values())else'ORIGINAL_PYTHON_SCHEDULE_REJECTED',checks={k:bool(v)for k,v in cc.items()},wait_profile_native_ticks=waits,added_wait_native=len(waits)*25,terminal_goal_upper_m=upper,minimum_raw_m=minimum,analytical_native=len(candidate));np.savez_compressed(O/'MODULATION_SOURCE.npz',states=states,controls=controls,requests=candidate);(O/'MODULATION_PACKET.json').write_text(json.dumps(packet)+'\n')
result['wall_s']=time.monotonic()-begun;(O/'MODULATION_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
