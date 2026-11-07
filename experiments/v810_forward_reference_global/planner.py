"""Causal point memory, rectangular footprint, forward/reverse Hybrid A*. No simulator access."""
import heapq,math,time
import numpy as np

def wrap(a):return (a+np.pi)%(2*np.pi)-np.pi

class PointMemory:
    def __init__(self,resolution=.06):self.cells={};self.resolution=resolution
    def update(self,points,known_rects,known_circles,step,persist=True):
        points=np.asarray(points,dtype=float).reshape(-1,2)
        unknown=np.ones(len(points),dtype=bool)
        # The workspace boundary is part of the known prior, including noisy returns around it.
        unknown &= np.min(np.abs(np.abs(points)-5.0),axis=1)>.14
        # Filter only returns explained by the known prior map; no hidden obstacle IDs/geometry.
        for x,y,hx,hy in known_rects:
            outside=np.maximum(np.abs(points-[x,y])-[hx,hy],0)
            unknown &= np.linalg.norm(outside,axis=1)>.14
        for x,y,r in known_circles:unknown &= np.abs(np.linalg.norm(points-[x,y],axis=1)-r)>.14
        if not persist:self.cells={}
        for pt in points[unknown]:
            key=tuple(np.rint(pt/self.resolution).astype(int));self.cells[key]=(pt.copy(),int(step))
        return np.asarray([v[0] for v in self.cells.values()],dtype=float).reshape(-1,2)

