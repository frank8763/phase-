"""Record explicit original-contract authorization before all numerical work."""
import copy,json,time
from context import C,O,R,OLD,put,sha,digest
def main():
 auth=json.loads((R/'runs/v1620_mechanism_boundary/EVALUATION_AUTHORIZATION.json').read_text())
 assert time.time()+600<auth['absolute_deadline_unix']
 old=json.loads((R/'runs/v1620_mechanism_boundary/TASKS_LOCKED.json').read_text())
 new=copy.deepcopy(old)
 templates={t['case_id']:t for t in json.loads((OLD/'TASKS.json').read_text())if t['task_id']in {'main_slot01','main_slot09','main_slot17'}}
 for row in new['tasks']:
  task=row['task'];task['seed']=templates[task['case_id']]['seed'];task['run_root']=str(O)
  task['output']=str(O/task['task_id']);task['sensor_seed_unchanged']=True
  for a in row['assignments']:a['output']=str(O/a['assignment_id'])
 new.update(original_contract_user_selected=True,all_formal_assignments_unexecuted=True,
    superseded_plan_sha256=sha(R/'runs/v1620_mechanism_boundary/TASKS_LOCKED.json'),
    correction='New phase only: retain original route sensor seed; previous new seeds would change sensor corruption. No model or outcome preceded correction.',physical_admission=False)
 pilot=copy.deepcopy(templates['WEST_EAST']);pilot.update(task_id='pilot_WE_full',run_id='v1624-pilot_WE_full',output=str(O/'pilot_WE_full'),run_root=str(O),role='pilot',stage='exposed_operational_development',scope='original_contract_operational_pilot_not_new_task')
 limits=dict(storage_limit_bytes=15*1024**3,maximum_task_evidence_bytes=224*1024**2,remaining_archive_download_reserve_bytes=272*1024**2,root_reserve_bytes=512*1024**2,maximum_actual_native=60000,maximum_replay_native=60000,cpp_native_cap=150000000,python_native_cap=25000000,maximum_round_s=5400,close_reserve_s=1200,maximum_factory_attempts=1,internal_factory_models=None,qualified=False)
 for name,value in [('AUTHORIZATION.json',dict(authorized=True,user_instruction='采用V1281原合同做独立仿真对照，保留其全部安全门；明确不声称满足周末新版合同',prior_root_authorization=auth,weekend_restarted=False,source_only_until_new_admission=True)),('TASKS_LOCKED.json',new),('PILOT_TASK.json',pilot),('LIMITS_DRAFT.json',limits)]:
  assert not(O/name).exists();put(O/name,value)
 print(json.dumps(dict(prepared=True,phase_only_sensor_seed_fixed=True,models=0,physical_admission=False)))
if __name__=='__main__':main()
