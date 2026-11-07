"""Independent qualification, geometry and unchanged original-model coverage."""
import hashlib,importlib.abc,json,sys
from pathlib import Path
import numpy as np
own=Path(__file__).parent;repo=own.parents[1];root=repo/'runs/v815_stopping_corridor_qualification'
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('SAVED_QUALIFICATION_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
sys.path.insert(0,str(repo/'experiments/v812_soft_global_reference'));sys.path.insert(0,str(own))
from exact_footprint import pose_values
from independent_corridor import independent_field,containment
from independent_soft_reference import soft_values
from union_belief import future_cells
from motion_evaluator import check_forecast

read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
protocol=read(repo/'runs/v812_soft_global_reference/main_slot01/paired/STATIC_PROTOCOL.json')
config=read(repo/'runs/v812_soft_global_reference/main_slot01/paired/DYNAMIC_PROTOCOL.json')
rows=read(root/'RESULTS.json');records=[];samples=0
for row in rows:
    state=row['state'];excess,n=containment(state,row['corridor_world'],len(protocol['known_rectangles']));samples+=n
    checks=dict(input_sha=sha(repo/row['source'])==row['source_sha256'],no_truth=state['hidden_world_geometry_used']is False and row['metadata']['hidden_world_geometry_used']is False,
        original_current_hard_geometry_retained=row['corridor_world']['rectangles'][:11]==[*protocol['known_rectangles'],state['current_outer_rectangle']]and row['corridor_world']['circles']==protocol['known_circles'],
        continuous_hull_sampled_containment=excess<=1e-10,original_329_execution_coverage=check_forecast(config,state)['passed'],metadata_horizon=row['metadata']['horizon_s']==3.28,
        separated_execution=row['metadata']['reference_is_not_dynamic_execution_certificate']and row['metadata']['all_actual_328_native_admission_unchanged'])
    role=row['required_role'];error=heat_error=None
    if row['path']is not None:
        z=np.load(root/(row['label']+'.npz'));p=z['path'];f=independent_field(protocol,state)
        values=pose_values(f,z['dense']);error=float(np.max(abs(values-z['corridor_values'])));heat_error=float(np.max(abs(soft_values(f,state,z['dense'])-z['soft_heat'])))
        checks.update(geometry_exact=error<=1e-10,soft_cost_exact=heat_error<=1e-10,
            entire_dense_stopping_corridor_floor=bool(values.min()>=max(.155,row['stats']['guard_m'])-1e-8),registered_gear_scope=(role=='CHARACTERIZE_TRAPPED_INPUT')or bool(np.all(p[:,3]>0)))
    if role=='FULL_GOAL':checks['registered_functional_qualification']=row['path']is not None and row['stats']['status']=='GLOBAL_GOAL_PATH'and row['endpoint_goal_m']<=.28
    elif role=='MEANINGFUL_FORWARD':checks['registered_functional_qualification']=row['path']is not None and (row['endpoint_goal_m']<=.28 or row['start_goal_m']-row['endpoint_goal_m']>=.5)
    elif role=='REJECT_TOO_CLOSE_STOP':checks['registered_functional_qualification']=row['path']is None and row['stats']['status']=='START_BELOW_HARD_FLOOR'
    elif role=='CHARACTERIZE_TRAPPED_INPUT':checks['registered_functional_qualification']=row['path']is not None or row['stats']['status']in['START_BELOW_HARD_FLOOR','NO_MEANINGFUL_GLOBAL_PROGRESS_WITHIN_BUDGET','NO_PROGRESS_PATH']
    else:raise AssertionError('UNREGISTERED_ROLE')
    # The actual 657-step union is unchanged. Its relation to the original
    # global tracker bounds is also checked, independently of the 3.28s guide.
    t=np.arange(657)*.01;tt=t[:,None];pl=np.asarray(state['position_lower']);pu=np.asarray(state['position_upper']);vl=np.asarray(state['velocity_lower']);vu=np.asarray(state['velocity_upper'])
    lo=np.maximum(pl+tt*vl-.02*tt**2,pl-.12*tt)-1e-5;hi=np.minimum(pu+tt*vu+.02*tt**2,pu+.12*tt)+1e-5
    cl,ch=future_cells(state['outer_state_cells'],t)
    checks['original_657_joint_cells_retained']=bool(np.max(lo[:,None]-cl)<=1e-7 and np.max(ch-hi[:,None])<=1e-7)
    records.append(dict(label=row['label'],checks={k:bool(v)for k,v in checks.items()},passed=bool(all(checks.values())),maximum_corridor_error=error,maximum_soft_error=heat_error,containment_excess_m=excess))
checks=dict(exact_initial_astar=read(root/'INITIAL_ROUTE.json')['status']=='EXACT_V812_INITIAL_ASTAR_PATH',fixed_inputs=[r['label']for r in rows]==['OLD303','OLD375','STOP442','STOP626'],all_registered_gates=all(r['passed']for r in records))
result=dict(status='STOPPING_CORRIDOR_FIXED_QUALIFICATION_PASS'if all(checks.values())else'STOPPING_CORRIDOR_QUALIFICATION_NOT_PASSED',checks=checks,records=records,
    sampled_joint_cell_times=samples,original_execution_coverage_queries=4*329,original_planning_coverage_queries=4*657,models=0,integrations=0,
    scope='Causal geometric stopping-room proposal qualification only; actual approach, braking, complete arrival and repeats remain untested.')
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(0 if all(checks.values())else 1)