def spatial_search(field,start,goal,wheel_base,max_steer,guard=.20,budget=7.0,resolution=.10,heading_bins=72,dense_requested_guard=False,work_limit=None):
    start=np.asarray(start,float);goal=np.asarray(goal,float);begin=time.monotonic()
    hard=.15
    if float(field.pose_values([start])[0])<hard-1e-6:return None,{'status':'START_BELOW_HARD_FLOOR','expanded':0}
    required=min(guard,float(field.pose_values([start])[0])-.001);required=max(hard,required)
    cfg=field.config
    field.free=field.clearance>=hard-cfg.resolution/math.sqrt(2)
    guide=field.base_heuristic(field,goal) if hasattr(field,'base_heuristic') else None
    global_goal=goal.copy()
    # Search toward the actual goal. A position-only short local subgoal can
    # accept the wrong heading at a narrow entrance and repeatedly back out.
    def h(p):
        eu=float(np.linalg.norm(p[:2]-goal))
        if guide is None:return eu
        idx=field.indices([p[:2]])[0]
        if (idx>=0).all() and (idx<guide.shape).all() and np.isfinite(guide[tuple(idx)]):return max(eu,float(guide[tuple(idx)]))
        return eu+20.
    def key(p,gear):return (round(p[0]/resolution),round(p[1]/resolution),round((p[2]%(2*np.pi))/(2*np.pi)*heading_bins)%heading_bins,gear)
    poses=[start];parents=[-1];pieces=[None];gears=[1];costs=[0.];best={key(start,1):0.};queue=[(h(start),0.,0)]
    steer=np.linspace(-max_steer,max_steer,7);ds=np.arange(1,7)*.04
    expanded=0;best_id=0;best_h=h(start);goal_id=None
    if work_limit is not None:assert isinstance(work_limit,int) and 0<work_limit<=22000
    expansion_limit=22000 if work_limit is None else work_limit
    while queue and expanded<expansion_limit and (work_limit is not None or time.monotonic()-begin<budget):
        _,cost,i=heapq.heappop(queue);pose=poses[i]
        if cost>best.get(key(pose,gears[i]),float('inf'))+1e-9:continue
        expanded+=1
        distance=float(np.linalg.norm(pose[:2]-goal))
        if distance<.28:goal_id=i;break
        hh=h(pose)
        if hh<best_h-.02:best_h=hh;best_id=i
        all_pieces=[];choices=[]
        for gear in (1,-1):
            for st in steer:
                curvature=math.tan(st)/wheel_base;s=gear*ds
                yaw=pose[2]+s*curvature
                if abs(curvature)>1e-9:
                    xx=pose[0]+(np.sin(yaw)-math.sin(pose[2]))/curvature
                    yy=pose[1]-(np.cos(yaw)-math.cos(pose[2]))/curvature
                else:xx=pose[0]+s*math.cos(pose[2]);yy=pose[1]+s*math.sin(pose[2])
                all_pieces.append(np.column_stack((xx,yy,yaw)));choices.append((gear,st))
        # Match the final certificate BEFORE an edge is admitted to search.
        # The parent-to-first-pose interval must be checked as well.
        pieces_array=np.asarray(all_pieces)
        previous=np.concatenate((np.broadcast_to(pose,(len(choices),1,3)),pieces_array[:,:-1,:]),axis=1)
        difference=pieces_array-previous
        difference[:,:,2]=(difference[:,:,2]+np.pi)%(2*np.pi)-np.pi
        fractions=np.arange(1,6,dtype=float)/5.
        dense=previous[:,:,None,:]+difference[:,:,None,:]*fractions[None,None,:,None]
        vals=field.pose_values(dense.reshape(-1,3)).reshape(len(choices),30)
        for piece,clearance,(gear,st) in zip(all_pieces,vals,choices):
            if np.min(clearance)<required-1e-8:continue
            endpoint=piece[-1].copy();endpoint[2]=wrap(endpoint[2]);k=key(endpoint,gear)
            new=cost+.24*(1.0 if gear==1 else 1.8)+(.65 if gears[i]!=gear else 0.)
            new+=.045*abs(st/max_steer)+.18*max(0.,.30-float(np.min(clearance)))
            if new>=best.get(k,float('inf'))-1e-9:continue
            best[k]=new;j=len(poses);poses.append(endpoint);parents.append(i);pieces.append(piece);gears.append(gear);costs.append(new)
            heapq.heappush(queue,(new+1.45*h(endpoint),new,j))
    selected=goal_id if goal_id is not None else best_id
    if goal_id is None and h(start)-best_h<.5 and np.linalg.norm(poses[selected][:2]-goal)>.45:
        return None,{'status':'NO_MEANINGFUL_GLOBAL_PROGRESS_WITHIN_BUDGET','expanded':expanded,'heuristic_start_m':h(start),'heuristic_best_m':best_h,'wall_s':time.monotonic()-begin}
    if selected==0:return None,{'status':'NO_PROGRESS_PATH','expanded':expanded,'wall_s':time.monotonic()-begin}
    chain=[];i=selected
    while parents[i]>=0:
        chain.append(np.column_stack((pieces[i],np.full(6,gears[i]))));i=parents[i]
    path=np.vstack((np.r_[start,1.],*reversed(chain)))
    # Exact dense validation before any path reaches the controller.
    dense=[]
    for a,b in zip(path[:-1],path[1:]):
        for t in np.linspace(0,1,5,endpoint=False):dense.append([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*wrap(b[2]-a[2])])
    dense.append(path[-1,:3]);minimum=float(np.min(field.pose_values(dense)))
    certificate_floor=required if dense_requested_guard else hard
    if minimum<certificate_floor-1e-8:return None,{'status':'DENSE_CERTIFICATE_REJECTED','clearance_m':minimum,'required_m':certificate_floor,'expanded':expanded}
    return path,{'status':'GLOBAL_GOAL_PATH' if goal_id is not None else 'SAFE_PROGRESS_PREFIX','expanded':expanded,'wall_s':time.monotonic()-begin,'minimum_clearance_m':minimum,'local_goal_distance_m':float(np.linalg.norm(path[-1,:2]-goal)),'goal_distance_m':float(np.linalg.norm(path[-1,:2]-global_goal)),'guard_m':required}


