"""Actual pre-ARM budget functions on deterministic clocks; no processes/models."""
import ast,copy,hashlib,json,time
from pathlib import Path
from types import SimpleNamespace as S
from budget import create,validate,wait_ready,alarm_seconds,check_restore,TASK_S
R=Path(__file__).resolve().parents[2];O=R/'runs/v987_bounded_startup_components'
class Clock:
    def __init__(self,wall=1000.,mono=2000.):self.wall=wall;self.mono=mono;self.on_sleep=lambda:None
    def time(self):return self.wall
    def monotonic(self):return self.mono
    def sleep(self,n):self.wall+=n;self.mono+=n;self.on_sleep()
def main():
    task=dict(run_id='budget-counter-only',origin_native_tick=6083,origin_sim_time=60.83,wall_limit_s=40.,brake_s=2.)
    q={};cases=[]
    for label,ready_s,exit_s,stop_s,expected in [
        ('old_observed_129',129.176090034,1e6,1e6,True),('near_cap',179.9,1e6,1e6,True),
        ('hung',1e6,1e6,1e6,False),('failed_worker',129.,20.,1e6,False),('parent_stop',129.,1e6,10.,False),
        ('wrong_origin',1.,1e6,1e6,False)]:
        folder=O/('budget_'+label);folder.mkdir(exist_ok=False);clock=Clock();record=create(task,6400.,clock.time(),clock.monotonic())
        def update():
            elapsed=clock.monotonic()-2000.
            if elapsed>=ready_s and not(folder/'NATIVE_READY.json').exists():
                (folder/'NATIVE_READY.json').write_text(json.dumps(dict(origin_validated=True,native_tick=6084 if label=='wrong_origin' else 6083,sim_time=60.83)))
            if elapsed>=stop_s and not(folder/'PARENT_STOP_REQUEST.json').exists():
                (folder/'PARENT_STOP_REQUEST.json').write_text(json.dumps(dict(run_id=task['run_id'],reason='FIXTURE')))
        clock.on_sleep=update;job=S(poll=lambda:1 if clock.monotonic()-2000.>=exit_s else None)
        try:wait_ready(job,folder,record,task,clock);accepted=True;error=None
        except (AssertionError,InterruptedError)as e:accepted=False;error=str(e)
        cases.append(dict(case=label,passed=accepted==expected,accepted=accepted,wait_s=clock.monotonic()-2000.,error=error))
    q['actual_wait_cases']=all(c['passed']for c in cases)
    record=create(task,6400.,1000.,2000.)
    q['all_clocks_coherent']=validate(record,task,6400.)==record and record['hard_deadline_unix']==1350. and record['restore_stop_monotonic']==2180.
    bad=copy.deepcopy(record);bad['hard_deadline_unix']+=1
    try:validate(bad,task,6400.)
    except AssertionError:q['changed_clock_rejected']=True
    else:q['changed_clock_rejected']=False
    try:create(task,1374.,1000.,2000.)
    except AssertionError:q['insufficient_root_reserve_rejected']=True
    else:q['insufficient_root_reserve_rejected']=False
    q['backward_wall_clock_cannot_extend_alarm']=alarm_seconds(record,wall=900.,monotonic=2300.)==45.
    clock=Clock(wall=900.,mono=2181.)
    try:check_restore(record,O,task['run_id'],clock)
    except AssertionError:q['monotonic_restore_cap_even_after_wall_backstep']=True
    else:q['monotonic_restore_cap_even_after_wall_backstep']=False
    # Frozen old parent's own AST reproduces the exact missing slow-start case.
    source=R/'experiments/v985_rear_yaw_components/launch_one.py';tree=ast.parse(source.read_text())
    f=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main');body=next(x for x in f.body if isinstance(x,ast.Try)).body
    i=next(i for i,x in enumerate(body)if isinstance(x,ast.Assign)and any(isinstance(y,ast.Name)and y.id=='ready_until'for y in x.targets))
    clock=Clock(wall=0.,mono=0.)
    class Out:
        def __truediv__(self,key):return S(exists=lambda:clock.time()>=129.176090034)
    try:exec(compile(ast.fix_missing_locations(ast.Module(body=body[i:i+2],type_ignores=[])),str(source),'exec'),dict(time=clock,deadline=5400.,out=Out(),jobs=[S(poll=lambda:None)]))
    except AssertionError as e:q['old_actual_parent_still_red']=str(e)=='CANONICAL_STATE_RESTORE_TIMEOUT'
    else:q['old_actual_parent_still_red']=False
    result=dict(passed=all(q.values()),checks=q,cases=cases,models=0,integrations=0,
        original_red_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),actual_candidate_budget_functions=True,
        nonphysical_clock_fixture=True,task_hard_s=TASK_S,drive_s=40.,brake_s=2.)
    (O/'BUDGET_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
if __name__=='__main__':main()
