"""No-model night admission: real imports, exact tasks, gates and operations."""
import os,sys,ast,json,copy,importlib.abc,math,time,tempfile
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from resource_policy import apply
resource=apply()
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from authority import authorized
from decisions import can_continue_after_failure,three_gate,confirmation_gate
from execute import ProcessJob
assert resource['cpu_affinity']==[2]and resource['nice']==19 and resource['scheduler']==os.SCHED_IDLE and resource['gpu_visible']==''and resource['mujoco_gl']=='disable';assert ProcessJob.__init__.__globals__['C']==C
checks_={}
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
for name in ['worker','audit','fresh','handoff','atomic','capture','execute','scene_binding']:load('v1062_qualification_'+name,C/(name+'.py'))
checks_['real_entry_modules_model_free_import_and_own_namespace']=True
from scene_binding import create_vehicle
try:create_vehicle(None,None)
except AssertionError as e:assert str(e)=='PHYSICAL_MODELS_DISABLED_FOR_PREPARATION'
else:raise AssertionError('MODEL_CREATION_WITHOUT_AUTHORITY')
checks_['model_guard_before_import']=True
tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==78 and len({t['task_id']for t in tasks})==78 and len({t['output']for t in tasks})==78;branches=json.loads((C/'BRANCHES.json').read_text());assert len(branches)==4
for t in tasks:
 assert json.loads((C/('TASK_'+t['task_id']+'.json')).read_text())==t
 meta=json.loads((O/(t['case_id']+'_T0_METADATA.json')).read_text());assert t['start_xy']==meta['packet']['body'][:2]and t['goal_xy']==meta['goal']and t['start_yaw']==meta['packet']['body'][2]and t['course_id']=='V1061_EW_START_NORTH_010';assert Path(t['output'])==R/'runs/v858_nav2_verified/v1062'/t['task_id']
for case in ['WEST_EAST','NORTH_SOUTH','EAST_WEST']:
 source=json.loads((O/(case+'_STATIC_SOURCE.json')).read_text());assert source['passed']and source['audit']['passed']
checks_['all_tasks_course_identity_and_three_complete_static_sources']=True
pool=json.loads((C/'CONFIRMATION_POOL.json').read_text());assert len(pool)==24 and len({x['seed']for x in pool})==24 and min(x['seed']for x in pool)==1011062001
for case in ['WEST_EAST','NORTH_SOUTH','EAST_WEST']:assert sum(x['case_id']==case for x in pool)==8
for d in ['POSITIVE_AXIS','NEGATIVE_AXIS']:assert sum(x['initial_axis_motion_direction']==d for x in pool)==12
assert all((math.cos(x['phase'])>0)==(x['initial_axis_motion_direction']=='POSITIVE_AXIS')for x in pool);checks_['fixed24_preregistered_balanced_fresh_pool']=True
fake=[dict(task=dict(case_id=case,kind=kind),passed=True)for case in ['NORTH_SOUTH','EAST_WEST','WEST_EAST']for kind in ['main','repeat']];repeats=[dict(passed=True)]*3;assert three_gate(fake,repeats)
for i in range(6):bad=copy.deepcopy(fake);bad[i]['passed']=False;assert not three_gate(bad,repeats)
assert not three_gate(fake,repeats[:2]);checks_['full_six_actual_tasks_and_three_repeats_required']=True
rows=[dict(task=dict(slot=i),passed=True)for i in range(1,25)];assert confirmation_gate(rows,pool);rows[0]['passed']=False;assert confirmation_gate(rows,pool);rows[1]['passed']=False;assert not confirmation_gate(rows,pool)and not confirmation_gate(rows[:-1],pool);checks_['full24_and_direction_route_functional_gates']=True
safe=dict(safety_passed=True,prediction=dict(passed=True));assert can_continue_after_failure(dict(passed=False,error="AssertionError('NO_ORIGINAL_GOAL_INPUT_SEED')"),safe)
for error in ['LOCAL_NATIVE_TRACKING_FAILED','NATIVE_SAFETY_ANOMALY','FUTURE_SOURCE','UNKNOWN_ERROR'] :assert not can_continue_after_failure(dict(passed=False,error=error),safe)
assert not can_continue_after_failure(dict(passed=False,error='SOURCE_PRODUCER_FAILED'),dict(safety_passed=False,prediction=dict(passed=True)));checks_['unsafe_or_unknown_failure_stops_all_branches']=True
# End-to-end route identities and output receipts are validated by the real
# authority against an isolated temporary metadata filesystem, never a model.
import authority
with tempfile.TemporaryDirectory(dir=O,prefix='authority_fixture_')as temp:
 tc=Path(temp)/'source';to=Path(temp)/'run';tc.mkdir();to.mkdir();task=tasks[0];(tc/'TASKS.json').write_text(json.dumps(tasks));tp=tc/('TASK_'+task['task_id']+'.json');tp.write_text(json.dumps(task));(tc/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files={})));(to/'ROUND_WINDOW.json').write_text(json.dumps(dict(absolute_deadline_unix=HARD_END,hard_stop_monotonic=time.monotonic()+1000)));(to/'APPROVAL.json').write_text(json.dumps(dict(models_authorized=True,absolute_deadline_unix=HARD_END,allowed_task_ids=[task['task_id']])));receipt=dict(task_id=task['task_id'],task_sha256=sha(tp),source_sha256=sha(tc/'SOURCE_FREEZE.json'),window_sha256=sha(to/'ROUND_WINDOW.json'),task_deadline_unix=time.time()+90);old=(authority.C,authority.O);authority.C,authority.O=tc,to
 try:
  assert authority.authorized(task,receipt)>time.time();bad=dict(receipt,task_sha256='wrong')
  try:authority.authorized(task,bad)
  except AssertionError:pass
  else:raise AssertionError('CHANGED_RECEIPT_ACCEPTED')
 finally:authority.C,authority.O=old
checks_['actual_authority_positive_and_changed_receipt_rejected']=True
assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert not(O/'ROUND_WINDOW.json').exists();checks_['old_window_closed_guard_original_and_zero_models']=True
result=dict(passed=True,checks=checks_,resource_policy=resource,models=0,integrations=0,not_a_physical_preflight=True);dump(O/'OPERATIONS_QUALIFICATION.json',result);print(json.dumps(result))
