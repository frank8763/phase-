"""Four fixed causal counterfactual searches, no physical models or integrations."""
import importlib.abc
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time
import traceback


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('CAUSAL_REFERENCE_QUERIES_FORBID_MODELS')


sys.meta_path.insert(0,NoModels())
import numpy as np
REPO=Path(__file__).resolve().parents[2];W=REPO/'experiments/v842_staged_long_navigation';OUT=REPO/'runs/v847_gpu_reference_diagnosis/references';CELL=REPO/'runs/v842_staged_long_navigation/v843_main_slot02/paired/geometry_memory'
sys.path.insert(0,str(REPO/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'));sys.path.insert(0,str(W))
from exact_footprint import build,pose_values
from current_guide import attach
from planner import spatial_search
from independent_soft_reference import dense_path


def dump(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2,allow_nan=False,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item())+'\n')


def main():
    import hashlib
    freeze=json.loads((Path(__file__).parent/'REFERENCE_FREEZE.json').read_text())
    assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
    OUT.mkdir(exist_ok=False)
    started=time.time();deadline=min(started+720.,1794009600.);rows=[]
    dump('CLAIM.json',dict(started_unix=started,absolute_deadline_unix=deadline,attempts=1,models=0,integrations=0))
    spec=importlib.util.spec_from_file_location('original_F',REPO/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
    selected={374,683,893,1198};states={}
    with(CELL/'motion_estimate.jsonl').open()as stream:
        for line in stream:
            d=json.loads(line)
            if d['step']in selected:states[d['step']]=d
    for step in sorted(selected):
        row=dict(step=step,models=0,integrations=0)
        alarm=min(180.,deadline-time.time());assert alarm>0
        signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FIXED_SEARCH_180S_LIMIT')))
        signal.setitimer(signal.ITIMER_REAL,alarm)
        try:
            before=time.perf_counter();old=json.loads((CELL/f'planning_{step:04d}.json').read_text());world=old['causal_route_input'];state=states[step]
            f=build(F,world);f.guard=.15;f.base_heuristic=F.base._heuristic_grid;attach(f,state)
            guard=old['stats']['guard_m'];fine='preferred_search'in old['stats']
            path,stats=spatial_search(f,old['pose'],world['goal'],world['wheel_base'],world['max_steer'],
                guard=guard,budget=8. if fine else 2.,resolution=.05 if fine else .10,
                heading_bins=144 if fine else 72,dense_requested_guard=True,work_limit=16000 if fine else 4000,
                forward_only=False)
            row.update(old_status=old['stats']['status'],counterfactual_status=stats['status'],stats=stats,
                path=None if path is None else path.tolist(),query_elapsed_s=time.perf_counter()-before,
                original_forward_selected=old['stats']['spatial_soft_reference']['forward_reference_selected'])
            if path is not None:
                dense=dense_path(path);minimum=float(pose_values(f,dense).min());distance=float(np.linalg.norm(path[-1,:2]-world['goal']))
                row.update(minimum_current_clearance_m=minimum,endpoint_goal_m=distance,
                    reverse_nodes=int(np.sum(path[:,3]<0)),
                    complete_reference_independently_qualified=stats['status']=='GLOBAL_GOAL_PATH'and minimum>=guard-1e-8 and distance<=.28)
                np.savez_compressed(OUT/f'step{step:04d}.npz',path=path,dense=dense,current_values=pose_values(f,dense))
            else:row['complete_reference_independently_qualified']=False
        except BaseException as error:
            row.update(error=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()),complete_reference_independently_qualified=False)
        finally:signal.setitimer(signal.ITIMER_REAL,0)
        rows.append(row);dump('RESULTS.json',rows)
        print(json.dumps({k:v for k,v in row.items()if k not in ['path','stats']}),flush=True)
    dump('COMPLETION.json',dict(status='FOUR_CAUSAL_COUNTERFACTUAL_QUERIES_COMPLETE',records=rows,
        complete_references=sum(x['complete_reference_independently_qualified']for x in rows),
        models=0,integrations=0,navigation=0,training=0,elapsed_s=time.time()-started))


if __name__=='__main__':main()
