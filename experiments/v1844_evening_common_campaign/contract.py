"""Frozen common-task identity, order and complete-window admission only."""
import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1844_evening_common_campaign'
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
KEYS=['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction','native_limit','stop_native','speed']
def validate(plan,registry):
 assert plan['locked_total']==9 and len(plan['assignments'])==9
 assert plan['common_registry_sha256']==sha(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')
 assert len({row['round_id']for row in plan['assignments']})==9
 methods={'TEB':'v1841_evening_teb','DWA':'v1842_evening_dwa','RP-CCR':'v1843_evening_rpccr'}
 expected=[('common_02','TEB'),('common_02','DWA'),('common_02','RP-CCR'),('common_03','DWA'),('common_03','RP-CCR'),('common_03','TEB'),('common_04','RP-CCR'),('common_04','TEB'),('common_04','DWA')]
 for i,row in enumerate(plan['assignments']):
  assert row['order']==i and (row['common_task'],row['method'])==expected[i]and row['production']==methods[row['method']],'REGISTERED_FIXED_ORDER'
  assert row['output_root']=='runs/v1844_evening_common_campaign/rounds/'+row['round_id'],'ROUND_OUTPUT_IDENTITY'
  task=read(R/row['output_root']/'PILOT_TASK.json');shared=next(x['task']for x in registry['tasks']if x['task']['task_id']==row['common_task'])
  assert task['common_task_id']==row['common_task']and task['task_id']==row['round_id']and task['common_method']==row['method']
  for key in KEYS:assert task[key]==shared[key],'COMMON_PHYSICAL_FIELD:'+key
  assert task['case_id']=='WEST_EAST'and task['maximum_control_native']==57600
  assert Path(task['output'])==R/row['output_root']/'actual'and Path(task['run_root'])==R/row['output_root']
 return True
def time_admission(auth,now,boot):
 assert auth['boot_id']==boot and auth['deadline_local']=='2026-11-24T21:00:00+08:00'
 assert auth['maximum_assignments']==9 and auth['maximum_round_s']==5400
 assert auth['normal_s']==4200 and auth['close_s']==1200
 assert now+auth['per_round_pipeline_admission_reserve_s']<auth['deadline_unix'],'NO_COMPLETE_ROUND_BEFORE_2100'
 return True
