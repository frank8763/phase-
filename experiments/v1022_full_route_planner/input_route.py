"""Complete-goal search in the ORIGINAL controller's analytical input dynamics.

Fast expansion is only a proposal. Complete selected requests are regenerated
by the frozen Python predictor and checked at every predicted native state,
including the complete brake tail, before source qualification can pass.
No partial progress result can be accepted. No model or actuation authority.
"""
import heapq,math,time
import numpy as np
from full_route import ref,REQUIRED,RHO
from whole_input import initial,predict,checks,EDGE_TICKS,public_setup
from fast_predict import Expander
CAP=.42722137342572125
TARGETS=np.linspace(-CAP,CAP,5)
MAX_EXPANSIONS=30000
MAX_EDGES=100
STRIDE=5
# Both boundaries retained; nearest sample is <=25ms away. Dynamic occupied
# set is a full-period union (stationary as a set). Retain the original .08
# term, which also dominates the admitted <=.03 lateral translation bound.
SAMPLE_RESERVE=.5*STRIDE*.01*(.13+RHO*.16+.08)

def construct(packet,source,goal,setup,deadline,scope='post_detection_full_cycle'):
    assert scope in ('post_detection_full_cycle','pre_detection_static'), 'UNKNOWN_CERTIFICATE_SCOPE'
    setup=public_setup(setup)
    if scope=='post_detection_full_cycle':
        ref.snapshot_state(packet,source,packet['body_measured_at']);prior=source['periodic']
    else:
        assert source is None and packet.get('dynamic_discovered') is False,'STATIC_SCOPE_NOT_UNDISCOVERED'
        body=np.asarray(packet['body'],float);enc=packet['steering'];q=np.asarray(enc['position'],float);qd=np.asarray(enc['velocity'],float)
        assert body.shape==(5,)and q.shape==qd.shape==(2,)and np.isfinite(np.r_[body,q,qd]).all(),'INVALID_INITIAL_STATE'
        assert abs(q).max()<=.52+1e-6 and abs(qd).max()<=.03,'UNQUALIFIED_INITIAL_ENCODERS'
        assert enc['native_tick']==packet['native_tick'] and enc['measured_at']==packet['body_measured_at'],'INCOHERENT_INITIAL_ENCODERS'
        assert 0<=packet['body_measured_at']-enc['measured_at']<=.05,'STALE_INITIAL_ENCODERS'
        assert packet['native_tick']==0 and packet['sim_time']==0,'STATIC_SCOPE_T0_ONLY'
        assert max(abs(x)for x in packet['body'][3:])<=.03,'INITIAL_BODY_NOT_STOPPED'
        assert max(abs(x)for x in packet['steering']['velocity'])<=.03,'INITIAL_STEERING_NOT_STOPPED'
        prior=None
    goal=np.asarray(goal,float);assert goal.shape==(2,)and np.isfinite(goal).all()
    known=setup['known'];geometry=ref._old.Geometry(known,prior);origin=initial(packet);state=np.asarray(origin['state']);memory=np.r_[origin['last_ctrl'],origin['integral']]
    a,b=geometry.clearances(state[None,:3]);minimum=float(min(a[0],b[0]));start=time.monotonic()
    base=dict(passed=False,models=0,integrations=0,certificate_scope=scope,original_goal=goal.tolist(),original_goal_radius_m=.45,
        full_goal_route_required=True,partial_progress_never_success=True,required_raw_clearance_m=REQUIRED,
        search_sample_reserve_m=SAMPLE_RESERVE,source_native_tick=source['source_native_tick']if source else None,
        body_native_tick=packet['native_tick'],physical_ready=False,actuation_authority=False)
    if minimum<REQUIRED:return dict(base,status='INITIAL_GEOMETRY_REJECTED',expanded=0)
    heuristic,hproof=geometry.heuristic(goal);engine=Expander(setup)
    def key(s,m):
        return(round(s[0]/.025),round(s[1]/.025),round((s[2]%(2*math.pi))*144/(2*math.pi))%144,
            round(s[6]/(CAP/2)),round(s[7]/.03),round(s[3]/.01),round(m[4]/.02))
    nodes=[(state,memory,-1,None,0,minimum)];best={key(state,memory):0.};heap=[(1.5*heuristic(state),0.,0)]
    expanded=rejected=complete_rejected=0;tested=[];best_goal=float(np.linalg.norm(state[:2]-goal));chosen=None
    sample_indices=np.unique(np.r_[np.arange(STRIDE-1,EDGE_TICKS,STRIDE),EDGE_TICKS-1])
    def targets_to(index):
        result=[]
        while nodes[index][2]!=-1:
            result.append(nodes[index][3]);index=nodes[index][2]
        return list(reversed(result))
    while heap and expanded<MAX_EXPANSIONS and time.time()<deadline:
        _,cost,index=heapq.heappop(heap);state,memory,parent,target,depth,node_min=nodes[index]
        if cost>best.get(key(state,memory),math.inf)+1e-10:continue
        expanded+=1;error=float(np.linalg.norm(state[:2]-goal));best_goal=min(best_goal,error)
        if depth and error+.08<=.45:
            targets=targets_to(index);states,ctrl,requests=predict(setup,packet,targets)
            a,b=geometry.clearances(states[:,:3]);lower=float(np.minimum(a,b).min());cc,upper=checks(states,ctrl,requests,packet,setup,goal,lower,REQUIRED)
            discrepancy=float(abs(states[-201]-state).max());cc['fast_proposal_agrees_with_original']=discrepancy<=1e-10
            tested.append(dict(checks=cc,goal_upper_m=upper,minimum_full_raw_m=lower,edges=len(targets),maximum_endpoint_prediction_error=discrepancy))
            if all(cc.values()):
                chosen=dict(state_path=states.tolist(),path=states[:,:3].tolist(),planned_body_requests=requests.tolist(),predicted_actuator_controls=ctrl.tolist(),
                    edge_targets=targets,checks=cc,terminal_goal_distance_upper_m=upper,minimum_raw_full_cycle_clearance_m=lower,
                    analytical_prediction_steps=len(requests),movement_ticks=len(requests)-200,brake_ticks=200)
                break
            complete_rejected+=1
        if depth>=MAX_EDGES:continue
        states,ctrl,memories=engine.expand(state,memory,TARGETS)
        # Check initial separately, then every <=5 native predicted states.
        samples=states[:,sample_indices,:3];a,b=geometry.clearances(samples.reshape(-1,3));values=np.minimum(a,b).reshape(5,len(sample_indices))
        legal=(values>=REQUIRED+SAMPLE_RESERVE).all(axis=1)&(abs(states[:,:,3]).max(axis=1)<=.13)&(abs(states[:,:,5]).max(axis=1)<=.16)&(abs(states[:,:,4]).max(axis=1)<=.03)
        for j,target in enumerate(TARGETS):
            if not legal[j]:rejected+=1;continue
            child=states[j,-1];cmem=memories[j];next_cost=cost+.1002*(1+.15*abs(target)/CAP)+.02*abs(target-state[6])/CAP
            marker=key(child,cmem)
            if next_cost>=best.get(marker,math.inf)-1e-10:continue
            best[marker]=next_cost;nodes.append((child.copy(),cmem.copy(),index,float(target),depth+1,min(node_min,float(values[j].min())-SAMPLE_RESERVE)))
            heapq.heappush(heap,(next_cost+1.5*heuristic(child),next_cost,len(nodes)-1))
    report=dict(base,expanded=expanded,generated=len(nodes),rejected_edges=rejected,complete_candidates_rejected=complete_rejected,
        best_goal_distance_m=best_goal,wall_s=time.monotonic()-start,max_expansions=MAX_EXPANSIONS,max_edges=MAX_EDGES,
        input_candidate_checks=tested,heuristic=hproof)
    if chosen is None:return dict(report,status='WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=MAX_EXPANSIONS else'NO_COMPLETE_INPUT_ROUTE')
    from certificate import binding
    return dict(report,**chosen,snapshot_binding_sha256=binding(packet,source,setup,goal.tolist(),scope),passed=True,status='COMPLETE_GOAL_INPUT_ROUTE_SOURCE_QUALIFIED',analytical_only=True,global_safety_bound=False)
