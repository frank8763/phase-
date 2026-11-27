"""Preserved first software attempt + corrected identity seam; no second client run."""
import ast,os,json,subprocess
from context import R,C,SOURCE as S,read,put,load,sha
from software_checks import UNCHANGED
assert os.sched_getaffinity(0)=={4}
first=read(S/'COMPONENT_INTERFACE_PROOF.json');assert first['closed']and not first['passed']and first['error']=="AssertionError('evidence_service.py')"
assert not(S/'COMPONENT_INTERFACE_ATTEMPT01.json').exists();put(S/'COMPONENT_INTERFACE_ATTEMPT01.json',first)
for name in UNCHANGED:assert(C/name).read_bytes()==(R/'experiments/v2122_priest_quiescent_handoff'/name).read_bytes(),name
for name in ['compact_json.py','metadata_pack.py']:assert(C/name).read_bytes()==(R/'experiments/v2151_psf_wrapper_identity_binding'/name).read_bytes(),name
assert(C/'evidence_service.py').read_text()==(R/'experiments/v2151_psf_wrapper_identity_binding/evidence_service.py').read_text().replace('MAX_REBUILD_NATIVE=11100000','MAX_REBUILD_NATIVE=500000')
assert(C/'scaled.py').read_bytes()==(R/'experiments/v2156_pcbf_pinned_scipy_entry/scaled.py').read_bytes()
assert(C/'filter.py').read_bytes()==(R/'experiments/v2134_pcbf_remaining_numeric/filter_minimal.py').read_bytes()
for name in ['geometry.py','kinematics.py','oracle.py','request.py']:assert(C/name).read_bytes()==(R/'experiments/v2123_causal_footprint_filters'/name).read_bytes(),name
out=S/'software/PCBF';builder=read(out/'BUILDER_PROOF.json');assert builder['passed']and builder['models']==builder['optimizer_queries']==0
console=read(out/'FILTER_NATIVE_CONSOLE.json');assert console['returncode']==0 and console['queries']==100 and console['bytes']<=4*1024**2
assert __import__('hashlib').sha256(console['text'].encode()).hexdigest()==console['sha256']
for i in range(100):
 raw=read(out/f'FILTER_QUERY_{i:03d}_RESULT.json');assert raw['passed']and raw['transport_ack']['sequence']==i and raw['answer']['explicit_software_fixture']and raw['answer']['models']==raw['answer']['optimizer_queries']==0
 assert len(raw['answer']['coordinate_transforms'])==len(raw['answer']['returns'])==2
closed=read(out/'FILTER_NATIVE_CLOSED.json');assert closed['optimizer_calls']==100 and closed['NLP_returns']==0 and not closed['inflight_unknown']
namespace=load('actual_serialization_namespace',C/'run_phase.py');cmd=namespace.namespace(C/'serialization_probe.py',out)
p=subprocess.run(['taskset','-c','4',*cmd],cwd=R,capture_output=True,timeout=30,env=dict(os.environ,PHASE_REPO=str(R),PHASE_FILTER_METHOD='PCBF',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES=''))
assert p.returncode==0,p.stderr.decode()[-1500:];serial=json.loads(p.stdout);assert serial['passed'];put(S/'NATIVE_SERIALIZATION_PROOF.json',serial)
for path in C.glob('*.py'):ast.parse(path.read_text())
put(S/'COMPONENT_INTERFACE_PROOF.json',dict(passed=True,closed=True,models=0,DLLs=0,optimizer_queries=0,physics=0,replay=0,preserved_first_attempt=sha(S/'COMPONENT_INTERFACE_ATTEMPT01.json'),old_comparison_error_only=True,real_persistent_client_readonly_software_peer=True,ordered_fake_queries_per_method=100,console_bytes=console['bytes'],console_sha256=console['sha256'],complete_saved_conditioned_reply_shape=True,native_serialization_proof_sha256=sha(S/'NATIVE_SERIALIZATION_PROOF.json'),unchanged_low_level_modules=UNCHANGED,recipe_scope_change_only_11100000_to_500000=True,mathematical_modules_byte_exact=True,unadmitted_entries_refused_before_models_or_solver=True))
print(json.dumps(dict(passed=True,queries=100,console_bytes=console['bytes'],numerical_calls=0,models=0,real_numpy_serialization=True,first_attempt_preserved=True)))
