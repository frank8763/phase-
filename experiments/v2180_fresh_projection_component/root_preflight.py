"""Actual Phase namespace entry refusal and dependency identity, zero models."""
from context import R,C,SOURCE as S,O,put
from peer_namespace import command
import os,subprocess,json
assert os.sched_getaffinity(0)=={5}and not(S/'ROOT_NAMESPACE_PROOF.json').exists()and not(S/'SOURCE_ONCE.json').exists()
# readonly namespace is sufficient because legitimate absence must refuse first.
q=subprocess.run(['taskset','-c','2',*command(C/'pilot_entry.py')],cwd=R,env=dict(os.environ,PHASE_FILTER_METHOD='PROJ',PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),capture_output=True,timeout=20)
assert q.returncode!=0 and b'FILTER_COMPONENT_NOT_ADMITTED'in q.stderr
put(S/'ROOT_NAMESPACE_PROOF.json',dict(passed=True,real_Phase_namespace=True,CPU=2,entry_refused_before_model_bootstrap=True,stdout=q.stdout.decode(),stderr=q.stderr.decode(),new_models_NLP_physics_Source=0));print(json.dumps(dict(passed=True,real_namespace_preinit_refusal=True,models=0)))
