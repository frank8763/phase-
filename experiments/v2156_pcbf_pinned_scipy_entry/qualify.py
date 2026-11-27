"""Once SOURCE for only new fixed mathematical coordinate adapter."""
import ast,os,time,json,traceback,subprocess
from context import R,C,ROOT as S,O,P,read,put,sha

def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(unix=time.time(),models=0,NLP=0));v=dict(passed=False,closed=False,models=0,NLP=0,physics=0,replay=0,formal_tasks=0)
 try:
  old=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in old.items())and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
  assert read(S/'SOFTWARE_PROOF.json')['passed']and read(S/'DEPENDENCY_IMPORT_PROOF.json')['passed']and read(P/'components/MATH/POST_MATH_STORAGE_BARRIER.json')['passed']
  cases=read(S/'CASES_LOCKED.json');assert len(cases['cases'])==6 and cases['maximum_NLP']==12
  for n,h in cases['input_SHA256'].items():assert sha(R/n)==h
  for n in ['common.py','geometry.py','kinematics.py','oracle.py','request.py','filter.py']:assert(C/n).read_bytes()==(R/'experiments/v2141_pcbf_progress_scope'/n).read_bytes()
  assert all(not(O/n).exists()for n in ['NUMERICAL_ADMISSION.json','WORKER_ONCE.json','COMPLETION.json','RESULT.json'])
  # Actual worker CLI cannot import NumPy/SciPy before separate admission.
  q=subprocess.run(['taskset','-c','3','/usr/bin/python3','-B',str(C/'worker.py')],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),capture_output=True,timeout=10)
  assert q.returncode!=0 and b'NUMERICAL_ADMISSION.json'in q.stderr
  from reservation import admission
  reserve=admission();from evidence import deliver
  for rid in [None,'MATH']:compile(deliver(rid,preview=True),'bounded_math_delivery','exec')
  files=dict(old)
  for folder in [C,S]:
   for p in folder.rglob('*'):
    if not p.is_file()or '__pycache__'in p.parts or p.name=='SOURCE_ONCE.json':continue
    if p.suffix=='.py':ast.parse(p.read_text())
    files[str(p.relative_to(R))]=sha(p)
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if old.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  v.update(passed=True,source_members=len(files),delta=len(files)-len(old),original_math_body_byte_exact=True,new_coordinate_transform_only=True,source_CLI_refused_before_numeric=True,reservation=reserve)
 except BaseException as e:v.update(error=repr(e),traceback=traceback.format_exc())
 v['closed']=True;put(S/'SOURCE_QUALIFICATION.json',v);put(S/'SOURCE_OUTER_CLOSED.json',dict(passed=v['passed'],closed=True,models=0,NLP=0));print(json.dumps(v));return 0 if v['passed']else 1
if __name__=='__main__':raise SystemExit(main())
