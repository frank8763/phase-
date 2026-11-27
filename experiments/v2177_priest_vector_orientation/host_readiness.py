"""Real namespace readiness/refusal; no optimizer or model calls."""
from context import R,C,ROOT,O,put
from namespace import command
import os,subprocess,json
assert os.sched_getaffinity(0)=={5}and not(ROOT/'DEPENDENCY_IMPORT_PROOF.json').exists()and not(ROOT/'SOURCE_ONCE.json').exists()
output=ROOT/'dependency_probe_output';output.mkdir(exist_ok=False)
env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
a=subprocess.run(['taskset','-c','3',*command(C/'dependency_probe.py',output)],cwd=R,env=env,capture_output=True,text=True,timeout=60)
if a.returncode:
 put(ROOT/'DEPENDENCY_IMPORT_FAILED.json',dict(passed=False,returncode=a.returncode,stdout=a.stdout,stderr=a.stderr,optimizer_calls=0,models=0));raise AssertionError('REAL_NAMESPACE_IMPORT_READINESS_FAILED')
x=json.loads(a.stdout);assert x['passed']and x['optimizer_calls']==0;put(ROOT/'DEPENDENCY_IMPORT_PROOF.json',x)
b=subprocess.run(['taskset','-c','3',*command(C/'worker.py',output)],cwd=R,env=env,capture_output=True,text=True,timeout=20)
assert b.returncode!=0 and 'NUMERICAL_ADMISSION.json'in b.stderr and not(O/'WORKER_ONCE.json').exists()
put(ROOT/'UNADMITTED_WORKER_REFUSAL.json',dict(passed=True,returncode=b.returncode,stderr=b.stderr,before_Numpy_Scipy_optimizer_import=True,models_NLP_physics=0))
print(json.dumps(dict(passed=True,exact_SciPy_modules=x['imported_exact_SciPy_modules'],actual_namespace=True,unadmitted_worker_refused=True,models_NLP_physics=0)))
