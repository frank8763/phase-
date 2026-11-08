"""Pure-data route/dependency gates, explicit unchanged scientific-engine bindings."""
import ast,copy,hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v885_remaining_static_routes'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
import authority as a
from handshake import ProtocolError
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    tasks=read(C/'TASKS.json');old=read(R/'experiments/v881_timing_accounting_continuation/TASKS.json');checks={};freeze=read(R/'experiments/v884_feasible_rpp/SOURCE_FREEZE.json')
    for name,h in freeze['files'].items():assert sha(R/name)==h,name
    checks['all6575_V884_sources_and_plugin_unchanged']=True;checks['real_frozen_NS_anchor']=a.validate_ns_anchor();checks['old_NS_loop_and_entry_qualification_reused_by_source_SHA']=read(R/'records/nav2_v884_20261108/ZERO_QUALIFICATION.json')['passed']and read(R/'records/nav2_v884_20261108/ENTRY_QUALIFICATION.json')['passed'];checks['new_actual_entry_15_cases']=read(O/'ENTRY_QUALIFICATION.json')['passed']
    for t in tasks:
        original=next(x for x in old if x['variant']=='A'and x['case_id']==t['case_id']and x['stage']=='static_main');checks[t['task_id']+'_exact_original_physical_task']=all(t[k]==original[k]for k in ['case_id','seed','phase','dynamic','goal_xy','goal_yaw','wall_limit_s','brake_s'])and t['nav2_params']==str(R/'experiments/v884_feasible_rpp/A_feasible.yaml')
    def virtual(task,dep=True,main=True):
        root=dict(models_authorized=True,user_requested_next_static_stage=True,scope=a.SCOPE,source_freeze_sha256='ZERO_ONLY',started_unix=100.,deadline_unix=5500.)
        receipt=dict(root,run_id=task['run_id'],task_sha256=a.digest(task))
        def data(p):
            if Path(p)==O/'AUTHORIZATION.json':return root
            if Path(p)==C/'TASKS.json':return tasks
            if Path(p)==O/'WEST_EAST_REPEAT_COMPARISON.json':return dict(passed=dep)
            return dict(passed=main)
        with patch.object(a,'read',side_effect=data),patch.object(a,'DEADLINE',5500.),patch.object(a,'validate_ns_anchor',return_value=True),patch.object(Path,'exists',return_value=False):return a.authorized(task,receipt,101.,'ZERO_ONLY')
    for t in tasks:
        checks[t['task_id']+'_positive_gate']=virtual(t)==5500.
        if t['task_id'].startswith('repeat_'):
            try:virtual(t,main=False);checks[t['task_id']+'_main_failure_rejected']=False
            except ProtocolError:checks[t['task_id']+'_main_failure_rejected']=True
        if t['case_id']=='EAST_WEST':
            try:virtual(t,dep=False);checks[t['task_id']+'_WE_pair_failure_rejected']=False
            except ProtocolError:checks[t['task_id']+'_WE_pair_failure_rejected']=True
    proof=read(C/'NS_ANCHOR.json');bad=copy.deepcopy(proof);key=next(iter(bad['files']));bad['files'][key]='0'*64;original=a.read
    with patch.object(a,'read',side_effect=lambda p:bad if Path(p)==C/'NS_ANCHOR.json'else original(p)):checks['tampered_NS_anchor_rejected']=a.validate_ns_anchor()is False
    checks['fixed_order_four_tasks']=[t['task_id']for t in tasks]==['main_we','repeat_we','main_ew','repeat_ew'];checks['deadline_exactly_inherited']=a.DEADLINE==read(R/'records/nav2_v884_20261108/ROUND_WINDOW.json')['deadline_unix'];checks['no_new90min_created']=read(C/'WINDOW_POLICY.json')['new90min_not_created'];checks['no_model_window_started']=not(O/'AUTHORIZATION.json').exists()and not(O/'ROUND_WINDOW.json').exists()and not(R/'runs/v858_nav2_verified/v885').exists()
    for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    result=dict(passed=all(checks.values()),checks=checks,scientific_revisions=0,models=0,native_integrations=0,real_ros_servers=0,new_model_window_started=False,underlying_native_fault_cases_reused=19,new_actual_entry_cases=15,scope='Remaining fixed route operation/dependency qualification only; source-exact V884 scientific engines, no new ROS or physics run')
    (O/'ZERO_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
