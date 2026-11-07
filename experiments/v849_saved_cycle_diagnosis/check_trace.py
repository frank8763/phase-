"""Read-only V848 trace feedback: reproduce non-arrival without any physical model."""
import argparse
import importlib.abc
import json
from pathlib import Path
import sys


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('SAVED_CYCLE_DIAGNOSIS_FORBIDS_MODELS')


sys.meta_path.insert(0,NoModels())
import numpy as np
R=Path(__file__).resolve().parents[2]
CELL=R/'runs/v848_goal_first_worker/v848_main_slot01/paired/geometry_memory'


def main():
    p=argparse.ArgumentParser();p.add_argument('--assert-arrival',action='store_true');a=p.parse_args()
    result=json.loads((CELL/'result.json').read_text());protocol=json.loads((CELL.parent/'STATIC_PROTOCOL.json').read_text())
    rows=[json.loads(s)for s in(CELL/'v648_execution.jsonl').open()]
    xy=np.asarray([x['qpos_full'][:2]for x in rows]);distance=np.linalg.norm(xy-protocol['goal_xy'],axis=1)
    print(json.dumps(dict(outcome=result['outcome'],strict_arrival=result['strict_safe_arrival'],
         final_goal_m=float(distance[-1]),last300_sampled_travel_m=float(np.linalg.norm(np.diff(xy[-300:],axis=0),axis=1).sum()),
         last300_net_goal_progress_m=float(distance[-300]-distance[-1]),models=0,integrations=0)),flush=True)
    if a.assert_arrival:assert result['strict_safe_arrival']and distance[-1]<=.45,'SAVED_EPISODE_NON_ARRIVAL_WITH_REPEATED_MOTION'


if __name__=='__main__':main()
