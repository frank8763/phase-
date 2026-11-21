"""Bind the next fair baseline to exact original inputs; grant no runtime."""
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
TASKS=R/'experiments/v1370_overnight_controller_matrix/TASKS.json'
CONTROLLER_FIELDS=frozenset({'algorithm','branch','candidate','controller_kind','controller_plugin','depends_on','nav2_params','output','run_id','task_id'})
PENDING_GATES=('distinct_scientific_integration_registration','exact_original_MPPI_plugin_and_parameters','actual_and_modeled_same_MPPI_ownership','current_input_complete_MPPI_witness_backend','same_observation_shared_skeleton_and_budgets','complete_process_source_byte_scope_qualification','original_dependency_status_and_failures_preserved','all_current_source_remote_recovery','full_all_runs_peak_and_once_scope')
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def describe():
 tasks=read(TASKS);rpp=next(t for t in tasks if t['task_id']=='rpp_default_horizon_m1_s01_main');mppi=next(t for t in tasks if t['task_id']=='coherent_mppi_horizon_m1_s01_main')
 assert {k for k in set(rpp)|set(mppi)if rpp.get(k)!=mppi.get(k)}==CONTROLLER_FIELDS,'UNDECLARED_SHARED_TASK_DIFFERENCE'
 assert mppi['seed']==10060001 and mppi['case_id']=='WEST_EAST'and mppi['planner_mode']==1
 assert mppi['controller_kind']==mppi['algorithm']=='mppi'and mppi['controller_plugin']=='Deadband'
 assert mppi['nav2_params']==str(R/'experiments/v1370_overnight_controller_matrix/coherent_mppi_params.json')
 closed=read(R/'runs/v1479_retirement_scope_binding/CLOSED_REVIEW.json')
 assert closed['closed']and not closed['passed']and closed['no_relaunch_or_frozen_edit']and closed['no_infinite_RPP_rescue']
 return dict(scope='FAIR_BASELINE_BINDING_PREPARATION_ONLY',candidate='ENGINEERING_COHERENT_MPPI_WITH_DISCLOSED_SHARED_EXECUTION',not_unmodified_author_whole_system=True,original_task_id=mppi['task_id'],original_task_sha256=hashlib.sha256(json.dumps(mppi,sort_keys=True,separators=(',',':')).encode()).hexdigest(),task_source_sha256=sha(TASKS),parameters_source=mppi['nav2_params'],parameters_sha256=sha(mppi['nav2_params']),original_dependencies=mppi['depends_on'],shared_task_fields_exact=True,controller_specific_fields=sorted(CONTROLLER_FIELDS),proposed_integrated_limits_reference='experiments/v1479_retirement_scope_binding/LIMITS.json',old_native60000_not_current_admission=True,original_RPP_non_success_preserved=True,RPP_relaunch_authorized=False,RPPlabeled_witness_cannot_authorize_MPPI=True,missing_gates=list(PENDING_GATES),models_authorized=False,whole_route_admission=False)

def authorize_runtime(*_args,**_kwargs):
 descriptor=describe()
 raise RuntimeError('MPPI_CURRENT_EVENT_RUNTIME_NOT_QUALIFIED:'+','.join(descriptor['missing_gates']))

if __name__=='__main__':
 print(json.dumps(describe(),ensure_ascii=False,indent=2))
