"""Validate existing closure chain proofs only; no HTTP, replay or old audit."""
from pathlib import Path
import os,json,hashlib,datetime
R=Path(__file__).resolve().parents[2];S=R/'runs/v2172_closed_capacity_accounting'
assert os.sched_getaffinity(0)=={5} and not(S/'CLOSURE_CHAIN_CHECK.json').exists()
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(S/'RESULT.json');assert r['passed'];proofs=[]
for root,methods in [('v2131_filter_measured_current',['PSF','PCBF']),('v2144_sccr_depth_resource_units',['SCCR']),('v2170_sccr_live_source_scope',['SCCR'])]:
 for method in methods:
  s=R/'runs'/root;barrier=s/'components'/method/'POST_COMPONENT_STORAGE_BARRIER.json';b=read(barrier)
  d=s/'runtime_archives'/method;remote=d/'FULL_REMOTE_VERIFIED.json';cleanup=d/'TRANSPORT_CLEANUP.json'
  assert b['passed'] and read(remote)['passed'] and read(cleanup)['passed']
  if 'runtime_proof_sha256' in b:assert sha(remote)==b['runtime_proof_sha256']
  else:
   assert sha(remote)==b['full_remote_sha256'] and sha(cleanup)==b['cleanup_sha256']
   assert sha(R/b['index_path'])==b['index_sha256']
  remoteproof=read(remote)
  for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA']:
   if k in remoteproof:assert remoteproof[k]
  proofs.append(dict(root=root,method=method,barrier_sha256=sha(barrier),remote_proof_path=str(remote.relative_to(R)),
                     remote_proof_sha256=sha(remote),cleanup_proof_path=str(cleanup.relative_to(R)),cleanup_proof_sha256=sha(cleanup)))
x=dict(passed=True,created_at=datetime.datetime.now().astimezone().isoformat(),accounting_result_sha256=sha(S/'RESULT.json'),proofs=proofs,
       actual_remote_proofs_verified_at_original_delivery_not_redownloaded_now=True,no_new_HTTP_push_archive_model_replay_audit=True)
(S/'CLOSURE_CHAIN_CHECK.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'passed':True,'closed_runtime_chains':len(proofs)}))
