"""Four fixed causal snapshots and exact undetected route check; zero models."""
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time
import numpy as np

own=Path(__file__).parent;repo=own.parents[1];root=repo/'runs/v820_tracked_norm_global/pre_navigation';root.mkdir(exist_ok=False)
class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,*args):
        if fullname=='mujoco'or fullname.startswith('mujoco.'):
            raise RuntimeError('QUALIFICATION_FORBIDS_MODEL_IMPORT')
sys.meta_path.insert(0,NoPhysics());sys.path.insert(0,str(own));sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from exact_footprint import build
from current_guide import attach,route_world
from planner import search
from independent_soft_reference import dense_path
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dump=lambda n,v:(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/p)==h for p,h in freeze['files'].items())
started=time.time();deadline=min(started+600,read(repo/'RPCCR_TEMPORAL_PROGRESS_AUTHORIZATION_20261105.json')['unique_absolute_deadline_unix'])
window=dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=False,models=0,integrations=0);dump('ROUND_WINDOW.json',window)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('QUALIFICATION_600S')));signal.alarm(max(1,int(deadline-time.time())))
rows=[];status='RUNNING'
def do_search(f,start,goal,w):
    path,stats=search(f,start,goal,w['wheel_base'],w['max_steer'],guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000)
    if stats['status']!='GLOBAL_GOAL_PATH':
        p,s=path,stats
        path,stats=search(f,start,goal,w['wheel_base'],w['max_steer'],guard=.155,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
        if path is None and p is not None:path,stats=p,dict(s)
        stats['preferred_search']=s
    return path,stats
try:
    cell=repo/'runs/v809_time_reference_global/main_slot01/paired/geometry_memory'
    initial=read(cell/'planning_0000.json');w=initial['causal_input'];f=build(F,w);f.base_heuristic=F.base._heuristic_grid;attach(f,dict(center=None))
    p,s=do_search(f,initial['pose'],w['goal'],w)
    assert np.array_equal(p,np.asarray(initial['stats']['forward_curve']['original_path'])),'INITIAL_UNDETECTED_ASTAR_CHANGED'
    dump('INITIAL_STATIC_ROUTE.json',dict(status='EXACT_ORIGINAL_INITIAL_SPATIAL_PATH',models=0,integrations=0))
    for old in read(repo/'runs/v810_forward_reference_global/pre_navigation/RESULTS.json'):
        assert sha(repo/old['input_file'])==old['input_sha256']
        state=old['causal_state'];world,md=route_world(read(repo/old['input_file'])['causal_input'],state)
        f=build(F,world);f.base_heuristic=F.base._heuristic_grid;attach(f,state)
        path,stats=do_search(f,old['start'],old['goal'],world)
        row=dict(step=old['step'],input_file=old['input_file'],input_sha256=old['input_sha256'],causal_state=state,causal_world=world,
            start=old['start'],goal=old['goal'],metadata=md,stats=stats,path=None if path is None else path.tolist())
        if path is not None:
            q=dense_path(path);values=f.reference_values(q,np.zeros(len(q)));heat=f.soft_forecast_cost(q)
            gap=float(np.max(abs(f.reference_values(q,np.full(len(q),6.56))-f.reference_values(q,np.full(len(q),6.560001)))))
            row.update(endpoint_goal_m=float(np.linalg.norm(path[-1,:2]-old['goal'])),
                start_goal_m=float(np.linalg.norm(np.asarray(old['start'])[:2]-old['goal'])),
                reverse_nodes=int(np.sum(path[:,3]<0)),horizon_jump_m=gap)
            np.savez_compressed(root/f'step{row["step"]:04d}.npz',path=path,dense=q,current_values=values,heat=heat)
        rows.append(row);dump('RESULTS.json',rows)
        print(json.dumps(dict(step=row['step'],status=stats['status'],remaining=row.get('endpoint_goal_m'),reverse=row.get('reverse_nodes'),jump=row.get('horizon_jump_m'))),flush=True)
    status='FIXED_SAVED_PROPOSAL_QUALIFICATION_COMPLETE'
except BaseException as exc:
    import traceback
    status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
finally:
    signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
    dump('COMPLETION.json',dict(status=status,records=rows,models=0,integrations=0))
