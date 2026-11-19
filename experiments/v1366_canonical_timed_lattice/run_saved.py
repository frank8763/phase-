"""Single fixed original terminal graph search; no vehicle initialization."""
import json
import os
from pathlib import Path
import time
from planner import solve,R,C,O


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    target=O/'MAIN_RESULT.json';assert not target.exists()
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes()
    graph=json.loads((O/'GRAPH_INPUT.json').read_text());result=solve(graph)
    result.update(scope='original saved15105 terminal only; no new navigation',review_pending_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,current_pointer_unchanged=(R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer)
    assert result['review_pending_unchanged'] and result['current_pointer_unchanged']
    target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='path'}))


if __name__=='__main__':main()
