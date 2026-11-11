"""Fixed memory-bounded best-first search, with complete stop witnesses."""
import copy,heapq,math,time
import numpy as np
from kernel import Predictor,PARAMETERS,initial,checks,public_setup,ref,REQUIRED,RHO,Expander,Geometry,CAP,TARGETS,predict,stop_witness

def construct(x,config,deadline,progress=lambda x:None):
 packet=x['packet'];source=x['source'];setup=public_setup(x['setup']);goal=np.asarray(x['goal']);ref.snapshot_state(packet,source,packet['body_measured_at']);p=initial(packet);state=np.asarray(p['state']);memory=np.r_[p['last_ctrl'],p['integral']];full=ref._old.Geometry(setup['known'],source['periodic']);a,b=full.clearances(state[None,:3]);minimum=float(min(a[0],b[0]));base=dict(passed=False,models=0,integrations=0,physical_ready=False,source_native_tick=packet['native_tick'],config=config,scope='V1047_MEMORY_BOUNDED_TIME_ROUTE_SOURCE',original_goal=goal.tolist(),required_raw_clearance_m=REQUIRED)
 if minimum<REQUIRED:return dict(base,status='INITIAL_FULL_CYCLE_HOLD_REJECTED')
 geometry=Geometry(setup['known'],source['periodic'],packet['sim_time']);engine=Expander(setup);guide=copy.deepcopy(setup['known']);vertices=source['periodic']['vertices'];anchor=[float((np.asarray(vertices[i])[:,0].min()+np.asarray(vertices[i])[:,0].max())/2)for i in [0,4]];guide['known_circles']=[*guide['known_circles'],[*anchor,.1]];h0,_=ref._old.Geometry(guide,None).heuristic(goal)
 def h(s):a=math.atan2(goal[1]-s[1],goal[0]-s[0])-s[2];return h0(s)+.25*abs(math.atan2(math.sin(a),math.cos(a)))
 def key(s,m,t,last):return(round(s[0]/.04),round(s[1]/.04),round((s[2]%(2*math.pi))*144/(2*math.pi))%144,round(s[6]/(CAP/2)),round(s[7]/.03),round(s[3]/.01),round(m[4]/.02),round((t*.01%geometry.period)/.25),last)
 # Heap stores complete immutable short action trails, no unbounded ancestry.
 width=config['frontier_width'];seq=0;heap=[(config['heuristic_weight']*h(state),0.,seq,state,memory,0,0,())];best={key(state,memory,0,0):0.};expanded=generated=rejected=stop_rejected=dropped=0;closest=float(np.linalg.norm(state[:2]-goal));nearest_actions=();nearest_state=state;started=time.monotonic();tested=[]
 while heap and expanded<config['maximum_expansions']and time.time()<deadline:
  _,cost,_,state,memory,elapsed,last,actions=heapq.heappop(heap)
  if cost>best.get(key(state,memory,elapsed,last),math.inf)+1e-10:continue
  expanded+=1;error=float(np.linalg.norm(state[:2]-goal))
  if error<closest:closest=error;nearest_actions=actions;nearest_state=state.copy()
  if elapsed and error+.08<=.45 and last==1:
   ss,uu,rr,mm=predict(setup,packet,actions);low=geometry.complete(ss);cc,upper=checks(ss,uu,rr,packet,setup,goal,low,REQUIRED);a,b=full.clearances(ss[-1:,:3]);cc['terminal_full_cycle_hold']=float(min(a[0],b[0]))>=REQUIRED;cc['whole_time_horizon']=len(rr)<=40000
   tested.append(dict(checks=cc,goal_upper_m=upper,minimum_raw_m=low))
   if all(cc.values()):return dict(base,passed=True,status='FULL_TIME_INPUT_CANDIDATE',expanded=expanded,wall_s=time.monotonic()-started,actions=actions,state_path=ss.tolist(),planned_body_requests=rr.tolist(),predicted_actuator_controls=uu.tolist(),checks=cc,terminal_goal_upper_m=upper,minimum_timed_raw_m=low,analytical_prediction_steps=len(rr),requires_reverse=any(r['gear']<0 for r in actions))
  if elapsed+200>=40000:continue
  stopped=abs(memory[2:4]).max()<=1e-10 and abs(state[3])<=.003 and abs(state[7])<=.03;gear=1 if memory[2:4].mean()>=0 else-1;gears=([1,-1]if config['allow_reverse']else[1])if stopped else[gear];steps=config['move_ticks'];choices=[('move',TARGETS,steps,np.full(5,.08 if g>0 else-.03),g)for g in gears]+[('wait',np.array([0.]),200,np.array([0.]),last)]
  for kind,targets,n,speeds,direction in choices:
   if elapsed+n+200>40000:continue
   ss,uu,mm=engine.expand(state,memory,targets,n,speeds);ix=np.unique(np.r_[0,np.arange(5,n,5),n]);dense=np.concatenate([np.repeat(state[None,None,:3],len(targets),axis=0),ss[:,:,:3]],axis=1);values=np.asarray([geometry.clearances(q[ix],elapsed+ix,.025)for q in dense]);j=np.arange(n+1);left=ix[np.maximum(0,np.searchsorted(ix,j,side='right')-1)];right=ix[np.minimum(len(ix)-1,np.searchsorted(ix,j,side='left'))];dl=np.linalg.norm(dense[:,:,:2]-dense[:,left,:2],axis=2)+RHO*abs(dense[:,:,2]-dense[:,left,2]);dr=np.linalg.norm(dense[:,:,:2]-dense[:,right,:2],axis=2)+RHO*abs(dense[:,:,2]-dense[:,right,2]);gap=np.minimum(dl,dr).max(axis=1);valid=(values.min(axis=1)-gap>=REQUIRED)&(abs(ss[:,:,3]).max(axis=1)<=.13)&(abs(ss[:,:,4]).max(axis=1)<=.03)&(abs(ss[:,:,5]).max(axis=1)<=.16)
   for k,target in enumerate(targets):
    if not valid[k]:rejected+=1;continue
    child=ss[k,-1];cm=mm[k];t=elapsed+n;nextlast=direction if kind=='move'else last;nc=cost+n*.01*(.08 if kind=='wait'or direction>0 else.03)*(1+.15*abs(target)/CAP)+(0.3 if kind=='move'and last and last!=direction else 0.);marker=key(child,cm,t,nextlast)
    if nc>=best.get(marker,math.inf)-1e-10:continue
    safe,sl=stop_witness(engine,geometry,child,cm,t)
    if not safe:stop_rejected+=1;continue
    action=dict(kind=kind,target=float(target),ticks=n,gear=direction if kind=='move'else 0);trail=actions+(action,);best[marker]=nc;seq+=1;generated+=1;heapq.heappush(heap,(nc+config['heuristic_weight']*h(child),nc,seq,child.copy(),cm.copy(),t,nextlast,trail))
  if len(heap)>4*width:
   count=len(heap);heap=heapq.nsmallest(width,heap);heapq.heapify(heap);dropped+=count-len(heap)
  if len(best)>200000:best={key(row[3],row[4],row[5],row[6]):row[1]for row in heap}
  if expanded%1000==0:progress(dict(expanded=expanded,generated=generated,stop_rejected=stop_rejected,frontier=len(heap),dropped=dropped,closest_goal_m=closest,wall_s=time.monotonic()-started))
 return dict(base,status='WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=config['maximum_expansions']else'FRONTIER_EXHAUSTED',expanded=expanded,generated=generated,rejected_edges=rejected,stop_rejected=stop_rejected,beam_dropped=dropped,best_goal_distance_m=closest,nearest_actions=nearest_actions,nearest_state=nearest_state.tolist(),wall_s=time.monotonic()-started,input_candidate_checks=tested,infeasibility_proved=False)
