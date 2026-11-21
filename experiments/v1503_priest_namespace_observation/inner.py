"""Exact nested OS/source target, no JAX/author/model imports or work."""
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import threading
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
class NoNumeric(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'jax','jaxlib','numpy','scipy','torch','mujoco','rclpy','vehicle','factory'}:raise AssertionError('NAMESPACE_TARGET_NO_NUMERIC_IMPORT:'+name)
def main():
 import sys
 sys.meta_path.insert(0,NoNumeric());guard_spec=importlib.util.spec_from_file_location('v1503_child_immutable_guard',R/'experiments/v1500_priest_thread_observation/common.py');guard_module=importlib.util.module_from_spec(guard_spec);guard_spec.loader.exec_module(guard_module);guard_module.guard(Path(os.environ['PHASE_WORKER_TASK'])/'volatile');spec=importlib.util.spec_from_file_location('v1503_current_namespace_mapper',C/'thread_observation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 stop=threading.Event();ready=[threading.Event(),threading.Event()];actual=[];threads=[];result=dict(passed=False,models=0,optimizer_calls=0)
 def hold(index):actual.append(threading.get_native_id());ready[index].set();stop.wait(8)
 try:
  assert sorted(os.sched_getaffinity(0))==[4]and os.environ['PHASE_REPO']==str(R)
  for i in range(2):
   t=threading.Thread(target=hold,args=(i,));threads.append(t);t.start();assert ready[i].wait(1)
  proof=m.observe('EXACT_NESTED_PID_NAMESPACE_SOURCE_TARGET');old=[]
  for row in proof['final_live']:
   value=dict(proc_tid=row['proc_tid'],correct_namespace_tid=row['current_namespace_tid'])
   try:value['old_query_mask']=sorted(os.sched_getaffinity(row['proc_tid']))
   except ProcessLookupError as error:value.update(old_error=repr(error),proc_task_still_visible=(Path('/proc/self/task')/str(row['proc_tid'])).exists())
   old.append(value)
  observed={v['current_namespace_tid']for v in proof['observed'].values()};assert set(actual)|{os.getpid()}<=observed
  assert any(v['proc_tid']!=v['current_namespace_tid']for v in proof['final_live']),'TARGET_DID_NOT_EXERCISE_NESTED_NAMESPACE'
  assert any(v.get('proc_task_still_visible')for v in old),'OLD_VISIBLE_ESRCH_NOT_REPRODUCED'
  base=Path('/proc/self/status').read_text();process=m.fields(base);negatives=[]
  for name,text,tid in [('ABSENT_NSPID','Pid: 1\nTgid: 1\n',1),('WRONG_GROUP','Pid: 1\nTgid: 999999\nNSpid: 1 2\n',1),('WRONG_PROC_ID',base,2147483000)]:
   try:m.bind_status(text,tid,process)
   except AssertionError:negatives.append(name)
   else:raise AssertionError('NAMESPACE_NEGATIVE_ACCEPTED:'+name)
  result.update(passed=True,actual_namespace_thread_ids=actual,observation=proof,old_raw_proc_tid_query=old,negative_cases=negatives,JAX_author_imported=False,constructor_calls=0)
 except BaseException as error:result.update(error=repr(error),traceback=traceback.format_exc())
 finally:
  stop.set()
  for t in threads:t.join(1)
  result['all_target_helpers_joined']=all(not t.is_alive()for t in threads)
  print(json.dumps(result,separators=(',',':'),allow_nan=False),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
