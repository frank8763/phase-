"""Fixed saved causal requests at a reduced nominal curvature, zero models."""
import json
import math
import os
from pathlib import Path
import sys
import time
from diagnose import field, rear, geometry, R, C, O
import numpy as np
sys.path.insert(0,str(R/'experiments/v855_renewal_worker'))
from task_planner import search
from types import MethodType


def main():
    index=int(sys.argv[1]); os.sched_setaffinity(0,{3+index%3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    p=R/'runs/v858_nav2_verified/v1347/rpp_async_default_dynamic_main/planner_jobs'/('request%02d.json'%index)
    request=json.loads(p.read_text());f=field(request['known'])
    f.circles=np.vstack([f.circles,request['ball']]);f.pose_values=MethodType(geometry.pose_values,f)
    f.config.resolution=.05;f.clearance=np.ones((201,201))
    body=np.asarray([request['body']]);start=rear(body)[0];goal=np.asarray(request['goal'])-[.3,0.]
    path,proof=search(f,start,goal,.6,math.atan(.6*.5),guard=.27,budget=15.,dense_requested_guard=True)
    result=dict(saved_request=index,nominal_curvature_maximum=.5,path=None if path is None else path.tolist(),report=proof,models=0,physical_native=0)
    (O/('CURVATURE_PROBE%02d.json'%index)).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='path'}))


if __name__=='__main__':main()
