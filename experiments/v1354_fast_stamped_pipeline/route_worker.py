"""Actual bounded mode0 compiled worker; no physical imports or online truth."""
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys
import traceback


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical'}:
            raise AssertionError('PLANNER_PHYSICAL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0,NoPhysical())
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('phase_exact_fast_search',R/'experiments/v1350_bounded_complete_search/planner.py')
fast=importlib.util.module_from_spec(spec);spec.loader.exec_module(fast)
from observed_route import revalidate


def main():
    source,target=map(Path,sys.argv[1:3]);request=json.loads(source.read_text())
    result=dict(passed=False,request_id=request['request_id'],models=0,physical_native=0,
                request_native_tick=request['native_tick'],request_sim_time=request['sim_time'])
    try:
        ball=request['ball'];ball=None if ball is None else (ball[:2],ball[2])
        path,report=fast.propose(request['known'],request['body'],request['goal'],ball,guard=request['guard'],mode=0,maxwall=1.5,maxexpand=22000)
        valid,proof=revalidate(request['known'],path,request['body'],ball,guard=request['guard'])
        result.update(passed=bool(path is not None and valid),path=path.tolist() if path is not None and valid else None,
                      report=report,snapshot_dense_validation=proof)
    except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
    temporary=target.with_suffix('.tmp');temporary.write_text(json.dumps(result,allow_nan=False)+'\n');temporary.replace(target)


if __name__=='__main__':main()
