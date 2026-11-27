"""New substantive SCCR-CP integration; all cheap checks BEFORE Source once."""
from context import R,C,SOURCE as S,O,read,put,sha,predecessors_closed,remaining
from pathlib import Path
import ast,os,json
P=R/'runs/v2170_sccr_live_source_scope'
EXCLUDED={'SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_INHERITED_CHAINS.json','FAILED_SOURCE_FREEZE.json'}
PRIOR_METADATA=['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','POST_SOURCE_STORAGE_BARRIER.json','LAUNCH_IDENTITY.json','DISPATCH_ONCE.json','owner.console','components/SCCR/COMPLETION.json','components/SCCR/RUNTIME_CLOSED_REVIEW.json','components/SCCR/POST_COMPONENT_STORAGE_BARRIER.json','components/SCCR/OWNED_CHILD.json','components/SCCR/PILOT_ONCE_CLAIM.json','components/SCCR/PILOT_WINDOW.json','components/SCCR/PILOT_ADMISSION.json','components/SCCR/actual/RESULT.json','components/SCCR/actual/FINAL_INDEPENDENT_AUDIT.json','runtime_archives/SCCR/ARCHIVE_INDEX.json','runtime_archives/SCCR/FULL_REMOTE_VERIFIED.json','runtime_archives/SCCR/TRANSPORT_CLEANUP.json','recovery/ARCHIVE_INDEX.json','recovery/FULL_REMOTE_VERIFIED.json','recovery/TRANSPORT_CLEANUP.json','recovery/SOURCE_SYNC_RESULT.json']
SUPPORT=['v2171_sccr_control_contract_readout','v2172_closed_capacity_accounting','v2173_sccr_inner_control_readout','v2174_shared_virtual_command_domain','v2175_sccr_persistent_controller']
def candidate():
 old=read(P/'SOURCE_FREEZE.json')['files'];files=dict(old)
 for folder in [C]+[R/'experiments'/n for n in SUPPORT]:
  for p in folder.iterdir():
   if p.is_file()and p.suffix in{'.py','.md'}:files[str(p.relative_to(R))]=sha(p)
 for folder in [S]+[R/'runs'/n for n in SUPPORT]:
  for p in folder.rglob('*.json'):
   if p.name not in EXCLUDED and not any(x in p.parts for x in ['recovery','runtime_archives','actual']):files[str(p.relative_to(R))]=sha(p)
 for n in PRIOR_METADATA:files[str((P/n).relative_to(R))]=sha(P/n)
 for n in ['docs/SCCR_CONTROL_CONTRACT_V2171_REPORT.md','docs/SCCR_INNER_CONTROL_V2173_V2174_REPORT.md']:files[n]=sha(R/n)
 return old,files

def prior_raw_chain():
 d=P/'runtime_archives/SCCR';full=read(d/'FULL_REMOTE_VERIFIED.json');assert full['passed']and full['every_asset_actual_download_SHA']and full['every_member_SHA_and_link_text']and full['whole_archive_SHA']and full['recovery_index_download_SHA']and read(d/'TRANSPORT_CLEANUP.json')['passed']
 index=read(d/'ARCHIVE_INDEX.json');members={z['path']:z for z in index['files']};capacity=read(R/'runs/v2172_closed_capacity_accounting/RESULT.json');inventory=R/capacity['newest_closed_inventory_path'];assert sha(inventory)==capacity['newest_closed_inventory_sha256']
 raw=[z for z in read(inventory)['rows']if z['path'].startswith(str((P/'components/SCCR/actual').relative_to(R))+'/')]
 assert all(members.get(z['path'],{}).get('sha256')==z['sha256']and members[z['path']]['bytes']==z['bytes']for z in raw if z.get('kind')!='symlink_not_followed')
 return dict(passed=True,prior_actual_members=len(raw),every_prior_raw_member_bound_to_verified_runtime_index=True,index_sha256=sha(d/'ARCHIVE_INDEX.json'),full_remote_proof_sha256=sha(d/'FULL_REMOTE_VERIFIED.json'),old_raw_not_duplicated_into_new_source_archive=True)

