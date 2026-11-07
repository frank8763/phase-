"""Two fixed original rejected brake-only contracts; no models/integrations."""
import argparse,hashlib,importlib.abc,importlib.util,json,signal,sys,time
from pathlib import Path
import numpy as np
own=Path(__file__).parent;repo=own.parents[1]
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('NORM_QUALIFICATION_FORBIDS_MODEL_IMPORT')
sys.meta_path.insert(0,NoModels())
for p in ['runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','experiments/v812_soft_global_reference']:
    sys.path.insert(0,str(repo/p))
sys.path.insert(0,str(own))
from exact_footprint import build
from motion_tracker import install_time_gate
from norm_gate import refine,radial_values
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--red-old-brake',action='store_true');a=ap.parse_args()
cell=repo/'runs/v812_soft_global_reference/main_slot01/paired/geometry_memory';protocol=read(cell.parent/'STATIC_PROTOCOL.json')
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
base_world=read(cell/'planning_0303.json')['causal_input'];entries=read(own/'FIXED_INPUTS.json')
def field(state):
    f=build(F,base_world);install_time_gate(f,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);return f
if a.red_old_brake:
    entry=entries[0];z=np.load(repo/entry['witness_file']);p=z['poses'];values=field(entry['state']).trajectory_values(p,.01)
    print(json.dumps(dict(signal='OLD_COURSE_BRAKE_REJECTED_UNDER_WIDER_AXIS_BOUND',step=entry['step'],full_minimum_m=float(values.min()),gate=.155)),flush=True)
    assert values.min()>=.155,'DECLARED_COURSE_BRAKE_REJECTED_BY_ORIGINAL_BROAD_TRACKED_TUBE'
    raise SystemExit
root=repo/'runs/v817_tracked_norm_qualification';root.mkdir(exist_ok=False)
def dump(n,x):(root/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
started=time.time();deadline=min(started+600,read(repo/'RPCCR_TRACKED_NORM_AUTHORIZATION_20261105.json')['absolute_deadline_unix'])
window=dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=False,models=0,integrations=0)
dump('ROUND_WINDOW.json',window);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('NORM_FIXED_600S')));signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
records=[];status='RUNNING'
try:
    for entry in entries:
        assert sha(repo/entry['witness_file'])==entry['witness_sha256']
        z=np.load(repo/entry['witness_file']);poses=z['poses'];state=entry['state'];times=np.arange(1,329)*.01
        assert hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()==str(z['state_sha256'])
        original=field(state);old=original.trajectory_values(poses,.01)
        new=field(state);refine(new,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
        values=new.trajectory_values(poses,.01);radial=radial_values(new,poses,state,times)
        assert len(values)==328 and np.all(values>=old-1e-12)
        assert entry['original_reason']=='TIME_CLEARANCE' and old.min()<.155
        np.savez_compressed(root/f'step{entry["step"]:04d}.npz',poses=poses,times=times,old_values=old,new_values=values,radial_values=radial)
        record=dict(step=entry['step'],original_input=entry,old_minimum_m=float(old.min()),new_minimum_m=float(values.min()),new_complete_geometry_passed=bool(values.min()>=.155),
            original_self_margin_m=entry['self_domain_margin_m'],original_terminal_speed_m_s=entry['terminal_speed_m_s'])
        records.append(record);dump('RESULTS.json',records);print(json.dumps({k:v for k,v in record.items()if k!='original_input'}),flush=True)
    status='FIXED_DECLARED_NORM_GEOMETRY_QUALIFICATION_COMPLETE'
except BaseException as error:
    import traceback
    status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
    signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
    dump('COMPLETION.json',dict(status=status,records=records,models=0,integrations=0))
