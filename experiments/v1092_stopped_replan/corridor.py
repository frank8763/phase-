"""Admit one finite gear episode with full braking, not an entire maneuver."""
import importlib.util,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1]
spec=importlib.util.spec_from_file_location('prior_finite_geometry',R/'experiments/v1090_active_corridor/corridor.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
live=prior.live;planner=prior.planner
def proof(setup,packet,source,requests):
    assert source['source_native_tick']==source['periodic']['source_tick']<=packet['native_tick'],'NONCAUSAL_RECOVERY_SOURCE'
    return prior.proof(setup,packet,source,requests)
def construct(setup,packet,source,output,goal):
    static=planner(output).construct(setup,packet,None,goal,wall_s=30.,max_expansions=20000)
    assert static['passed']and static.get('functional_goal_source'),'NO_COMPLETE_STATIC_TOPOLOGY_FOR_RECOVERY'
    rr=np.asarray(static['planned_body_requests']);moving=np.flatnonzero(abs(rr[:,0])>.005)
    assert len(moving),'NO_MOVING_STATIC_SOURCE'
    start=int(moving[0]);gear=np.sign(rr[start,0]);end=start
    while end<len(rr)and(rr[end,0]==0. or np.sign(rr[end,0])==gear):end+=1
    lengths=sorted(set(min(n,end-start)for n in [2000,1500,1000,500]),reverse=True)
    candidates=[]
    for length in lengths:
        requests=np.vstack([rr[:start+length],np.zeros((2200,3))])
        q,states,controls=proof(setup,packet,source,requests)
        q.update(first_gear=int(gear),prefix_native=length,static_complete_goal_not_executed=True,
                 predicted_motion_m=float(np.linalg.norm(states[-1,:2]-np.asarray(packet['body'][:2]))))
        candidates.append(q)
        if q['passed']and q['predicted_motion_m']>=.05:
            return dict(proof=q,candidates=candidates,requests=requests,states=states,
                        controls=controls,static_actions=static['actions'])
    raise AssertionError(('NO_CERTIFIED_SINGLE_GEAR_STOP_PREFIX',candidates))
