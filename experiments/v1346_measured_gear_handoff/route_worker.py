"""Bounded pure-data planning subprocess. No physical model allowed."""
import importlib.abc
import json
from pathlib import Path
import sys
import traceback


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical'}:
            raise AssertionError('PLANNING_WORKER_PHYSICAL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoPhysical())
from observed_route import propose


def main():
    import numpy as np
    request_path,result_path=map(Path,sys.argv[1:3]);request=json.loads(request_path.read_text())
    result=dict(passed=False,request_id=request['request_id'],models=0,physical_native=0)
    try:
        ball=request['ball'];ball=None if ball is None else (np.array(ball[:2]),ball[2])
        path,proof=propose(request['known'],request['body'],request['goal'],ball,guard=request['guard'])
        result.update(passed=path is not None,path=path.tolist() if path is not None else None,report=proof)
    except BaseException as error:result.update(error=repr(error),traceback=traceback.format_exc())
    temporary=result_path.with_suffix('.tmp');temporary.write_text(json.dumps(result,allow_nan=False)+'\n');temporary.replace(result_path)


if __name__=='__main__':main()
