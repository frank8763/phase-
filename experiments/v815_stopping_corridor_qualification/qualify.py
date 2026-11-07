"""Four preregistered causal inputs, zero model construction/integration."""
import argparse,hashlib,importlib.abc,importlib.util,json,signal,sys,time
from pathlib import Path
import numpy as np

own=Path(__file__).parent;repo=own.parents[1]
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('STOPPING_CORRIDOR_QUALIFICATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
for p in ['runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','experiments/v816_stopping_corridor_global']:
    sys.path.insert(0,str(repo/p))
sys.path.insert(0,str(own))
from exact_footprint import build
from stopping_guide import route_world,attach
from planner import search
from independent_soft_reference import dense_path
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
ap=argparse.ArgumentParser();ap.add_argument('--red-original',action='store_true');a=ap.parse_args()
root=repo/'runs/v815_stopping_corridor_qualification'
if a.red_original:
    item=read(repo/'runs/v814_stop_wait_entry_continuation/physical/RESULT.json')['records'][1]
    state=item['searches'][0]['state'];world=read(repo/'runs/v812_soft_global_reference/main_slot01/paired/geometry_memory/planning_0303.json')['causal_input']
    world['rectangles']=[*world['rectangles'][:-1],state['current_outer_rectangle']]
    w,_=route_world(world,state);field=build(F,w);path=np.asarray(item['searches'][0]['path'])
    minimum=float(field.pose_values(dense_path(path)).min())
    print(json.dumps(dict(signal='OLD_CURRENT_ONLY_REFERENCE_ENTERS_NONSTOPPABLE_CORRIDOR',minimum_m=minimum,required_m=.155)),flush=True)
    assert minimum>=.155,'OLD_ROUTE_DOES_NOT_RESERVE_STOPPING_HORIZON_ROOM'
    raise SystemExit
assert not root.exists();root.mkdir()
def dump(n,x):(root/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
started=time.time();deadline=min(started+900,read(repo/'RPCCR_STOPPING_CORRIDOR_AUTHORIZATION_20261105.json')['absolute_deadline_unix'])
window=dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=False,models=0,integrations=0)
dump('ROUND_WINDOW.json',window)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('FIXED_900S_QUALIFICATION')));signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
rows=[];status='RUNNING'
def solve(field,start,goal,world):
    field.base_heuristic=F.base._heuristic_grid
    path,stats=search(field,start,goal,world['wheel_base'],world['max_steer'],guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000)
    if stats['status']!='GLOBAL_GOAL_PATH':
        preferred,ps=path,stats
        path,stats=search(field,start,goal,world['wheel_base'],world['max_steer'],guard=.155,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
        if path is None and preferred is not None:path,stats=preferred,dict(ps)
        stats['preferred_search']=ps
    return path,stats
try:
    cell=repo/'runs/v812_soft_global_reference/main_slot01/paired/geometry_memory'
    initial=read(cell/'planning_0000.json');world=initial['causal_input'];field=build(F,world);attach(field,dict(center=None))
    path,stats=solve(field,initial['pose'],world['goal'],world)
    assert np.array_equal(path,np.asarray(initial['stats']['forward_curve']['original_path'])),'INITIAL_UNDETECTED_PATH_CHANGED'
    dump('INITIAL_ROUTE.json',dict(status='EXACT_V812_INITIAL_ASTAR_PATH',models=0,integrations=0))
    for entry in read(own/'FIXED_INPUTS.json'):
        assert sha(repo/entry['source'])==entry['source_sha256']
        world=entry['world'];state=entry['state'];w,metadata=route_world(world,state);field=build(F,w);attach(field,state)
        path,stats=solve(field,entry['start'],world['goal'],world)
        row=dict(label=entry['label'],source=entry['source'],source_sha256=entry['source_sha256'],state=state,start=entry['start'],world=world,corridor_world=w,
                 metadata=metadata,stats=stats,path=None if path is None else path.tolist(),required_role=entry['required_role'])
        if path is not None:
            dense=dense_path(path);values=field.pose_values(dense);heat=field.soft_forecast_cost(dense)
            np.savez_compressed(root/(entry['label']+'.npz'),path=path,dense=dense,corridor_values=values,soft_heat=heat)
            row.update(endpoint_goal_m=float(np.linalg.norm(path[-1,:2]-world['goal'])),start_goal_m=float(np.linalg.norm(np.asarray(entry['start'])[:2]-world['goal'])),
                       reverse_nodes=int(np.sum(path[:,3]<0)),minimum_corridor_m=float(values.min()))
        rows.append(row);dump('RESULTS.json',rows)
        print(json.dumps(dict(label=row['label'],status=stats['status'],remaining=row.get('endpoint_goal_m'),reverse=row.get('reverse_nodes'),minimum=row.get('minimum_corridor_m'))),flush=True)
    status='FIXED_STOPPING_CORRIDOR_PROPOSALS_COMPLETE'
except BaseException as error:
    import traceback
    status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
    signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
    dump('COMPLETION.json',dict(status=status,records=rows,models=0,integrations=0))
