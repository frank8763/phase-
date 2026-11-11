"""Bounded signed-input search with conservative cached interval occupancy."""
import heapq,math,time,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
# Import own dynamics before geometry modules can prepend legacy import paths.
from whole_input import Predictor,PARAMETERS,initial,public_setup,checks
from fast_predict import Expander
from time_geometry import interval_support
from geometry_model import ref,REQUIRED,RHO
NORMALS=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
CAP=.42722137342572125;TARGETS=np.linspace(-CAP,CAP,5);MOVE=125;HOLD=200;STRIDE=5;MAX_EXPANSIONS=120000;MAX_TICKS=40000
class Geometry:
 def __init__(self,known,prior,start):
  self.static=ref._old.Geometry(known,None);self.prior=prior;self.start=start;self.period=2*math.pi/.32;self.bin=.025
  edges=np.arange(0,self.period,self.bin);self.edges=edges
  self.support=interval_support(prior['vertices'],edges-.075,edges+self.bin+.075)
 def clearances(self,poses,ticks,half_s=.025):
  assert half_s<=.025+1e-12
  t=(self.start+np.asarray(ticks)*.01)%self.period;indices=np.minimum((t/self.bin).astype(int),len(self.edges)-1);b=self.support[indices]
  p=np.asarray(poses);c=np.cos(p[:,2]);s=np.sin(p[:,2]);front=np.c_[c,s];left=np.c_[-s,c];low=p[:,:2]@NORMALS.T-.44*abs(front@NORMALS.T)-.375*abs(left@NORMALS.T)
  dynamic=(low-b-.1).max(axis=1);static=self.static.clearances(p)[0];return np.minimum(static,dynamic)
 def complete(self,states):
  lowest=math.inf
  for start in range(0,len(states),2048):q=states[start:start+2048];lowest=min(lowest,float(self.clearances(q[:,:3],np.arange(start,start+len(q)),.005).min()))
  return lowest

def predict(setup,packet,actions):
 p=Predictor(setup,initial(packet),PARAMETERS);states=[p.state.copy()];ctrl=[];requests=[]
 for action in [*actions,dict(kind='wait',target=0.,ticks=200,gear=0)]:
  v=(.08 if action['gear']>0 else-.03)if action['kind']=='move'else 0.;w=v*math.tan(action['target'])/.6
  for _ in range(action['ticks']):s,u=p.step(v,w,False);states.append(s);ctrl.append(u);requests.append([v,w,False])
 return np.asarray(states),np.asarray(ctrl),np.asarray(requests,float)

