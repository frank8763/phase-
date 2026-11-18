"""Fixed saved-positive and isolated corruption gates for the goal auditor."""
import copy
import fcntl
import importlib.abc
import json
from pathlib import Path
import signal
import sys
import time
import traceback


class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('AUDIT_ZERO_MODELS '+name)


sys.meta_path.insert(0,NoModels())
from audit_goal import R,q,np,verify,load_bundle,COUNTS
C=Path(__file__).resolve().parent;O=R/'runs/v1204_goal_audit_worker'
P=R/'runs/v1203_goal_entry_handoff'
NAMES=['C1_nominal','A2_nominal','B1_nominal','P1_nominal','C1_yaw_plus','B1_x_minus','B1_y_plus','P1_x_plus']
TABLE_PATHS=[]


def table_for(name):
    label=name.split('_')[0]
    version,task={'C1':('v1195','recovery_main_slot01'),'A2':('v1191','recovery_main_slot02'),
        'B1':('v1194','recovery_main_slot01'),'P1':('v1189','recovery_main_slot01')}[label]
    path=R/'runs/v858_nav2_verified'/version/task/'LIVE_GOAL_TABLE.npz'
    TABLE_PATHS.append(path)
    with np.load(path)as z:return {k:z[k].copy()for k in z.files}


def main():
    O.mkdir(exist_ok=True);assert not (O/'GOAL_AUDIT_QUALIFICATION.json').exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    frozen={str(p.relative_to(R)):q.sha(p)for p in [*C.glob('*.py'),C/'PROTOCOL.md']}
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path and Path(path).resolve().is_relative_to(R) and Path(path).suffix=='.py':
            p=Path(path).resolve();frozen[str(p.relative_to(R))]=q.sha(p)
    cases=[]
    for load,parent in [(False,P),(True,P/'CARRIED_MODE_QUALIFICATION')]:
        for name in NAMES:
            path=parent/name;x=json.loads((P/name/'INPUT.json').read_text());b=load_bundle(path)
            cases.append((load,name,x,table_for(name),b))
            for p in path.iterdir():
                if p.is_file():frozen[str(p.relative_to(R))]=q.sha(p)
    for p in [*TABLE_PATHS,R/'experiments/v1159_bounded_steering_load/PARAMETERS.json',R/'runs/v1159_bounded_steering_load/profile.so']:
        frozen[str(p.relative_to(R))]=q.sha(p)
    q.dump(C/'AUDIT_FREEZE.json',dict(files=frozen,wall_cap_s=180))
    started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('AUDIT180')));signal.alarm(180)
    results=[];negatives=[];error=None
    try:
        for load,name,x,table,b in cases:
            result=verify(x,table,b,load)
            results.append(dict(case=name,initial_load=load,**result))
        _,name,x,table,original=cases[8]
        changes=[
            ('request',lambda b:b['trace']['requests'].__setitem__((10,0),b['trace']['requests'][10,0]+.001)),
            ('measured_state',lambda b:b['trace']['states'].__setitem__((100,0),b['trace']['states'][100,0]+.02)),
            ('ctrl',lambda b:b['trace']['controls'].__setitem__((10,0),b['trace']['controls'][10,0]+.001)),
            ('integral',lambda b:b['trace']['memory'].__setitem__((100,4),b['trace']['memory'][100,4]+.001)),
            ('handoff_mode',lambda b:b['result']['generations'][1]['origin'].update(steering_load_episode=False)),
            ('handoff_clock',lambda b:b['handoff']['packet'].update(sim_time=0.)),
            ('handoff_origin',lambda b:b['result']['generations'][1]['origin']['state'].__setitem__(0,b['result']['generations'][1]['origin']['state'][0]+.01)),
            ('source_reference',lambda b:b['initial_ref']['states'].__setitem__((50,0),b['initial_ref']['states'][50,0]+.01)),
            ('incomplete_tail',lambda b:b['trace'].update(requests=b['trace']['requests'][:-1])),
            ('native_journal',lambda b:b['journal'][100].update(native=b['journal'][100]['native']+1)),
            ('handoff_offset',lambda b:b['result']['generations'][1].update(offset=b['result']['generations'][1]['offset']+1)),
            ('false_clearance',lambda b:b['result']['proof'].update(minimum_raw_m=b['result']['proof']['minimum_raw_m']+.1)),
            ('moving_final_stop',lambda b:b['trace']['requests'].__setitem__((-1,0),.001)),
            ('shadow',lambda b:b['trace']['shadow'].__setitem__((100,0),b['trace']['shadow'][100,0]+.01))]
        for name,mutate in changes:
            bad=copy.deepcopy(original);mutate(bad)
            try:verify(x,table,bad,True)
            except AssertionError as exc:negatives.append(dict(case=name,rejected=True,reason=str(exc)))
            else:raise AssertionError('TAMPER_ACCEPTED '+name)
    except BaseException as exc:
        error=dict(error=repr(exc),traceback=traceback.format_exc(),partial_work='unknown; successful saved audit counts only')
    finally:
        signal.alarm(0)
        result=dict(closed=True,passed=len(results)==16 and len(negatives)==14 and error is None,
            positives=results,negatives=negatives,error=error,wall_s=time.monotonic()-started,
            positive_analytical_cpp_native=sum(r['analytical_cpp_native']for r in results),
            all_analytical_cpp_native=COUNTS['cpp_native'],
            partial_analytical_work_unknown=COUNTS['partial_unknown'],
            source_unchanged=all(q.sha(R/p)==h for p,h in frozen.items()),guard_original=q.sha(R/'REVIEW_PENDING')==q.GUARD,
            models=0,new_mujoco_native=0,physical_audit_complete=False)
        q.dump(O/'GOAL_AUDIT_QUALIFICATION.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['positives','negatives']}))


if __name__=='__main__':main()
