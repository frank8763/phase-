"""Pure registered-assignment selection. Never grants model/physical authority."""
import copy,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def select(locked,assignment_id,output_root):
 assert locked['assignment_count']==20 and locked['task_count']==12
 assert locked['original_contract_user_selected']and not locked['new_map']and not locked['new_motion_class']
 matches=[];order=[]
 for row in locked['tasks']:
  task=row['task'];case=task['case_id'];expected={'WEST_EAST':{'full','no_onward'},'EAST_WEST':{'full','no_time'},'NORTH_SOUTH':{'full'}}
  assert case in expected and set(row['variants'])==expected[case]
  assert task['sensor_seed_unchanged']and task['original_pool_task']is None
  assert task['historical_prefix_native']==0 and task['from_actual_native_zero']and task['native_limit']==60000 and task['stop_native']==2200
  assert row['assignments']and {a['variant']for a in row['assignments']}==expected[case]
  for assignment in row['assignments']:
   assert assignment['task_id']==task['task_id'];order.append(assignment['assignment_id'])
   if assignment['assignment_id']==assignment_id:matches.append((task,assignment))
 assert len(order)==len(set(order))==20 and len(matches)==1
 original,assignment=matches[0];root=Path(output_root).resolve();assert root==R/'runs/v1643_formal_parent_metadata'
 assert assignment_id.replace('_','').isalnum()and '/'not in assignment_id
 task=copy.deepcopy(original);round_root=root/'rounds'/assignment_id
 # Only output identifiers change; scientific task fields retain original bytes.
 for key in ['output','run_root','run_id','task_id']:task.pop(key)
 scientific_task_sha256=digest(task)
 task.update(output=str(round_root/'actual'),run_root=str(round_root),run_id='v1642-'+assignment_id,
             task_id=assignment_id,parent_task_id=original['task_id'],mechanism_variant=assignment['variant'],
             formal_assignment_id=assignment_id,formal_order_index=order.index(assignment_id))
 return dict(task=task,variant=assignment['variant'],assignment_id=assignment_id,
             scientific_task_sha256=scientific_task_sha256,registered_order=order,
             original_registered_task=copy.deepcopy(original),physical_authorized=False,
             models_authorized=False,not_original_exposed_task=True)
