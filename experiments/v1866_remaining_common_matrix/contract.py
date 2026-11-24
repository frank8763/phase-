"""Exact remaining original registry matrix and fixed rotated method order."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1866_remaining_common_matrix'
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
KEYS=['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction','native_limit','stop_native','speed']
def expected():
 return [(f'common_{i:02d}',m)for i in range(5,13)for m in [['RP-CCR','DWA','TEB'],['DWA','TEB','RP-CCR'],['TEB','RP-CCR','DWA']][(i-5)%3]]
def validate(plan,registry):
 assert plan['locked_total']==24 and len(plan['assignments'])==24
 assert plan['common_registry_sha256']==sha(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')
 assert len({r['round_id']for r in plan['assignments']})==24
 for i,row in enumerate(plan['assignments']):
  assert row['order']==i and(row['common_task'],row['method'])==expected()[i],'REGISTERED_FIXED_ORDER'
  production={'TEB':'v1862_remaining_routes_teb','DWA':'v1863_remaining_routes_dwa','RP-CCR':'v1864_remaining_routes_rpccr_ns'if i<12 else'v1865_remaining_routes_rpccr_ew'}[row['method']]
  assert row['production']==production,'REGISTERED_ROUTE_METHOD_PRODUCTION'
  assert row['output_root']=='runs/v1866_remaining_common_matrix/rounds/'+row['round_id'],'ROUND_OUTPUT_IDENTITY'
  task=read(R/row['output_root']/'PILOT_TASK.json');shared=next(x['task']for x in registry['tasks']if x['task']['task_id']==row['common_task'])
  assert task['common_task_id']==row['common_task']and task['task_id']==row['round_id']and task['common_method']==row['method']
  for k in KEYS:assert task[k]==shared[k],'COMMON_PHYSICAL_FIELD:'+k
  assert task['case_id']==('NORTH_SOUTH'if i<12 else'EAST_WEST')and task['maximum_control_native']==57600
  assert Path(task['output'])==R/row['output_root']/'actual'and Path(task['run_root'])==R/row['output_root']
  if row['method']=='RP-CCR':assert task['mechanism_variant']=='full'
 return True
def time_admission(auth,now,boot):
 assert auth['boot_id']==boot and auth['deadline_local']=='2026-11-24T21:00:00+08:00'
 assert auth['maximum_assignments']==24 and auth['maximum_round_s']==5400 and auth['normal_s']==4200 and auth['close_s']==1200
 assert now+auth['per_round_pipeline_admission_reserve_s']<auth['deadline_unix'],'NO_COMPLETE_ROUND_BEFORE_2100'
 return True
