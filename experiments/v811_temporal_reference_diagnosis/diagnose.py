"""Fixed-input causal contrasts of frozen pure planner; no physical model."""
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time
import numpy as np

own=Path(__file__).parent
repo=own.parents[1]
root=repo/'runs/v811_temporal_reference_diagnosis'
root.mkdir(exist_ok=False)
class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,*args):
        if fullname=='mujoco' or fullname.startswith('mujoco.'):
            raise RuntimeError('ZERO_MODEL_DIAGNOSIS_FORBIDS_MUJOCO')
sys.meta_path.insert(0,NoPhysics())
sys.path.insert(0,str(repo/'experiments/v810_forward_reference_global'))
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from planner import timed_search
from timed_reference import attach,scheduled_samples
from exact_footprint import build
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py')
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
read=lambda p:json.loads(p.read_text())
dump=lambda p,v:p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fixed=read(repo/'runs/v810_forward_reference_global/pre_navigation/RESULTS.json')
assert [x['step']for x in fixed]==[303,363,649,1183]
started=time.time()
deadline=min(started+1200,read(repo/'RPCCR_TEMPORAL_PROGRESS_AUTHORIZATION_20261105.json')['unique_absolute_deadline_unix'])
window=dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=False,models=0,integrations=0)
dump(root/'ROUND_WINDOW.json',window)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('DIAGNOSIS_ABSOLUTE_WALL')))
signal.alarm(max(1,int(deadline-time.time())))
records=[];status='RUNNING'
try:
    for r in fixed:
        assert sha(repo/r['input_file'])==r['input_sha256']
        world=r['causal_world'];state=r['causal_state']
        f=build(F,world);f.base_heuristic=F.base._heuristic_grid
        attach(f,state)
        # One causal intervention: remove future reachability from REFERENCE
        # query only; preserve the entire current causal rectangle and map.
        f.temporal_state=None
        path,stats=timed_search(f,r['start'],r['goal'],world['wheel_base'],world['max_steer'],
            guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000,forward_only=True)
        row=dict(step=r['step'],input_file=r['input_file'],input_sha256=r['input_sha256'],
            old_forward_status=r['stats']['forward_reference_preference']['preferred_status'],
            old_reverse_nodes=r['old_reverse_nodes'],current_only_forward_stats=stats,
            path=None if path is None else path.tolist(),causal_state=state,causal_world=world)
        if path is not None:
            arrival=np.asarray(stats['reference_arrival_times_s']);dense,clock=scheduled_samples(path,arrival)
            current_values=f.reference_values(dense,clock)
            attach(f,state)
            old_time_values=f.reference_values(dense,clock)
            mask=clock<=6.56
            row.update(endpoint_goal_m=float(np.linalg.norm(path[-1,:2]-r['goal'])),
                reverse_nodes=int(np.sum(path[:,3]<0)),minimum_current_geometry_m=float(current_values.min()),
                minimum_original_time_gate_m=float(old_time_values.min()),
                original_timed_rejected_dense_samples=int(np.sum(old_time_values<stats['guard_m']-1e-8)),
                first_original_time_rejection_s=float(clock[np.flatnonzero(old_time_values<stats['guard_m']-1e-8)[0]])if np.any(old_time_values<stats['guard_m']-1e-8)else None,
                reference_is_not_actual_execution_admission=True)
            np.savez_compressed(root/f'step{r["step"]:04d}.npz',path=path,arrivals=arrival,
                dense=dense,times=clock,current_values=current_values,original_timed_values=old_time_values)
        records.append(row);dump(root/'RESULTS.json',records)
        print(json.dumps({k:v for k,v in row.items()if k not in ['path','causal_state','causal_world','current_only_forward_stats']}|dict(new_status=stats['status'],expanded=stats['expanded'])),flush=True)
    status='FIXED_REFERENCE_CAUSAL_CONTRAST_COMPLETE'
except BaseException as e:
    import traceback
    status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
    signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started)
    dump(root/'ROUND_WINDOW.json',window);dump(root/'COMPLETION.json',dict(status=status,records=records,models=0,integrations=0))