def check(require_auth=False):
 assert not(S/'SOURCE_ONCE.json').exists()and not(S/'DISPATCH_ONCE.json').exists()and all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 assert predecessors_closed()
 names=['SAMPLER_PREFLIGHT_RESULT.json','UNION_AUDIT_PREFLIGHT.json','NAVIGATION_PREFLIGHT.json','CONTROL_AUDIT_PREFLIGHT.json','ROOT_NAMESPACE_PROOF.json','EXACT_CAPACITY_PREFLIGHT.json','PREFREEZE_CHEAP_INTERFACE_PROOF.json']
 for n in names:assert read(S/n)['passed'],n
 for n in SUPPORT:
  assert read(R/'runs'/n/'RESULT.json')['passed']
 assert read(R/'runs/v2174_shared_virtual_command_domain/FINITE_TRACE_SUPPLEMENT.json')['passed']
 assert read(R/'runs/v2166_sccr_import_binding_recovery/components/POLICY/RESULT.json')['passed']
 parent_code=R/'experiments/v2170_sccr_live_source_scope';changed=[];identical=[]
 for p in parent_code.glob('*.py'):
  if(C/p.name).exists():(identical if(C/p.name).read_bytes()==p.read_bytes()else changed).append(p.name)
 for n in ['response.py','runtime_binding.py','resources.py','capture.py','work.py','depth.py','assemble.py','union_features.py','private_snapshot.py','history_binding.py','source_scope.py','generic_audit.py','owner.py','pilot_entry.py','run_phase.py','evidence_service.py']:
  assert n in identical,('INHERITED_NUMERICAL_OR_SAFETY_BODY_CHANGED',n)
 assert(C/'policy.py').read_text()==(parent_code/'policy.py').read_text().replace('SCCR_FRESH_LIVE_UNION_ZERO_ACTUATION_COMPONENT','SCCR_CP_SHARED_ROUTE_NONZERO_COMPONENT'),'ONLY_ACTOR_AUTHORITY_SCOPE_STRING_MAY_CHANGE'
 task=read(O/'PILOT_TASK.json');registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']=='common_01')
 for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id']:assert task[k]==original[k]
 assert task['method']=='SCCR_CP_SHARED_ROUTE_V1'and task['component_not_navigation']and task['maximum_control_native']==10 and task['stop_native']==2200 and not task['formal_common_task']
 assert read(O/'LIMITS_DRAFT.json')==read(P/'components/SCCR/LIMITS_DRAFT.json')
 if require_auth:assert remaining(read(S/'AUTHORIZATION.json'))>6900
 for p in C.glob('*.py'):ast.parse(p.read_text())
 import evidence
 assert evidence.P==P
 for rid in [None,'SCCR']:compile(evidence.deliver(rid,preview=True),'new_SCCR_CP_delivery','exec')
 from reserved_census import admission
 budget=admission();chain=prior_raw_chain();parent,files=candidate();assert all(sha(R/n)==h for n,h in files.items())
 delta={n:h for n,h in files.items()if parent.get(n)!=h};raw=sum((R/n).stat().st_size for n in delta);upper=raw+len(delta)*2048+512*1024;assert upper<2*1024**2,('SOURCE_TAR_BOUND',upper)
 return dict(passed=True,source_members=len(files),delta_members=len(delta),delta_raw_bytes=raw,uncompressed_source_tar_upper_bytes=upper,byte_identical_inherited_modules=identical,changed_modules=changed,all_inherited_physical_sensor_actor_safety_bodies_exact=True,old_numerical_qualifications_not_rerun=True,prior_raw_chain=chain,budget=budget,models=0,NN_inference=0,renderer_constructors=0,physics=0,replay=0,formal_tasks=0,source_once_not_consumed=True)
if __name__=='__main__':
 assert os.sched_getaffinity(0)=={5};x=check();put(S/'PRE_SOURCE_PREFLIGHT.json',x);print(json.dumps(x))