def construct(packet,source,goal,setup,deadline):
 setup=public_setup(setup);ref.snapshot_state(packet,source,packet['body_measured_at']);goal=np.asarray(goal,float);origin=initial(packet);state=np.asarray(origin['state']);memory=np.r_[origin['last_ctrl'],origin['integral']];full=ref._old.Geometry(setup['known'],source['periodic']);a,b=full.clearances(state[None,:3]);initial_lower=float(min(a[0],b[0]));base=dict(passed=False,models=0,integrations=0,physical_ready=False,actuation_authority=False,reverse_physical_response_qualified=False,scope='RECOVERY_SEEDED_ORIGINAL_TIMED_FULL_GOAL_SOURCE_ONLY',original_goal=goal.tolist(),required_raw_clearance_m=REQUIRED,planned_start_native_tick=packet['native_tick'],start_window_ticks=5,initial_hold_lower_m=initial_lower)
 if initial_lower<REQUIRED:return dict(base,status='INITIAL_HOLD_REJECTED')
 geometry=Geometry(setup['known'],source['periodic'],packet['sim_time']);guide=__import__('copy').deepcopy(setup['known']);vertices=source['periodic']['vertices'];anchor=[float((np.asarray(vertices[i])[:,0].min()+np.asarray(vertices[i])[:,0].max())/2)for i in [0,4]];guide['known_circles']=[*guide['known_circles'],[*anchor,.1]];raw_h,_=ref._old.Geometry(guide,None).heuristic(goal)
 def heuristic(s):
  angle=math.atan2(goal[1]-s[1],goal[0]-s[0])-s[2];return raw_h(s)+.25*abs(math.atan2(math.sin(angle),math.cos(angle)))
 engine=Expander(setup)
 def key(s,m,t,last):return(round(s[0]/.05),round(s[1]/.05),round((s[2]%(2*math.pi))*144/(2*math.pi))%144,round(s[6]/(CAP/2)),round(s[7]/.03),round(s[3]/.01),round(m[4]/.02),round((t*.01%geometry.period)/.5),last)
 nodes=[(state,memory,-1,None,0,initial_lower,0)];best={key(state,memory,0,0):0.};heap=[];expanded=rejected=0;best_goal=float(np.linalg.norm(state[:2]-goal));begun=time.monotonic();tested=[];nearest=None
 # The direct-root temporal search is permanently recorded as WORK_CAP.
 # This finite repair uses exactly five original-.03 reverse proposals, each followed
 # by the original full200 stop. Only complete safe seeds enter the frontier.
 # Their predicted clock/state stay inside ONE original-source plan; they are
 # never represented as fresh actual measurements or executed on their own.
 seed_audits=[]
 for target in TARGETS:
  p=Predictor(setup,origin,PARAMETERS);path=[p.state.copy()];u=[];mid_state=None;mid_memory=None
  for j in range(2200):
   v=-.03 if j<2000 else 0.;w=v*math.tan(target)/.6 if j<2000 else 0.;q,command=p.step(v,w,False);path.append(q);u.append(command)
   if j==1999:mid_state=q.copy();mid_memory=np.r_[p.adapter.last,p.adapter.integral]
  path=np.asarray(path);a,b=full.clearances(path[:,:3]);minimum=float(np.minimum(a,b).min());tail_stopped=bool(abs(path[-50:,3:6]).max()<=.03 and abs(path[-50:,7]).max()<=.03)
  passed=minimum>=REQUIRED and tail_stopped and abs(path[:,3]).max()<=.13 and abs(path[:,5]).max()<=.16 and abs(path[:,4]).max()<=.03
  seed_audits.append(dict(target=float(target),passed=bool(passed),minimum_full_cycle_raw_m=minimum,full_200_stop=tail_stopped,native_prediction_steps=2200))
  if not passed:continue
  mid_index=len(nodes);nodes.append((mid_state,mid_memory,0,dict(kind='move',target=float(target),ticks=2000,gear=-1),2000,minimum,-1))
  stop=p.state.copy();stop_memory=np.r_[p.adapter.last,p.adapter.integral];index=len(nodes);nodes.append((stop,stop_memory,mid_index,dict(kind='wait',target=0.,ticks=200,gear=0),2200,minimum,-1));cost=1.36+.15*abs(float(target))/CAP;best[key(stop,stop_memory,2200,-1)]=cost;heapq.heappush(heap,(cost+1.5*heuristic(stop),cost,index))
 base['recovery_seed_audits']=seed_audits;base['fixed_recovery_candidates']=5;base['seed_scope']='fixed -.03 2000+200 original-source analytic prefix, reverse physical qualification missing'
 if not heap:return dict(base,status='NO_SAFE_RECOVERY_SEED')
 def chain(index):
  out=[]
  while nodes[index][2]!=-1:out.append(nodes[index][3]);index=nodes[index][2]
  return list(reversed(out))
 while heap and expanded<MAX_EXPANSIONS and time.time()<deadline:
  _,cost,index=heapq.heappop(heap);state,memory,parent,action,elapsed,lower,last=nodes[index]
  if cost>best.get(key(state,memory,elapsed,last),math.inf)+1e-10:continue
  expanded+=1;error=float(np.linalg.norm(state[:2]-goal))
  if error<best_goal:best_goal=error;nearest=index
  if elapsed and error+.08<=.45 and last==1:
   actions=chain(index);ss,uu,rr=predict(setup,packet,actions);minimum=geometry.complete(ss);cc,upper=checks(ss,uu,rr,packet,setup,goal,minimum,REQUIRED);a,b=full.clearances(ss[-1:,:3]);cc['terminal_full_cycle_hold']=float(min(a[0],b[0]))>=REQUIRED
   cc['all_gear_changes_have_200_stop']=all(j>0 and actions[j-1]['kind']=='wait'and actions[j-1]['ticks']==200 for j,x in enumerate(actions)if x['kind']=='move'and j>0 and x['gear']!=next((a['gear']for a in reversed(actions[:j])if a['kind']=='move'),x['gear']))
   tested.append(dict(checks=cc,goal_upper_m=upper,minimum_raw_m=minimum))
   if all(cc.values()):return dict(base,passed=True,status='FULL_SIGNED_TIMED_SOURCE_QUALIFIED',expanded=expanded,wall_s=time.monotonic()-begun,actions=actions,state_path=ss.tolist(),planned_body_requests=rr.tolist(),predicted_actuator_controls=uu.tolist(),checks=cc,terminal_goal_upper_m=upper,minimum_timed_raw_m=minimum,analytical_prediction_steps=len(rr),reverse_actions=sum(x['gear']<0 for x in actions),wait_actions=sum(x['kind']=='wait'for x in actions))
  if elapsed+HOLD>MAX_TICKS:continue
  common=float(memory[2:4].mean());stopped=bool(abs(memory[2:4]).max()<=1e-10 and abs(state[3])<=.003 and abs(state[5])<=.03 and abs(state[7])<=.03)
  gears=[1]
  choices=[('move',TARGETS,MOVE,np.full(5,.08*g),g)for g in gears]+[('wait',np.array([0.]),HOLD,np.array([0.]),last)]
  for kind,targets,steps,speeds,direction in choices:
   if elapsed+steps>MAX_TICKS:continue
   ss,uu,mm=engine.expand(state,memory,targets,steps,speeds);ix=np.unique(np.r_[0,np.arange(STRIDE,steps,STRIDE),steps]);dense=np.concatenate([np.repeat(state[None,None,:3],len(targets),axis=0),ss[:,:,:3]],axis=1);poses=dense[:,ix]
   values=np.asarray([geometry.clearances(p,elapsed+ix)for p in poses]);j=np.arange(steps+1);left=ix[np.maximum(0,np.searchsorted(ix,j,side='right')-1)];right=ix[np.minimum(len(ix)-1,np.searchsorted(ix,j,side='left'))];dl=np.linalg.norm(dense[:,:,:2]-dense[:,left,:2],axis=2)+RHO*abs(dense[:,:,2]-dense[:,left,2]);dr=np.linalg.norm(dense[:,:,:2]-dense[:,right,:2],axis=2)+RHO*abs(dense[:,:,2]-dense[:,right,2]);gap=np.minimum(dl,dr).max(axis=1)
   valid=(values.min(axis=1)-gap>=REQUIRED)&(abs(ss[:,:,3]).max(axis=1)<=.13)&(abs(ss[:,:,5]).max(axis=1)<=.16)&(abs(ss[:,:,4]).max(axis=1)<=.03)
   for i,target in enumerate(targets):
    if not valid[i]:rejected+=1;continue
    child=ss[i,-1];cm=mm[i];t=elapsed+steps;nextlast=direction if kind=='move'else last;nc=cost+steps*.01*.08*(2. if kind=='move'and direction<0 else 1.)*(1+.15*abs(target)/CAP)+(.3 if kind=='move'and last and direction!=last else 0.);marker=key(child,cm,t,nextlast)
    if nc>=best.get(marker,math.inf)-1e-10:continue
    best[marker]=nc;nodes.append((child.copy(),cm.copy(),index,dict(kind=kind,target=float(target),ticks=steps,gear=direction if kind=='move'else 0),t,min(lower,float(values[i].min())-gap[i]),nextlast));heapq.heappush(heap,(nc+1.5*heuristic(child),nc,len(nodes)-1))
 return dict(base,status='WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=MAX_EXPANSIONS else'NO_FULL_SIGNED_TIMED_ROUTE',expanded=expanded,generated=len(nodes),rejected_edges=rejected,best_goal_distance_m=best_goal,wall_s=time.monotonic()-begun,input_candidate_checks=tested,nearest_candidate_actions=[]if nearest is None else chain(nearest),nearest_candidate_state=[]if nearest is None else nodes[nearest][0].tolist())
