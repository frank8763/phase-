"""Zero-optimizer qualification before once numerical comparison."""
import os,ast,json,time,traceback,subprocess
from common import R,C,S,read,put,sha,load

def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(unix=time.time(),models=0,solvers=0));result=dict(passed=False,closed=False,models=0,solvers=0,physics=0,replay=0,formal_tasks=0)
 try:
  P=R/'runs/v2131_filter_measured_current';prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items())and read(P/'DISPATCH_RESULT.json')['finite_queue_completed']
  for method in ['PSF','PCBF']:assert read(P/'components'/method/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']
  assert(C/'filter_original.py').read_bytes()==(R/'experiments/v2131_filter_measured_current/filter.py').read_bytes()
  original=(C/'filter_original.py').read_text();minimal=(C/'filter_minimal.py').read_text();assert minimal==original.replace('np.maximum(initial,0.)+.01','np.maximum(initial,0.)')and original.count('np.maximum(initial,0.)+.01')==1
  for n in ['geometry.py','oracle.py','kinematics.py']:assert(C/n).read_bytes()==(R/'experiments/v2131_filter_measured_current'/n).read_bytes()
  cases=read(S/'CASES_LOCKED.json');assert len(cases['cases'])==5 and cases['maximum_NLP_returns']==20
  reserve=load('finite_component_subgrant',C/'reservation.py').admission();files=dict(prior)
  for row in cases['cases']:
   if row.get('input_path'):
    p=R/row['input_path'];frame=read(p);assert frame['request']['case']==row['case']and frame['request']['public_known']==row['known'];files[str(p.relative_to(R))]=sha(p)
  for folder in[C,S,R/'experiments/v2132_remaining_method_qualification',R/'runs/v2132_remaining_method_qualification']:
   for p in folder.iterdir():
    if p.is_file()and p.suffix not in{'.log','.console'}and p.name not in{'SOURCE_ONCE.json','owner.lock'}:
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  from evidence import deliver
  for rid in[None,'components']:compile(deliver(rid,preview=True),str(C/'generated_transport.py'),'exec')
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B',str(C/'worker.py')],cwd=R,capture_output=True,timeout=10);assert p.returncode!=0 and b'COMPONENT_ADMISSION.json'in p.stderr
  assert all(sha(R/n)==h for n,h in files.items())
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),delta_members=len(files)-len(prior),single_initialization_line_difference=True,unchanged_NLP_objectives_derivatives_bounds_tolerances=True,all_generated_transport_compiled=True,unadmitted_numerical_entry_denied=True,reservation=reserve)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 result['closed']=True;put(S/'SOURCE_QUALIFICATION.json',result);put(S/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,solvers=0));print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
