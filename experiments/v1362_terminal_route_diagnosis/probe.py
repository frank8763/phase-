"""Finite saved-state diagnostic counterfactuals; all outputs independently checked."""
import ctypes
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sys.path.insert(0,str(R/'experiments/v1361_dynamic_reserve_consistency'))
from observed_route import geometry,revalidate


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    begin=time.monotonic();guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes()
    raw=R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main'
    req=json.loads((raw/'planner_jobs/request03.json').read_text());body=req['body'];known=req['known'];ball=req['ball'];goal=np.array(req['goal'])
    spec=importlib.util.spec_from_file_location('original_pure_planner',R/'experiments/v1358_terminal_contract/planner.py')
    p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
    # Load and declare the original ctypes boundary using its actual public function.
    p.propose(known,body,goal,(ball[:2],ball[2]),mode=1,maxwall=1.5,maxexpand=22000)
    cases=[]
    for occupied in [True,False]:
        rect=np.ascontiguousarray(known['known_rectangles'],dtype=float).reshape(-1,4)
        circles=list(known['known_circles'])+([ball] if occupied else [])
        circles=np.ascontiguousarray(circles,dtype=float).reshape(-1,3)
        start=np.ascontiguousarray([body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]])
        for requested in [.27,.22]:
            for mode in [1,0,2]:
                assert time.monotonic()-begin<280
                output=np.empty((4096,4));stats=np.zeros(8);count=ctypes.c_int()
                wall=time.monotonic()
                code=p._library.plan_route(rect,len(rect),circles,len(circles),start,np.ascontiguousarray(goal),.50,requested,22000,1.5,mode,output,len(output),ctypes.byref(count),stats)
                path=output[:count.value] if code==0 else None
                valid,proof=revalidate(known,path,body,(ball[:2],ball[2]) if occupied else None,guard=.22)
                row=dict(occupied_disk_present=occupied,requested_nominal_margin_m=requested,mode=mode,code=code,
                         wall_s=time.monotonic()-wall,stats=stats.tolist(),path=None if path is None else path.tolist(),live_dense_passed=valid,independent_dense=proof)
                if path is not None:
                    endpoint=path[-1,:2]+.3*np.array([math.cos(path[-1,2]),math.sin(path[-1,2])])
                    row['actual_body_goal_distance_m']=float(np.linalg.norm(endpoint-goal))
                    assert valid,'KERNEL_POSITIVE_WITNESS_FAILS_ORIGINAL22CM_GATE'
                cases.append(row);print(json.dumps({k:v for k,v in row.items() if k!='path'}),flush=True)
    # Same finite body-centered acceptance-region poses, static versus causal.
    terminal=[]
    for radius in [0.,.08,.16,.24,.32]:
        for angle in range(72 if radius else 1):
            center=goal+radius*np.array([math.cos(angle*math.tau/72),math.sin(angle*math.tau/72)])
            for h in range(72):
                yaw=h*math.tau/72;terminal.append([center[0]-.3*math.cos(yaw),center[1]-.3*math.sin(yaw),yaw])
    terminal=np.array(terminal);geometry_rows=[]
    for occupied in [True,False]:
        circles=list(known['known_circles'])+([ball] if occupied else [])
        field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.array(known['known_rectangles']),circles=np.array(circles),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
        values=geometry.pose_values(field,terminal);idx=int(np.argmax(values))
        geometry_rows.append(dict(occupied_disk_present=occupied,sampled_terminal_poses=len(terminal),maximum_sampled_clearance_m=float(values[idx]),
            best_rear_pose=terminal[idx].tolist(),eligible_at27=int((values>=.27).sum()),eligible_at22=int((values>=.22).sum()),finite_sampling_not_impossibility_proof=True))
    result=dict(executed=True,cases=cases,terminal_geometry=geometry_rows,models=0,physical_native=0,
                original_saved_request_sha256=hashlib.sha256((raw/'planner_jobs/request03.json').read_bytes()).hexdigest(),
                compiled_library_sha256=hashlib.sha256(p.LIB.read_bytes()).hexdigest(),wall_s=time.monotonic()-begin,
                review_pending_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,current_pointer_unchanged=(R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer)
    assert result['review_pending_unchanged'] and result['current_pointer_unchanged']
    (O/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(terminal_geometry=geometry_rows,wall_s=result['wall_s'],models=0)))


if __name__=='__main__':main()
