"""Full-cycle safe maneuver to a known-map staging pose, not arrival success."""
import heapq,math,time
import numpy as np
from whole_input import Predictor,PARAMETERS,initial
from fast_predict import Expander
from geometry_model import ref,REQUIRED,RHO
CAP=.42722137342572125;TARGETS=np.linspace(-CAP,CAP,5);MOVE=125;HOLD=200;STRIDE=5;MAX_EXPANSIONS=30000

def original(setup,packet,actions):
 p=Predictor(setup,initial(packet),PARAMETERS);states=[p.state.copy()];controls=[];requests=[]
 for action in [*actions,dict(kind='wait',gear=0,target=0.,ticks=200)]:
  v=.08*action['gear']if action['kind']=='move'else 0.;w=v*math.tan(action['target'])/.6
  for _ in range(action['ticks']):s,u=p.step(v,w,False);states.append(s);controls.append(u);requests.append([v,w,False])
 return np.asarray(states),np.asarray(controls),np.asarray(requests),np.r_[p.adapter.last,p.adapter.integral]

def construct(packet,source,setup,stage,deadline):
 ref.snapshot_state(packet,source,packet['body_measured_at']);origin=initial(packet);state=np.asarray(origin['state']);memory=np.r_[origin['last_ctrl'],origin['integral']];geometry=ref._old.Geometry(setup['known'],source['periodic']);a,b=geometry.clearances(state[None,:3]);minimum=float(min(a[0],b[0]));goal=np.asarray(stage[:2]);engine=Expander(setup);guide,_=geometry.heuristic(goal);begun=time.monotonic();base=dict(passed=False,scope='COMPLETE_FINITE_SAFE_STAGING_PREFIX_NOT_ORIGINAL_GOAL',models=0,integrations=0,physical_ready=False,stage_target=stage)
 if minimum<REQUIRED:return dict(base,status='INITIAL_HOLD_REJECTED')
 def key(s,m,last):return(round(s[0]/.05),round(s[1]/.05),round((s[2]%(2*math.pi))*144/(2*math.pi))%144,round(s[6]/(CAP/2)),round(s[7]/.03),round(s[3]/.01),round(m[4]/.02),last)
 def h(s):d=s[2]-stage[2];return 1.5*guide(s)+.3*abs(math.atan2(math.sin(d),math.cos(d)))
 nodes=[(state,memory,-1,None,0,minimum,0)];best={key(state,memory,0):0.};heap=[(h(state),0.,0)];expanded=rejected=0;nearest=float(np.linalg.norm(state[:2]-goal));tested=0
 def chain(index):
  actions=[]
  while nodes[index][2]!=-1:actions.append(nodes[index][3]);index=nodes[index][2]
  return list(reversed(actions))
 while heap and expanded<MAX_EXPANSIONS and time.time()<deadline:
  _,cost,index=heapq.heappop(heap);state,memory,parent,action,elapsed,lower,last=nodes[index]
  if cost>best.get(key(state,memory,last),math.inf)+1e-10:continue
  expanded+=1;error=float(np.linalg.norm(state[:2]-goal));nearest=min(nearest,error);angle=state[2]-stage[2];angle=abs(math.atan2(math.sin(angle),math.cos(angle)))
  if error<.05 and angle<.05 and abs(state[6])<.01 and abs(state[7])<.01:
   actions=chain(index);ss,uu,rr,mm=original(setup,packet,actions);a,b=geometry.clearances(ss[:,:3]);minimum=float(np.minimum(a,b).min());tested+=1
   if minimum>=REQUIRED and abs(ss[-50:,3:6]).max()<=.03 and abs(ss[-50:,7]).max()<=.03:
    return dict(base,passed=True,status='FULL_CYCLE_STAGING_SOURCE_QUALIFIED',actions=actions,state_path=ss.tolist(),planned_body_requests=rr.tolist(),predicted_actuator_controls=uu.tolist(),memory=mm.tolist(),minimum_full_cycle_raw_m=minimum,expanded=expanded,analytical_prediction_steps=len(rr),terminal_pose=ss[-1,:3].tolist(),wall_s=time.monotonic()-begun)
  if elapsed>=22000:continue
  common=float(memory[2:4].mean());stopped=bool(abs(memory[2:4]).max()<=1e-10 and abs(state[3])<=.003 and abs(state[5])<=.03 and abs(state[7])<=.03);gears=[1,-1]if stopped else[1 if common>=0 else -1]
  choices=[('move',TARGETS,MOVE,np.full(5,.08*g),g)for g in gears]+[('wait',np.array([0.]),HOLD,np.array([0.]),last)]
  for kind,targets,steps,speeds,direction in choices:
   ss,uu,mm=engine.expand(state,memory,targets,steps,speeds);ix=np.unique(np.r_[0,np.arange(STRIDE,steps,STRIDE),steps]);dense=np.concatenate([np.repeat(state[None,None,:3],len(targets),axis=0),ss[:,:,:3]],axis=1);a,b=geometry.clearances(dense[:,ix].reshape(-1,3));values=np.minimum(a,b).reshape(len(targets),len(ix));j=np.arange(steps+1);left=ix[np.maximum(0,np.searchsorted(ix,j,side='right')-1)];right=ix[np.minimum(len(ix)-1,np.searchsorted(ix,j,side='left'))];dl=np.linalg.norm(dense[:,:,:2]-dense[:,left,:2],axis=2)+RHO*abs(dense[:,:,2]-dense[:,left,2]);dr=np.linalg.norm(dense[:,:,:2]-dense[:,right,:2],axis=2)+RHO*abs(dense[:,:,2]-dense[:,right,2]);gap=np.minimum(dl,dr).max(axis=1)
   valid=(values.min(axis=1)-gap>=REQUIRED)&(abs(ss[:,:,3]).max(axis=1)<=.13)&(abs(ss[:,:,5]).max(axis=1)<=.16)&(abs(ss[:,:,4]).max(axis=1)<=.03)
   for i,target in enumerate(targets):
    if not valid[i]:rejected+=1;continue
    child=ss[i,-1];cm=mm[i];nextlast=direction if kind=='move'else last;nc=cost+steps*.01*.08*(1.3 if kind=='move'and direction<0 else 1.)+.015*abs(target)/CAP+(.1 if last and kind=='move'and last!=direction else 0.);marker=key(child,cm,nextlast)
    if nc>=best.get(marker,math.inf)-1e-10:continue
    best[marker]=nc;nodes.append((child.copy(),cm.copy(),index,dict(kind=kind,target=float(target),ticks=steps,gear=direction if kind=='move'else 0),elapsed+steps,min(lower,float(values[i].min())-gap[i]),nextlast));heapq.heappush(heap,(nc+h(child),nc,len(nodes)-1))
 return dict(base,status='WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=MAX_EXPANSIONS else'NO_STAGING_ROUTE',expanded=expanded,generated=len(nodes),rejected_edges=rejected,best_stage_distance_m=nearest,complete_candidates_checked=tested,wall_s=time.monotonic()-begun)
