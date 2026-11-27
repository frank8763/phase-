"""One zero-model source qualification; original active locks untouched."""
from pathlib import Path
import ast,os,time,json,traceback
from context import R,C,SOURCE as S,read,put,sha

def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0,optimizer_queries=0));result=dict(passed=False,closed=False,models=0,DLLs=0,optimizer_queries=0,physics=0,replay=0,formal_tasks=0)
 try:
  P=R/'runs/v2134_pcbf_remaining_numeric';prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items())and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']
  assert read(S/'PERSISTENT_PROTOCOL_PROOF.json')['passed']and read(S/'SOFT_PREDICTION_GATE_PROOF.json')['passed']
  from context import predecessors_closed
  predecessors_closed();assert read(S/'MEASURED_CLOCK_REGRESSION.json')['passed']
  proof=read(S/'COMPONENT_INTERFACE_PROOF.json');assert proof['passed']and proof['models']==proof['optimizer_queries']==0 and read(S/'DISPATCHER_SOFTWARE_PROOF.json')['passed']
  for n in proof['unchanged_low_level_modules']:assert(C/n).read_bytes()==(R/'experiments/v2122_priest_quiescent_handoff'/n).read_bytes(),n
  assert(C/'filter.py').read_bytes()==(R/'experiments/v2134_pcbf_remaining_numeric/filter_minimal.py').read_bytes()
  for n in['geometry.py','kinematics.py','oracle.py','request.py']:assert(C/n).read_bytes()==(R/'experiments/v2131_filter_measured_current'/n).read_bytes(),n
  registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']=='common_01')
  for method in['PCBF']:
   o=S/'components'/method;task=read(o/'PILOT_TASK.json')
   for key in['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id']:assert task[key]==original[key]
   assert task['component_not_navigation']and not task['formal_common_task']and task['maximum_control_native']==100 and task['stop_native']==2200
   assert all(not(o/n).exists()for n in['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])
  from reserved_census import admission
  reserve=admission();files=dict(prior)
  for folder in[C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.suffix not in{'.log','.console'}and p.name not in{'SOURCE_ONCE.json','dispatcher.lock'}:
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for folder in[S/'components',S/'software',S/'software_attempt01']:
   for p in folder.rglob('*'):
    if p.is_file()and p.suffix=='.json':files[str(p.relative_to(R))]=sha(p)
  from evidence import deliver
  for rid in[None,'PCBF']:compile(deliver(rid,preview=True),str(C/'generated_transport.py'),'exec')
  assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),delta_members=len(files)-len(prior),fixed_components=['PSF','PCBF'],no_formal_admission=True,all_generated_transport_variants_compiled=True,unchanged_physical_and_numerical_bodies=True,reservation=reserve,software_proof_sha256=sha(S/'COMPONENT_INTERFACE_PROOF.json'),dispatcher_proof_sha256=sha(S/'DISPATCHER_SOFTWARE_PROOF.json'))
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 result['closed']=True;put(S/'SOURCE_QUALIFICATION.json',result);put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,optimizer_queries=0));print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
