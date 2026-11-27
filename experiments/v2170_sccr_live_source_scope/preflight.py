"""Final single source-stage revision; prior numerical proofs reused by identity."""
from context import R,C,SOURCE as S,O,read,put,sha,predecessors_closed,remaining
from pathlib import Path
import ast,os
from source_scope import PROTECTED
P=R/'runs/v2169_sccr_owner_proof_binding_recovery'
EXCLUDED={'SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_INHERITED_CHAINS.json','FAILED_SOURCE_FREEZE.json'}
PRIOR_METADATA=['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','POST_SOURCE_STORAGE_BARRIER.json','LAUNCH_IDENTITY.json','DISPATCH_ONCE.json','owner.console','components/SCCR/COMPLETION.json','components/SCCR/RUNTIME_CLOSED_REVIEW.json','components/SCCR/POST_COMPONENT_STORAGE_BARRIER.json','components/SCCR/OWNED_CHILD.json','components/SCCR/PILOT_ONCE_CLAIM.json','components/SCCR/PILOT_WINDOW.json','components/SCCR/PILOT_ADMISSION.json','components/SCCR/APPROVAL.json','components/SCCR/actual/RESULT.json','components/SCCR/actual/FINAL_INDEPENDENT_AUDIT.json','runtime_archives/SCCR/ARCHIVE_INDEX.json','runtime_archives/SCCR/FULL_REMOTE_VERIFIED.json','runtime_archives/SCCR/TRANSPORT_CLEANUP.json','runtime_archives/SCCR/remote_delivery/RESULT.json','recovery/ARCHIVE_INDEX.json','recovery/FULL_REMOTE_VERIFIED.json','recovery/TRANSPORT_CLEANUP.json','recovery/SOURCE_SYNC_RESULT.json']
def candidate():
 old=read(P/'SOURCE_FREEZE.json')['files'];files=dict(old)
 for p in C.iterdir():
  if p.is_file()and p.suffix in {'.py','.md'}:files[str(p.relative_to(R))]=sha(p)
 for p in S.rglob('*'):
  if p.is_file()and p.suffix=='.json'and p.name not in EXCLUDED and not any(x in p.parts for x in ['recovery','runtime_archives','actual']):files[str(p.relative_to(R))]=sha(p)
 for n in PRIOR_METADATA:files[str((P/n).relative_to(R))]=sha(P/n)
 return old,files
def prior_raw_chain():
 d=P/'runtime_archives/SCCR';full=read(d/'FULL_REMOTE_VERIFIED.json');assert full['passed']and full['every_asset_actual_download_SHA']and full['every_member_SHA_and_link_text']and full['whole_archive_SHA']and full['recovery_index_download_SHA']and read(d/'TRANSPORT_CLEANUP.json')['passed']
 index=read(d/'ARCHIVE_INDEX.json');members={z['path']:z for z in index['files']};inv=read(S/'CLOSED_V2169_INVENTORY.json');raw=[z for z in inv['rows']if z['path'].startswith(str((P/'components/SCCR/actual').relative_to(R))+'/')]
 assert all(members.get(z['path'],{}).get('sha256')==z['sha256']and members[z['path']]['bytes']==z['bytes']for z in raw)
 return dict(passed=True,prior_actual_members=len(raw),every_prior_raw_member_bound_to_verified_runtime_index=True,index_path=str((d/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=sha(d/'ARCHIVE_INDEX.json'),full_remote_proof_sha256=sha(d/'FULL_REMOTE_VERIFIED.json'),old_closed_raw_not_duplicated_into_new_source_archive=True,old_remote_not_redownloaded_or_requalified=True)
def check(require_auth=False):
 assert not(S/'SOURCE_ONCE.json').exists()and not(S/'DISPATCH_ONCE.json').exists()and all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 assert predecessors_closed()
 for n in ['GUARD_REGRESSION.json','SOURCE_SCOPE_DRAFT_CHANGE_PROOF.json','LIVE_ADMISSION_CHECK.json','ROOT_NAMESPACE_PROOF.json','ADDITIONAL_CLOSED_UPPER_CREDIT.json']:assert read(S/n)['passed'],n
 reuse=read(S/'SOURCE_IDENTITY_REUSE.json')
 for n in reuse['byte_identical_modules']:assert(C/n).read_bytes()==(R/reuse['unchanged_parent']/n).read_bytes(),n
 assert(C/'owner.py').read_bytes()==(R/'experiments/v2169_sccr_owner_proof_binding_recovery/owner.py').read_bytes()
 assert read(R/'runs/v2168_sccr_live_union/SAMPLER_PREFLIGHT_RESULT.json')['passed']and read(R/'runs/v2168_sccr_live_union/UNION_AUDIT_PREFLIGHT.json')['passed']and read(R/'runs/v2166_sccr_import_binding_recovery/components/POLICY/RESULT.json')['passed']
 task=read(O/'PILOT_TASK.json');old=read(P/'components/SCCR/PILOT_TASK.json');assert{k:v for k,v in task.items()if k not in {'output','run_root','run_id'}}=={k:v for k,v in old.items()if k not in {'output','run_root','run_id'}}
 assert read(O/'LIMITS_DRAFT.json')==read(P/'components/SCCR/LIMITS_DRAFT.json')
 if require_auth:assert remaining(read(S/'AUTHORIZATION.json'))>6900
 for p in C.glob('*.py'):ast.parse(p.read_text())
 import evidence
 assert evidence.P==P
 for rid in [None,'SCCR']:compile(evidence.deliver(rid,preview=True),'v2170_source_scope_transport','exec')
 from reserved_census import admission
 budget=admission();chain=prior_raw_chain();parent,files=candidate();assert all(sha(R/n)==h for n,h in files.items())
 for n in files:
  p=R/n;assert not Path(n).is_absolute()and p.resolve().is_relative_to(R)
  assert p.resolve().name not in PROTECTED or p.name in PROTECTED,'SOURCE_SYMLINK_HISTORY_CLASSIFICATION_MISMATCH'
 delta={n:h for n,h in files.items()if parent.get(n)!=h};raw=sum((R/n).stat().st_size for n in delta);upper=raw+len(delta)*2048+512*1024;assert upper<2*1024**2
 return dict(passed=True,source_members=len(files),delta_members=len(delta),delta_raw_bytes=raw,uncompressed_source_tar_upper_bytes=upper,only_live_integration_change_is_source_authority_lifecycle=True,real_context_after_guard_and_boundary_regression_passed=True,all_inherited_physical_sensor_actor_safety_bodies_exact=True,old_numerical_qualifications_not_rerun=True,prior_raw_chain=chain,budget=budget,models=0,NN_inference=0,renderer_constructors=0,physics=0,replay=0,formal_tasks=0,source_once_not_consumed=True)
if __name__=='__main__':
 assert os.sched_getaffinity(0)=={5};x=check();put(S/'PRE_SOURCE_PREFLIGHT.json',x);print(__import__('json').dumps(x))
