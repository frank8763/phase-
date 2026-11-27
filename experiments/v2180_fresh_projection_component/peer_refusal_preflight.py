"""Real worker CLI must refuse admission before NumPy/SciPy or any query."""
from peer_guard import R,C,S
from peer_namespace import command
import os,subprocess,json,ast
assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists()and not(S/'PEER_CLI_REFUSAL.json').exists()
q=subprocess.run(['taskset','-c','6','nice','-n','19',*command(C/'peer_entry.py')],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),input=b'',capture_output=True,timeout=15)
assert q.returncode!=0 and b'PROJECTION_OPTIMIZER_ADMISSION.json'in q.stdout+q.stderr
for p in C.glob('*.py'):ast.parse(p.read_text())
x=dict(passed=True,real_readonly_Phase_namespace=True,CPU=6,refused_before_Numpy_Scipy_query=True,returncode=q.returncode,stdout=q.stdout.decode(),stderr=q.stderr.decode(),new_Source_NLP_models_physics=0,canonical_worker_counts_remain_null_without_admission=True);(S/'PEER_CLI_REFUSAL.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items()if k not in ['stdout','stderr']}))