def timed_search(field,start,goal,wheel_base,max_steer,guard=.20,budget=7.0,resolution=.10,heading_bins=72,dense_requested_guard=False,work_limit=None,forward_only=False):
    start=np.asarray(start,float);goal=np.asarray(goal,float);begin=time.monotonic()
    hard=.15
    if float(field.pose_values([start])[0])<hard-1e-6:return None,{'status':'START_BELOW_HARD_FLOOR','expanded':0}
    required=min(guard,float(field.pose_values([start])[0])-.001);required=max(hard,required)
    cfg=field.config
    field.free=field.clearance>=hard-cfg.resolution/math.sqrt(2)
    guide=field.base_heuristic(field,goal) if hasattr(field,'base_heuristic') else None
    global_goal=goal.copy()
    # Search toward the actual goal. A position-only short local subgoal can
    # accept the wrong heading at a narrow entrance and repeatedly back out.
    def h(p):
        eu=float(np.linalg.norm(p[:2]-goal))
        if guide is None:return eu
        idx=field.indices([p[:2]])[0]
        if (idx>=0).all() and (idx<guide.shape).all() and np.isfinite(guide[tuple(idx)]):return max(eu,float(guide[tuple(idx)]))
        return eu+20.
    def key(p,gear,arrival):return (round(p[0]/resolution),round(p[1]/resolution),round((p[2]%(2*np.pi))/(2*np.pi)*heading_bins)%heading_bins,gear,min(17,int(round(arrival/.4))))
    poses=[start];parents=[-1];pieces=[None];gears=[1];costs=[0.];arrivals=[0.];best={key(start,1,0.):0.};queue=[(h(start),0.,0)]
    steer=np.linspace(-max_steer,max_steer,7);ds=np.arange(1,7)*.04
    expanded=0;best_id=0;best_h=h(start);goal_id=None
    if work_limit is not None:assert isinstance(work_limit,int) and 0<work_limit<=22000
    expansion_limit=22000 if work_limit is None else work_limit
    while queue and expanded<expansion_limit and (work_limit is not None or time.monotonic()-begin<budget):
        _,cost,i=heapq.heappop(queue);pose=poses[i]
        if cost>best.get(key(pose,gears[i],arrivals[i]),float('inf'))+1e-9:continue
        expanded+=1
        distance=float(np.linalg.norm(pose[:2]-goal))
        if distance<.28:goal_id=i;break
        hh=h(pose)
        if hh<best_h-.02:best_h=hh;best_id=i
        all_pieces=[];choices=[]
        for gear in ((1,) if forward_only else (1,-1)):
            for st in steer:
                curvature=math.tan(st)/wheel_base;s=gear*ds
                yaw=pose[2]+s*curvature
                if abs(curvature)>1e-9:
                    xx=pose[0]+(np.sin(yaw)-math.sin(pose[2]))/curvature
                    yy=pose[1]-(np.cos(yaw)-math.cos(pose[2]))/curvature
                else:xx=pose[0]+s*math.cos(pose[2]);yy=pose[1]+s*math.sin(pose[2])
                all_pieces.append(np.column_stack((xx,yy,yaw)));choices.append((gear,st))
        # Match the final certificate BEFORE an edge is admitted to search.
        # The parent-to-first-pose interval must be checked as well.
        pieces_array=np.asarray(all_pieces)
        previous=np.concatenate((np.broadcast_to(pose,(len(choices),1,3)),pieces_array[:,:-1,:]),axis=1)
        difference=pieces_array-previous
        difference[:,:,2]=(difference[:,:,2]+np.pi)%(2*np.pi)-np.pi
        fractions=np.arange(1,6,dtype=float)/5.
        dense=previous[:,:,None,:]+difference[:,:,None,:]*fractions[None,None,:,None]
        from timed_reference import REFERENCE_SPEED,SHIFT_TIME
        offsets=(np.arange(6)[:,None]+fractions[None,:])*(.04/REFERENCE_SPEED)
        starts=np.array([arrivals[i]+(SHIFT_TIME if gear!=gears[i]else 0.)for gear,st in choices])
        dense_times=starts[:,None,None]+offsets[None,:,:]
        vals=field.reference_values(dense.reshape(-1,3),dense_times.reshape(-1)).reshape(len(choices),30)
        if any(gear!=gears[i]for gear,st in choices):
            wt=arrivals[i]+np.linspace(0.,SHIFT_TIME,21)
            minimum_wait=float(field.reference_values(np.repeat([pose],21,axis=0),wt).min())
            for j,(gear,st)in enumerate(choices):
                if gear!=gears[i]:vals[j]=np.minimum(vals[j],minimum_wait)
        for piece,clearance,(gear,st) in zip(all_pieces,vals,choices):
            if np.min(clearance)<required-1e-8:continue
            endpoint=piece[-1].copy();endpoint[2]=wrap(endpoint[2]);arrival=arrivals[i]+.24/REFERENCE_SPEED+(SHIFT_TIME if gear!=gears[i]else 0.);k=key(endpoint,gear,arrival)
            new=cost+.24*(1.0 if gear==1 else 1.8)+(.65 if gears[i]!=gear else 0.)
            new+=.045*abs(st/max_steer)+.18*max(0.,.30-float(np.min(clearance)))
            if new>=best.get(k,float('inf'))-1e-9:continue
            best[k]=new;j=len(poses);poses.append(endpoint);parents.append(i);pieces.append(piece);gears.append(gear);costs.append(new);arrivals.append(arrival)
            heapq.heappush(queue,(new+1.45*h(endpoint),new,j))
    selected=goal_id if goal_id is not None else best_id
    if goal_id is None and h(start)-best_h<.5 and np.linalg.norm(poses[selected][:2]-goal)>.45:
        return None,{'status':'NO_MEANINGFUL_GLOBAL_PROGRESS_WITHIN_BUDGET','expanded':expanded,'heuristic_start_m':h(start),'heuristic_best_m':best_h,'wall_s':time.monotonic()-begin}
    if selected==0:return None,{'status':'NO_PROGRESS_PATH','expanded':expanded,'wall_s':time.monotonic()-begin}
    chain=[];times_chain=[];i=selected
    while parents[i]>=0:
        parent=parents[i];wait=SHIFT_TIME if gears[i]!=gears[parent]else 0.
        chain.append(np.column_stack((pieces[i],np.full(6,gears[i]))))
        times_chain.append(arrivals[parent]+wait+np.arange(1,7)*(.04/REFERENCE_SPEED));i=parent
    path=np.vstack((np.r_[start,1.],*reversed(chain)));schedule=np.r_[0.,np.concatenate(list(reversed(times_chain)))]
    from timed_reference import scheduled_samples
    dense,dtimes=scheduled_samples(path,schedule)
    minimum=float(np.min(field.reference_values(dense,dtimes)))
    certificate_floor=required if dense_requested_guard else hard
    if minimum<certificate_floor-1e-8:return None,{'status':'DENSE_TIME_REFERENCE_REJECTED','clearance_m':minimum,'required_m':certificate_floor,'expanded':expanded}
    return path,{'status':'GLOBAL_GOAL_PATH' if goal_id is not None else 'SAFE_PROGRESS_PREFIX','expanded':expanded,'wall_s':time.monotonic()-begin,'minimum_clearance_m':minimum,'local_goal_distance_m':float(np.linalg.norm(path[-1,:2]-goal)),'goal_distance_m':float(np.linalg.norm(path[-1,:2]-global_goal)),'guard_m':required,'reference_arrival_times_s':schedule.tolist(),'temporal_reference_horizon_s':6.56,'uncertified_beyond_horizon_reference_nodes':int(np.sum(schedule>6.56)),'reference_speed_m_s':REFERENCE_SPEED,'reference_not_execution_certificate':True}


def search(field,*args,**kwargs):
    if getattr(field,'temporal_state',None)is None:return spatial_search(field,*args,**kwargs)
    preferred,preferred_stats=timed_search(field,*args,**kwargs,forward_only=True)
    selected=preferred is not None and preferred_stats['status']=='GLOBAL_GOAL_PATH'
    if selected:path,stats=preferred,dict(preferred_stats)
    else:path,stats=timed_search(field,*args,**kwargs)
    stats['forward_reference_preference']={
        'selected_forward_goal_reference':selected,
        'preferred_status':preferred_stats['status'],
        'preferred_expanded':preferred_stats.get('expanded',0),
        'original_bidirectional_fallback_called':not selected,
        'total_expanded':preferred_stats.get('expanded',0)+(0 if selected else stats.get('expanded',0)),
        'actual_reverse_control_and_recovery_unchanged':True,
        'scope':'Reference proposal preference only; all execution safety contracts unchanged.'}
    return path,stats
