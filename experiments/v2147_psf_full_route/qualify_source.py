"""One zero-model source qualification for the new full-route/evidence wrapper."""
import ast,os,time,json,traceback,subprocess
from pathlib import Path
from context import R,C,SOURCE as S,read,put,sha,predecessors_closed
PHYSICAL=['response.py','error_stop.py','capture.py','runtime_binding.py','history_binding.py','work.py','work_budget.py','resource_policy.py','quota.py','base_quota.py','granted_quota.py','direct_bits.py','audit_budget.py','generic_audit.py','observation.py','thread_observation.py','cpu_policy.py','input_frame.py']
MATH=['filter.py','geometry.py','kinematics.py','oracle.py','request.py','nominal.py']
def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0,NLP=0));v=dict(passed=False,closed=False,models=0,NLP=0,physics=0,replay=0,formal_tasks=0)
 try:
  predecessors_closed();P=R/'runs/v2145_verified_whole_transport_recovery';old=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in old.items())and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
  for n in ['COMPONENT_INTERFACE_PROOF.json','PERSISTENT_PROTOCOL_PROOF.json','MEASURED_CLOCK_REGRESSION.json','PACK_SOFTWARE_PROOF.json','FULL_ROUTE_SOFTWARE_FLOW.json','FULL_ROUTE_VALIDATOR_PROOF.json','EXACT_RECIPE_SOFTWARE_PROOF.json','DISPATCHER_SOFTWARE_PROOF.json']:assert read(S/n)['passed'],n
  for n in PHYSICAL+MATH:assert(C/n).read_bytes()==(R/'experiments/v2137_psf_progress_control'/n).read_bytes(),n
  obs=read(S/'FULL_ROUTE_SOFTWARE_FLOW.json');assert len(obs['cases'])==8 and obs['models']==obs['NLP_queries']==0
  assert read(S/'COMPONENT_INTERFACE_PROOF.json')['ordered_fake_queries_per_method']==2500
  assert read(S/'EXACT_RECIPE_SOFTWARE_PROOF.json')['bitwise_uint64_equal']
  registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']=='common_01');O=S/'components/PSF';t=read(O/'PILOT_TASK.json')
  for key in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id']:assert t[key]==original[key]
  assert not t['component_not_navigation']and t['exposed_full_route_development']and not t['formal_common_task']and t['maximum_current_native_queries']==2500 and t['maximum_plans']==12 and t['stop_native']==2200
  assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])
  from reserved_census import admission
  reserve=admission();from evidence import deliver
  for rid in [None,'PSF']:compile(deliver(rid,preview=True),'full_route_transport','exec')
  measured=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],timeout=20).split()[0]);b=read(S/'BASELINE_DRAFT.json');assert measured<=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['metadata_bytes']
  files=dict(old)
  for folder in [C,S]:
   for p in folder.rglob('*'):
    if not p.is_file()or '__pycache__'in p.parts or p.name in ['SOURCE_ONCE.json']:continue
    assert not p.is_symlink()
    if p.suffix=='.py':ast.parse(p.read_text())
    files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if old.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  v.update(passed=True,source_members=len(files),delta_members=len(files)-len(old),fixed_order=['PSF'],scope='EXPOSED_FULL_ROUTE_DEVELOPMENT_NOT_FORMAL',physical_and_math_modules_byte_exact=True,software_ordered_queries=2500,flow_cases=8,live_exact_reconstruction_canary_still_required=True,reservation=reserve,measured_allruns_before_source=measured)
 except BaseException as e:v.update(error=repr(e),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 v['closed']=True;put(S/'SOURCE_QUALIFICATION.json',v);put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=v['passed'],models=0,NLP=0));print(json.dumps(v));return 0 if v['passed']else 1
if __name__=='__main__':raise SystemExit(main())
