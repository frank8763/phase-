"""Actual serializer and static production seams, zero model constructors."""
from context import R,C,SOURCE as S,O,read,put,load,sha
from pathlib import Path
import ast,json,os
assert os.sched_getaffinity(0)=={0}and not(S/'PREFREEZE_CHEAP_INTERFACE_PROOF.json').exists()
import numpy as np
parent=R/'experiments/v2170_sccr_live_source_scope'
# The only frozen-actor authority change is a literal task-scope binding;
# architecture, original AST backend and dependency pins remain byte identical.
p=(C/'policy.py').read_text();old=(parent/'policy.py').read_text();assert p==old.replace('SCCR_FRESH_LIVE_UNION_ZERO_ACTUATION_COMPONENT','SCCR_CP_SHARED_ROUTE_NONZERO_COMPONENT')
ctx=ast.parse((C/'context.py').read_text());prior=ast.parse((parent/'context.py').read_text())
fn=lambda t,n:next(x for x in t.body if isinstance(x,ast.FunctionDef)and x.name==n)
assert ast.dump(fn(ctx,'admission'),include_attributes=False)==ast.dump(fn(prior,'admission'),include_attributes=False)
assert(C/'source_scope.py').read_bytes()==(parent/'source_scope.py').read_bytes()and(C/'history_binding.py').read_bytes()==(parent/'history_binding.py').read_bytes()
assert read(R/'runs/v2170_sccr_live_source_scope/GUARD_REGRESSION.json')['passed']and read(R/'runs/v2170_sccr_live_source_scope/LIVE_ADMISSION_CHECK.json')['passed']
assert(C/'owner.py').read_bytes()==(parent/'owner.py').read_bytes()
for n in ['runs/v2168_sccr_live_union/PHYSICAL_SEAM_PROOF.json','runs/v2090_svg_persistent_counter_fixture/COMPLETION.json']:assert read(R/n)['passed']
assert read(S/'LAUNCHER_PREFLIGHT.json')['passed']and read(S/'ROOT_NAMESPACE_PROOF.json')['passed']
nav=ast.parse((C/'navigation.py').read_text());prove=next(x for x in ast.walk(nav)if isinstance(x,ast.FunctionDef)and x.name=='proof')
methods={x.func.attr for x in ast.walk(prove)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)};assert 'persist'in methods and 'store'not in methods and 'current'not in methods
service=ast.parse((C/'evidence_service.py').read_text());assert any(isinstance(x,ast.FunctionDef)and x.name=='persist'for x in ast.walk(service))
assert any(isinstance(x,ast.keyword)and x.arg=='receipt'for x in ast.walk(prove))
atomic=load('SCCR_CP_exact_production_JSON',C/'compact_json.py').atomic;folder=S/'software_serialization';folder.mkdir(exist_ok=False)
value={'proposal_memory':read(R/'runs/v2175_sccr_persistent_controller/RESULT.json')['committed_memory'],'numpy':{'bool':np.bool_(True),'float':np.float32(.1),'integer':np.int64(5),'array':np.array([.1,.2])},'none':None}
f=folder/'SOURCE_EXPLICIT_SERIALIZER_FIXTURE.json';atomic(f,value);decoded=read(f);assert decoded['numpy']['bool']is True and decoded['numpy']['integer']==5
try:atomic(folder/'INVALID_NONFINITE.json',dict(nonfinite=float('nan')))
except ValueError:pass
else:raise AssertionError('NONFINITE_SERIALIZATION_ACCEPTED')
assert not(folder/'INVALID_NONFINITE.json').exists()
# New actual runtime helpers can be imported in the normal isolated CPU2
# environment later; all current imported modules remain pure data/software.
assert 'torch'not in __import__('sys').modules and 'mujoco'not in __import__('sys').modules
x=dict(passed=True,closed=True,scope='CHEAP_REAL_SERIALIZER_AND_EXACT_SOURCE_CONFIG_API_SEAMS',
 actor_network_backend_unchanged_only_authority_scope_literal_changed=True,source_context_admission_and_history_guard_bodies_exact=True,
 actual_preinitializer_and_guard_lifecycle_proofs_reused_by_byte_identity=True,new_root_refusal_still_precedes_policy_scope_literal=True,
 original_owner_body_literal_dependency_paths_present=True,actual_persist_API_and_receipt_keyword_verified=True,
 original_serializer_numpy_bool_float_integer_array_and_finite_negative_passed=True,
 old_network_and_numerical_qualifications_NOT_rerun=True,models_NN_render_physics_replay_source_claims=0,
 source_sha256={str(q.relative_to(R)):sha(q)for q in [C/'context.py',C/'policy.py',C/'navigation.py',C/'owner.py',C/'compact_json.py',Path(__file__)]})
put(S/'PREFREEZE_CHEAP_INTERFACE_PROOF.json',x);print(json.dumps({k:v for k,v in x.items()if k!='source_sha256'}))
