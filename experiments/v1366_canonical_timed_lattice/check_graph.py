"""Fixed graph connectivity and model counterfactuals, never navigation scores."""
import json
import os
import numpy as np
from planner import solve,R,C,O


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    target=O/'GRAPH_BOUNDARIES_V2.json';assert not target.exists()
    graph=json.loads((O/'GRAPH_INPUT.json').read_text());far=np.tile([4.7,4.7,.01,.01],(401,1))
    tests=[('static_only_DIAGNOSTIC',None,None,None,far),
           ('empty_DIAGNOSTIC',dict(known_rectangles=[],known_circles=[]),None,None,far),
           ('blocked_start',None,None,None,np.tile([*graph['request']['body'][:2],1.,1.],(401,1)))]
    rows=[]
    for name,known,body,goal,boxes in tests:
        result=solve(graph,known=known,body=body,goal=goal,boxes=boxes);result['name']=name;rows.append(result)
        print(json.dumps({k:v for k,v in result.items() if k!='path'}),flush=True)
    target.write_text(json.dumps(dict(cases=rows,models=0,physical_native=0,diagnostic_only=True),indent=2)+'\n')


if __name__=='__main__':main()
