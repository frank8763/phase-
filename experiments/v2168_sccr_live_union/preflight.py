"""All cheap complete configuration/source/serialization checks before SOURCE."""
from context import R,C,SOURCE as S,O,read,put,sha,predecessors_closed,remaining
from pathlib import Path
import ast,os,subprocess
P=R/'runs/v2166_sccr_import_binding_recovery'
EXCLUDED={'SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_INHERITED_CHAINS.json','FAILED_SOURCE_FREEZE.json'}
def candidate():
 parent=read(P/'SOURCE_FREEZE.json')['files'];files=dict(parent)
 for p in C.iterdir():
  if p.is_file()and p.suffix in {'.py','.md'}:files[str(p.relative_to(R))]=sha(p)
 for p in S.rglob('*'):
  if p.is_file()and not p.is_symlink()and p.suffix=='.json'and p.name not in EXCLUDED and not any(n in p.parts for n in ['recovery','runtime_archives','actual']):files[str(p.relative_to(R))]=sha(p)
 # All closed parent runtime and dispatch evidence is pinned by the new exact
 # closed-increment inventory, never requalified or numerically reevaluated.
 inv=read(S/'CLOSED_V2166_V2167_INVENTORY.json')
 for row in inv['rows']:assert sha(R/row['path'])==row['sha256'];files[row['path']]=row['sha256']
 for root in [R/'experiments/v2167_sccr_control_dispatch']:
  for p in root.iterdir():
   if p.is_file()and p.suffix in {'.py','.md'}:files[str(p.relative_to(R))]=sha(p)
 for p in [R/'experiments/v1370_overnight_controller_matrix/observed_route.py',R/'experiments/v855_renewal_worker/task_planner.py',R/'experiments/v855_renewal_worker/exact_footprint.py']:
  files[str(p.relative_to(R))]=sha(p)
 return parent,files
def check(require_auth=False):
 assert not(S/'SOURCE_ONCE.json').exists()and not(S/'DISPATCH_ONCE.json').exists()
 assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 assert predecessors_closed()and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
 if require_auth:
  a=read(S/'AUTHORIZATION.json');assert remaining(a)>6900 and a['scope']=='SCCR_FRESH_LIVE_UNION_ZERO_ACTUATION_COMPONENT'
 task=read(O/'PILOT_TASK.json');limits=read(O/'LIMITS_DRAFT.json')
 original=next(z['task']for z in read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')['tasks']if z['task']['task_id']=='common_01')
 for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id']:assert task[k]==original[k]
 assert task['scope']=='SCCR_FRESH_LIVE_UNION_ZERO_ACTUATION_COMPONENT'and task['component_not_navigation']and not task['formal_common_task']and task['maximum_control_native']==10 and task['stop_native']==2200
 assert limits['maximum_task_evidence_bytes']==224*1024**2 and limits['storage_limit_bytes']==16106127360 and limits['maximum_actual_native']==limits['maximum_replay_native']==60000 and limits['python_native_cap']==25000000 and limits['cpp_native_cap']==150000000
 for n in ['RAY_PROFILE_SOFTWARE_PROOF.json','CAMERA_ASSEMBLY_PREFLIGHT.json','SAMPLER_PREFLIGHT_RESULT.json','UNION_AUDIT_PREFLIGHT.json','PUBLIC_ROUTE_PREFLIGHT.json','PHYSICAL_SEAM_PROOF.json','BUDGET_PREFLIGHT.json','QUOTA_OUTPUT_BOUNDARY_PROOF.json','LAUNCHER_PREFLIGHT.json','ACTUAL_ALL_RUNS_PRECLAIM_CENSUS.json','software_cli/NAMESPACE_PROBE.json','software_cli/RUN_PHASE_UNADMITTED.json']:assert read(S/n)['passed'],n
 inherited=read(S/'INHERITED_PHYSICAL_FILES_DRAFT.json')
 for n in inherited['files']:assert(C/n).read_bytes()==(R/inherited['parent']/n).read_bytes(),n
 actor_tree=ast.parse((R/'experiments/v2165_sccr_dual_actor_component/actors.py').read_text());assert any(isinstance(n,ast.ClassDef)and n.name=='FrozenActor'for n in actor_tree.body)
 assert "self.authority,self.files=authority()"in(R/'experiments/v2165_sccr_dual_actor_component/actors.py').read_text()
 for p in C.glob('*.py'):ast.parse(p.read_text())
 import evidence
 for rid in [None,'SCCR']:compile(evidence.deliver(rid,preview=True),'C2168_source_bound_transport','exec')
 assert evidence.P==P and evidence.CASES=={'SCCR':'SCCR'}
 from reserved_census import admission
 reserve=admission();parent,files=candidate();assert all(sha(R/n)==h for n,h in files.items())
 delta={n:h for n,h in files.items()if parent.get(n)!=h};raw=sum((R/n).stat().st_size for n in delta)
 # Conservative tar width plus room for not-yet-produced freeze/proof metadata;
 # source archive fits2MiB without any assumed compression discount.
 assert raw+len(delta)*2048+512*1024<2*1024**2,'SOURCE_DELTA_WIDTH_TOO_LARGE'
 return dict(passed=True,models=0,NN_inference=0,renderer_constructors=0,physics=0,replay=0,formal_tasks=0,source_once_not_consumed=True,source_members=len(files),delta_members=len(delta),delta_raw_bytes=raw,delta_source_uncompressed_tar_upper_bytes=raw+len(delta)*2048+512*1024,original_physical_safety_and_stop_gates_unchanged=True,reservation=reserve,all_new_code_AST_parsed=True,all_generated_transport_variants_compiled=True,remaining_NN_render_and_physical_scope_not_yet_executed=True)
if __name__=='__main__':
 assert os.sched_getaffinity(0)=={5};v=check();put(S/'PRE_SOURCE_PREFLIGHT.json',v);print(__import__('json').dumps(v))
