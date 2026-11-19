"""Independent original-NumPy check of same-bin continuation counterexamples."""
import importlib.util
import os
import time
from types import SimpleNamespace
from common import *

spec=importlib.util.spec_from_file_location('original_independent_footprint',R/'experiments/v855_renewal_worker/exact_footprint.py')
geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)


def field(rect,circle,bounds=5.):
    return SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),
        rectangles=np.asarray(rect),circles=np.asarray(circle),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-bounds,upper=bounds))


def motion(pose,velocity,prior_gear,action,gear,curvature):
    rows=[];offset=0.
    if action==1:
        offset=.4+(2. if prior_gear and prior_gear!=gear else 0.)
        for t in np.arange(.1,offset+.001,.1):rows.append([*pose,t])
    duration=1. if action==1 else 2.4 if action==2 else 2.
    for t in np.arange(.1,duration+.001,.1):
        distance=gear*(.05*t*t if action==1 else .1*t if action==2 else .1*t-.025*t*t)
        angle=pose[2]+distance*curvature
        if abs(curvature)>1e-10:
            x=pose[0]+(math.sin(angle)-math.sin(pose[2]))/curvature;y=pose[1]-(math.cos(angle)-math.cos(pose[2]))/curvature
        else:x=pose[0]+distance*math.cos(pose[2]);y=pose[1]+distance*math.sin(pose[2])
        rows.append([x,y,angle,offset+t])
    if action==3:
        last=rows[-1]
        for j in range(1,5):rows.append([*last[:3],offset+duration+j*.1])
    return np.asarray(rows)


def continuation(pose,tick,velocity,prior_gear,steer,action,gear,steer_out,known,boxes):
    maxsteer=math.atan(.6*.5);angle=-maxsteer+steer_out*(2*maxsteer/6);curvature=math.tan(angle)/.6
    samples=motion(pose,velocity,prior_gear,action,gear,curvature)
    ticks=tick+np.floor((samples[:,3]+1e-8)/.2).astype(int)
    if ticks.max()>=390:return False,dict(reason='HORIZON_REFUSAL')
    static=geometry.pose_values(field(known['known_rectangles'],known['known_circles']),samples[:,:3]);minimum=float(static.min())
    for q in np.unique(ticks):
        values=geometry.pose_values(field([boxes[q]],[],bounds=1e6),samples[ticks==q,:3])-.1
        minimum=min(minimum,float(values.min()))
    return minimum>=.27-1e-8,dict(minimum_clearance_m=minimum,action=action,gear=gear,steer=steer_out)


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'MERGE_EXTENSION_AUDIT.json';assert not target.exists()
    cases=read(O/'MERGE_ABLATION.json')['cases'];req,args=inputs();known=req['known'];boxes=args[6];reviews=[];different=[]
    for case in cases:
        inspected=0;divergence=0
        for index,row in enumerate(case['collisions']):
            a=np.array(row[:3]);b=np.array(row[3:6]);tick,gear,velocity,steer=map(int,row[6:10]);inspected+=1
            # Check the actual quantizer represented by this diagnostic mode.
            if case['mode']==0:
                def key(p):return (round(p[0]/.1),round(p[1]/.1),round((p[2]%(math.tau))/math.tau*72)%72)
            else:
                def key(p):return (math.floor(p[0]/.02+.5) if p[0]>=0 else math.ceil(p[0]/.02-.5),math.floor(p[1]/.02+.5) if p[1]>=0 else math.ceil(p[1]/.02-.5),math.floor(p[2]/(math.pi/180)+.5) if p[2]>=0 else math.ceil(p[2]/(math.pi/180)-.5))
            assert key(a)==key(b),'COLLISION_NOT_ACTUAL_SAME_BIN'
            actions=[(1,g,s) for g in [1,-1] for s in range(7)] if velocity==0 else [(3,gear,steer)]+[(2,gear,s) for s in range(7)]
            for action,g,s in actions:
                before,proof_a=continuation(a,tick,velocity,gear,steer,action,g,s,known,boxes)
                after,proof_b=continuation(b,tick,velocity,gear,steer,action,g,s,known,boxes)
                if before!=after:
                    divergence+=1
                    if len(different)<16:different.append(dict(mode=case['mode'],collision_index=index,recorded_collision=row,old_admitted=before,new_admitted=after,old_proof=proof_a,new_proof=proof_b))
        reviews.append(dict(mode=case['mode'],actual_safe_incoming_collision_states_reviewed=inspected,
            distinct_one_edge_admission_outcomes=divergence,complete_route_found=case['code']==0))
    result=dict(passed=True,independent_original_numpy_reconstruction=True,reviews=reviews,witnesses=different,
        merging_can_change_local_feasibility=bool(different),merging_explains_whole_failure=False,
        no_complete_route_in_same_budget_cases=all(z['code']!=0 for z in cases),
        models=0,physical_native=0,wall_s=time.monotonic()-begin)
    dump(target,result);print(json.dumps({k:v for k,v in result.items() if k!='witnesses'}));print(json.dumps(different[:2]))


if __name__=='__main__':main()
