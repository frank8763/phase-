"""One zero-model qualification for actual shared-depth acquisition."""
import ast,os,time,json,traceback
from context import R,C,SOURCE as S,read,put,sha,predecessors_closed
def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0,actual_renderers=0));r=dict(passed=False,closed=False,models=0,actual_renderers=0,policy_calls=0,optimizer_queries=0,physics=0,replay=0,formal_tasks=0)
 try:
  P=R/'runs/v2141_pcbf_progress_scope';prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items())and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];predecessors_closed()
  proof=read(S/'COMPONENT_INTERFACE_PROOF.json');assert proof['passed']and proof['models']==proof['actual_renderers']==proof['optimizer_queries']==0
  for n in proof['unchanged_original_physical_modules']:assert(C/n).read_bytes()==(R/'experiments/v2141_pcbf_progress_scope'/n).read_bytes(),n
  task=read(S/'components/SCCR/PILOT_TASK.json');original=next(z['task']for z in read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')['tasks']if z['task']['task_id']=='common_01')
  for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id']:assert task[k]==original[k]
  assert task['maximum_control_native']==10 and task['stop_native']==2200 and task['component_not_navigation']and not task['formal_common_task']
  for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual']:assert not(S/'components/SCCR'/n).exists()
  from reserved_census import admission
  reserve=admission();files=dict(prior)
  for folder in [C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.suffix not in {'.log','.console'}and p.name not in {'SOURCE_ONCE.json','dispatcher.lock'}:
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for folder in [S/'components',S/'software']:
   for p in folder.rglob('*.json'):files[str(p.relative_to(R))]=sha(p)
  for p in [R/'runtime/mk-mini/training/envs/mkmini_real_indoor_phase3_depth_astar_sac_env.py',R/'runs/v2138_sccr_complete_sensor_inventory/CAMERA_BINDING_SUPPLEMENT.json']:
   files[str(p.relative_to(R))]=sha(p)
  from evidence import deliver
  for rid in [None,'SCCR']:compile(deliver(rid,preview=True),str(C/'generated_transport.py'),'exec')
  assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  r.update(passed=True,source_members=len(files),delta_members=len(files)-len(prior),fixed_components=['SCCR'],scope='ACTUAL_DEPTH_ACQUISITION_NOT_POLICY_OR_NAVIGATION',reservation=reserve,original_physical_modules_unchanged=True,software_proof_sha256=sha(S/'COMPONENT_INTERFACE_PROOF.json'))
 except BaseException as e:r.update(error=repr(e),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 r['closed']=True;put(S/'SOURCE_QUALIFICATION.json',r);put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=r['passed'],models=0,actual_renderers=0));print(json.dumps(r));return 0 if r['passed']else 1
if __name__=='__main__':raise SystemExit(main())
