"""Fixed same-request kernel and full-goal qualification, no physical imports."""
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:
            raise AssertionError('SEARCH_QUALIFICATION_NO_PHYSICAL '+name)


sys.meta_path.insert(0,NoPhysical())
import numpy as np
from planner import propose

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('QUALIFICATION_900S')));signal.alarm(900)
    spec=importlib.util.spec_from_file_location('original_numpy_admission',R/'experiments/v1348_recoverable_tracking/observed_route.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    raw=R/'runs/v858_nav2_verified/v1348/rpp_async_default_dynamic_main';rows=[]
    for index in [1,4,8]:
        req=json.loads((raw/'planner_jobs'/('request%02d.json'%index)).read_text())
        old=json.loads((R/'runs/v1349_planner_latency_qualification'/('SAVED_PROPOSAL%02d.json'%index)).read_text())
        ball=(req['ball'][:2],req['ball'][2])
        for mode in [0,1]:
            path,report=propose(req['known'],req['body'],req['goal'],ball,mode=mode)
            accepted,validation=original.revalidate(req['known'],path,req['body'],ball,guard=.22)
            baseline=np.asarray(old['old_path']);same_shape=path is not None and path.shape==baseline.shape
            error=float(np.max(abs(path-baseline))) if same_shape else None
            row=dict(saved_request=index,report=report,numpy_validation=validation,
                     geometry_passed=accepted,same_shape_as_python=same_shape,path_error=error)
            if path is not None:
                assert accepted,('UNSAFE_PROPOSED_PATH',row)
                yaw=path[-1,2];body=path[-1,:2]+.3*np.array([np.cos(yaw),np.sin(yaw)])
                row['independent_body_goal_distance_m']=float(np.linalg.norm(body-np.asarray(req['goal'])))
                if mode==1 and report['status']=='GLOBAL_GOAL_PATH':assert row['independent_body_goal_distance_m']<.28+1e-8
            rows.append(row)
            (O/('RESULT_%02d_MODE%d.json'%(index,mode))).write_text(json.dumps(dict(request=req,path=None if path is None else path.tolist(),summary=row),indent=2)+'\n')
            print(json.dumps(row),flush=True)
    full=[r for r in rows if r['report']['mode']=='obstacle_guided_body_goal' and r['report']['status']=='GLOBAL_GOAL_PATH']
    result=dict(qualification_executed=True,all_returned_paths_numpy_verified=True,
                full_goal_count=len(full),full_goal_total=3,full_goal_qualified=len(full)==3,
                maximum_kernel_wall_s=max(r['report']['wall_s'] for r in rows),rows=rows,
                models=0,physical_native=0,physical_authorized=False)
    (O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)
    signal.alarm(0)


if __name__=='__main__':main()
