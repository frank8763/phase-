"""One literal proof repair; inherited whole software/numerical proofs not rerun."""
from context import R,C,SOURCE as S,O,read,put,sha,predecessors_closed,remaining
from pathlib import Path
import ast,os
P=R/'runs/v2168_sccr_live_union'
EXCLUDED={'SOURCE_ONCE.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_INHERITED_CHAINS.json','FAILED_SOURCE_FREEZE.json'}
def candidate():
 old=read(P/'SOURCE_FREEZE.json')['files'];files=dict(old)
 for p in C.iterdir():
  if p.is_file()and p.suffix in {'.py','.md'}:files[str(p.relative_to(R))]=sha(p)
 for p in S.rglob('*'):
  if p.is_file()and p.suffix=='.json'and p.name not in EXCLUDED and not any(n in p.parts for n in ['recovery','runtime_archives','actual']):files[str(p.relative_to(R))]=sha(p)
 for z in read(S/'CLOSED_V2168_INVENTORY.json')['rows']:assert sha(R/z['path'])==z['sha256'];files[z['path']]=z['sha256']
 return old,files
def check(require_auth=False):
 assert not(S/'SOURCE_ONCE.json').exists()and not(S/'DISPATCH_ONCE.json').exists()and all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 assert predecessors_closed()and read(S/'OWNER_BINDING_REGRESSION.json')['red_old_missing_proof_and_green_corrected_actual_guard']and read(S/'ROOT_NAMESPACE_PROOF.json')['passed']
 proof=read(S/'SOURCE_IDENTITY_REUSE.json')
 for n in proof['byte_identical_modules']:assert(C/n).read_bytes()==(R/proof['unchanged_parent']/n).read_bytes()
 parent=(R/'experiments/v2168_sccr_live_union/owner.py').read_text();assert parent.replace("assert read(SOURCE/'COMPONENT_INTERFACE_PROOF.json')['passed']","assert read(R/'runs/v2168_sccr_live_union/PHYSICAL_SEAM_PROOF.json')['passed']")== (C/'owner.py').read_text()
 for n in ['SAMPLER_PREFLIGHT_RESULT.json','UNION_AUDIT_PREFLIGHT.json','RAY_PROFILE_SOFTWARE_PROOF.json','PHYSICAL_SEAM_PROOF.json','QUOTA_OUTPUT_BOUNDARY_PROOF.json','PUBLIC_ROUTE_PREFLIGHT.json','LAUNCHER_PREFLIGHT.json']:assert read(P/n)['passed']
 assert read(P/'QUOTA_OUTPUT_BOUNDARY_PROOF.json')['minimum_grant_capacity_bytes']-1024**2>(R/'runs/v2144_sccr_depth_resource_units/components/SCCR/actual/DWA_PREDICTIONS.pack').stat().st_size
 a=read(O/'PILOT_TASK.json');old=read(P/'components/SCCR/PILOT_TASK.json')
 assert {k:v for k,v in a.items()if k not in {'output','run_root','run_id'}}=={k:v for k,v in old.items()if k not in {'output','run_root','run_id'}}
 assert read(O/'LIMITS_DRAFT.json')==read(P/'components/SCCR/LIMITS_DRAFT.json')
 if require_auth:assert remaining(read(S/'AUTHORIZATION.json'))>6900
 for p in C.glob('*.py'):ast.parse(p.read_text())
 from reserved_census import admission
 budget=admission();import evidence
 for rid in [None,'SCCR']:compile(evidence.deliver(rid,preview=True),'C2169_transport_scope','exec')
 assert evidence.P==P
 old,files=candidate();assert all(sha(R/n)==h for n,h in files.items());delta={n:h for n,h in files.items()if old.get(n)!=h};raw=sum((R/n).stat().st_size for n in delta)
 assert raw+len(delta)*2048+512*1024<2*1024**2
 return dict(passed=True,models=0,NN_inference=0,renderer_constructors=0,physics=0,replay=0,formal_tasks=0,source_members=len(files),delta_members=len(delta),delta_raw_bytes=raw,source_once_not_consumed=True,original_numerical_sensor_actor_physical_bodies_inherited_by_exact_bytes=True,old_tests_not_reexecuted=True,one_owner_proof_lookup_change=True,new_root_namespace_refusal_checked=True,budget=budget)
if __name__=='__main__':
 assert os.sched_getaffinity(0)=={5};x=check();put(S/'PRE_SOURCE_PREFLIGHT.json',x);print(__import__('json').dumps(x))
