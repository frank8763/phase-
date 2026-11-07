"""Fixed V821 saved-reference diagnosis; MuJoCo imports and all physics forbidden."""
import argparse
import copy
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
import signal
import sys
import time
from pathlib import Path

os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
import numpy as np

repo=Path(__file__).resolve().parents[2]
own=Path(__file__).parent
root=repo/'runs/v823_global_continuation_diagnosis'
root.mkdir(exist_ok=True)
class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('V823_FORBIDS_MODELS_AND_INTEGRATIONS')
sys.meta_path.insert(0,NoPhysics())
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
sys.path.insert(0,str(repo/'experiments/v821_norm_route_development'))
from exact_footprint import build
from current_guide import attach
from planner import search
spec=importlib.util.spec_from_file_location('saved_footprint_F',repo/'current/footprint_map_b70_v513.py')
F=importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
ap=argparse.ArgumentParser()
ap.add_argument('--red-goal-guide',action='store_true')
ap.add_argument('--probes',action='store_true')
a=ap.parse_args()
assert a.red_goal_guide != a.probes
cell=repo/'runs/v821_norm_route_development/main_slot02/paired/geometry_memory'
states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
execution=list(map(json.loads,(cell/'v648_execution.jsonl').read_text().splitlines()))
protocol=read(cell.parent/'STATIC_PROTOCOL.json')
def world_and_pose(step):
    source=cell/f'planning_{step:04d}.json'
    if source.exists():
        data=read(source)
        return copy.deepcopy(data['causal_route_input']),np.asarray(data['pose']),data
    template=read(cell/'planning_0265.json')
    world=copy.deepcopy(template['causal_route_input'])
    world['rectangles']=[*protocol['known_rectangles'],states[step]['current_outer_rectangle']]
    q=np.asarray(execution[step-1]['qpos_full']);yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
    pose=np.r_[q[:2],yaw];world['start']=pose.tolist()
    return world,pose,None
def guide_query(world,pose):
    field=build(F,world)
    field.base_heuristic=F.base._heuristic_grid
    field.free=field.clearance>=.15-field.config.resolution/math.sqrt(2)
    guide=field.base_heuristic(field,np.asarray(world['goal']))
    idx=field.indices([pose[:2]])[0]
    inside=bool((idx>=0).all() and (idx<guide.shape).all())
    value=float(guide[tuple(idx)]) if inside else math.inf
    return dict(goal_guide_finite=bool(math.isfinite(value)),goal_guide_m=value if math.isfinite(value) else None,
                index_inside_grid=inside,grid_resolution_m=field.config.resolution,
                start_exact_footprint_clearance_m=float(field.pose_values([pose])[0]),
                finite_guide_cells=int(np.isfinite(guide).sum())),field
if a.red_goal_guide:
    world,pose,saved=world_and_pose(604)
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('30S_RED_FIXTURE_LIMIT')))
    signal.alarm(30);begin=time.monotonic();query,_=guide_query(world,pose)
    red=dict(status='ORIGINAL_SAVED_GLOBAL_GUIDE_REPRODUCED',step=604,source=str((cell/'planning_0604.json').relative_to(repo)),
             source_sha256=sha(cell/'planning_0604.json'),query=query,elapsed_s=time.monotonic()-begin,
             models=0,integrations=0,scope='Actual frozen global-guide seam; not a full-navigation regression')
    assert not (root/'RED_FIXTURE.json').exists()
    dump(root/'RED_FIXTURE.json',red);print(json.dumps(red),flush=True)
    assert query['goal_guide_finite'],'RED_GLOBAL_REFERENCE_HAS_NO_FINITE_GUIDE_TO_ORIGINAL_GOAL'
    raise SystemExit(0)

assert (root/'RED_FIXTURE.json').exists() and not read(root/'RED_FIXTURE.json')['query']['goal_guide_finite']
assert not (root/'ROUND_WINDOW.json').exists()
started=time.time();deadline=started+600
window=dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=False,models=0,integrations=0,
            fixed_steps=[265,500,564,604],only_original_planner_replays=True,max_replayed_hybrid_search_calls=2)
dump(root/'ROUND_WINDOW.json',window)
signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('V823_600S_FIXED_DIAGNOSIS_LIMIT')))
signal.alarm(600)
rows=[];replays=[];status='RUNNING'
try:
    for step in window['fixed_steps']:
        world,pose,saved=world_and_pose(step)
        current,_=guide_query(world,pose)
        known=copy.deepcopy(world);known['rectangles']=copy.deepcopy(protocol['known_rectangles']);known['circles']=copy.deepcopy(protocol['known_circles'])
        static,_=guide_query(known,pose)
        rows.append(dict(step=step,current_query=current,known_map_only_evaluator_contrast=static,
            actor_removed_contrast_is_not_an_online_admissible_route=True,
            observation_age_s=states[step]['age_s'],observed_this_frame=states[step]['observed_this_frame'],
            current_outer_rectangle=states[step]['current_outer_rectangle'],pose=pose.tolist(),
            saved_plan_status=None if saved is None else saved['stats']['status']))
        dump(root/'GRID_CAUSAL_CONTRASTS.json',rows)
    # Reproduce only the original265 call chain, not a new algorithm or action bank.
    step=265;world,pose,saved=world_and_pose(step)
    field=build(F,world);field.base_heuristic=F.base._heuristic_grid;attach(field,states[step])
    first,stats=search(field,pose,world['goal'],world['wheel_base'],world['max_steer'],guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000)
    replays.append(dict(role='ORIGINAL_PREFERRED4000',stats=stats,path=None if first is None else first.tolist()))
    if stats['status']!='GLOBAL_GOAL_PATH':
        second,stats2=search(field,pose,world['goal'],world['wheel_base'],world['max_steer'],guard=.155,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
        replays.append(dict(role='ORIGINAL_FALLBACK16000',stats=stats2,path=None if second is None else second.tolist()))
        chosen=first if second is None and first is not None else second
    else:chosen=first
    assert chosen is not None
    exact=bool(np.array_equal(chosen,np.asarray(saved['path'])))
    dump(root/'ORIGINAL265_REPLAY.json',dict(exact_saved_path=exact,records=replays,
        remaining_goal_m=float(np.linalg.norm(chosen[-1,:2]-world['goal'])),models=0,integrations=0))
    assert exact,'ORIGINAL_SAVED265_PATH_REPLAY_DIFFERED'
    status='FIXED_ZERO_MODEL_DIAGNOSIS_COMPLETE'
except BaseException as error:
    import traceback
    status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
    signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started)
    dump(root/'ROUND_WINDOW.json',window)
    dump(root/'COMPLETION.json',dict(status=status,grid_records=len(rows),original_search_replay_calls=len(replays),models=0,integrations=0,
        no_new_navigation_or_algorithm=True,no_existing_scientific_source_modified=True))
print(json.dumps(read(root/'COMPLETION.json')))
