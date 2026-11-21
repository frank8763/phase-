"""Reuse the new exact nested namespace target and numerical AST identities."""
import ast
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def qualify():
 q=R/'runs/v1503_priest_namespace_observation';result=json.loads((q/'QUALIFICATION.json').read_text());freeze=json.loads((q/'SOURCE_FREEZE.json').read_text());assert result['passed']and result['closed']and all(sha(R/n)==h for n,h in freeze['files'].items())
 nested=json.loads((q/'NESTED_RESULT.json').read_text());assert nested['passed']and nested['JAX_author_imported']is False and nested['all_target_helpers_joined']
 assert all(v['affinity']==[4]for v in nested['observation']['observed'].values())and nested['actual_namespace_thread_ids']==[3,4]
 old=R/'experiments/v1500_priest_thread_observation'
 for name in ['common.py','sandbox.py']:assert(C/name).read_bytes()==(old/name).read_bytes()
 for name in ['kernel_loader.py','optimizer_call.py']:
  expected=(old/name).read_text().replace('runs/v1500_priest_thread_observation/OPTIMIZER_ONLY_ADMISSION.json','runs/v1504_priest_namespace_worker/OPTIMIZER_ONLY_ADMISSION.json')
  assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((C/name).read_text()))
 expected=(old/'inner.py').read_text().replace("C/'thread_observation.py'","R/'experiments/v1503_priest_namespace_observation/thread_observation.py'")
 assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((C/'inner.py').read_text()))
 proof=dict(passed=True,scope='NAMESPACE_WORKER_SOURCE_BINDING_ONLY',exact_nested_target_reused_not_reexecuted=True,original_nested_qualification_sha256=sha(q/'QUALIFICATION.json'),original_nested_result_sha256=sha(q/'NESTED_RESULT.json'),namespace_source_freeze_sha256=sha(q/'SOURCE_FREEZE.json'),inner_AST_exact_except_observer_source=True,numerical_callgraph_AST_exact_except_admission_path=True,old_V1498_V1500_failed_immutable=True,models=0,optimizer_calls=0,JAX_author_imported=False)
 (O/'NAMESPACE_BINDING_REUSE.json').write_text(json.dumps(proof,indent=2,allow_nan=False)+'\n');return proof
