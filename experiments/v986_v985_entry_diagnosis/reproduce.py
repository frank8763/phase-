"""Execute the frozen parent's actual ready-wait AST with a deterministic clock.

No process, ROS, model, physical prediction, native replay or real sleep occurs.
The proposed budget is a future operational design, not a new authorized entry.
"""
import ast,hashlib,json
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];O=R/'runs/v986_v985_entry_diagnosis'
SOURCE=R/'experiments/v985_rear_yaw_components/launch_one.py'
def run_wait(nodes,ready_at,deadline=5400.,worker_exit_at=None):
    class Clock:
        now=0.
        def time(self):return self.now
        def sleep(self,n):self.now+=n
    clock=Clock()
    class Out:
        def __truediv__(self,name):
            assert name=='NATIVE_READY.json'
            return SimpleNamespace(exists=lambda:clock.now>=ready_at)
    job=SimpleNamespace(poll=lambda:1 if worker_exit_at is not None and clock.now>=worker_exit_at else None)
    env=dict(time=clock,deadline=deadline,out=Out(),jobs=[job])
    try:exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(SOURCE),'exec'),env)
    except AssertionError as e:return dict(passed=False,error=str(e),wait_s=clock.now)
    return dict(passed=True,wait_s=clock.now)
def main():
    original=json.loads((R/'experiments/v985_rear_yaw_components/SOURCE_FREEZE.json').read_text())
    h=hashlib.sha256(SOURCE.read_bytes()).hexdigest();assert original['files'][str(SOURCE.relative_to(R))]==h
    tree=ast.parse(SOURCE.read_text());main_fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    block=next(n for n in main_fn.body if isinstance(n,ast.Try)).body
    index=next(i for i,n in enumerate(block)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='ready_until'for t in n.targets))
    nodes=block[index:index+2];assert isinstance(nodes[1],ast.While)
    actual=json.loads((O/'RUNTIME_TIMING.json').read_text())['summaries']['factory_initialize']['inclusive_wall_s']
    red=run_wait(nodes,actual)
    assert not red['passed']and red['error']=='CANONICAL_STATE_RESTORE_TIMEOUT'
    boundary=run_wait(nodes,119.9);worker=run_wait(nodes,129.18,worker_exit_at=20.)
    assert boundary['passed']and worker['error']=='NATIVE_FAILED_BEFORE_CANONICAL_READY'
    # Explicitly proposed pre-ARM wall budgets only. Original driving and brake
    # budgets stay 40+2; actual native safety/timing gates are not changed here.
    budgets=dict(restore_cap_s=180.,ros_startup_s=35.,driving_s=40.,brake_s=2.,save_replay_s=40.,failure_closure_s=40.,margin_s=13.)
    assert sum(budgets.values())==350.
    proposed=ast.parse("ready_until=min(deadline-170,time.time()+180)\nwhile not (out/'NATIVE_READY.json').exists():\n assert jobs[0].poll() is None,'NATIVE_FAILED_BEFORE_CANONICAL_READY'\n assert time.time()<ready_until,'CANONICAL_STATE_RESTORE_TIMEOUT'\n time.sleep(.05)\n").body
    cases=dict(actual_saved_latency=run_wait(proposed,actual),near_cap_success=run_wait(proposed,179.9),
        startup_hang_rejected=run_wait(proposed,float('inf')),root_reserve_rejected=run_wait(proposed,129.18,deadline=260.),
        worker_failure_rejected=run_wait(proposed,129.18,worker_exit_at=20.))
    checks=dict(original_recorded_bug_reproduced=not red['passed'],original_fast_start_positive=boundary['passed'],
        original_failed_worker_rejected=not worker['passed'],proposed_actual_latency_admitted=cases['actual_saved_latency']['passed'],
        proposed_near_cap_admitted=cases['near_cap_success']['passed'],proposed_hang_stops=not cases['startup_hang_rejected']['passed'],
        proposed_root_reserve_kept=not cases['root_reserve_rejected']['passed'],proposed_failed_worker_stops=not cases['worker_failure_rejected']['passed'],
        task_budget_arithmetic=budgets['driving_s']==40 and budgets['brake_s']==2 and sum(budgets.values())==350)
    result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,actual_frozen_parent_ast_executed=True,
        source=str(SOURCE.relative_to(R)),source_sha256=h,recorded_factory_restore_wall_s=actual,
        original_parent_reproduction=red,original_boundary_case=boundary,proposed_budget_cases=cases,
        proposed_phase_budget=budgets,proposed_task_hard_s=350.,proposed_campaign_wait_s=360.,proposed_root_launch_reserve_s=375.,
        no_live_source_modified=True,no_new_physical_entry_prepared=True,no_model_authority=True,
        scope='Parent wait-loop and wall-budget arithmetic only. Does not qualify actual cold start, vehicle response or dynamic navigation.')
    (O/'PARENT_WAIT_REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));assert result['passed']
if __name__=='__main__':main()
