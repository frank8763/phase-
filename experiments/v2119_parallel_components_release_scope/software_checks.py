"""Scalar derivative and real guard negative checks; no optimizer imports."""
import ast,math,os,subprocess,sys,json,traceback
from common import R,C,S,read,put,sha
def main():
 assert os.sched_getaffinity(0)=={4};result=dict(passed=False,models=0,solvers=0,physics=0,replay=0)
 try:
  import bicycle,tracking
  maximum=0.;checks=0
  for gear in[-1,1]:
   for kind in['PSF','PCBF']:
    z=[.06,.2]*8;values,jac=bicycle.values_jac(z,[.2,.1,.3],gear,kind)
    for k in range(16):
     a=z[:];b=z[:];a[k]+=1e-6;b[k]-=1e-6;va=bicycle.values_jac(a,[.2,.1,.3],gear,kind)[0];vb=bicycle.values_jac(b,[.2,.1,.3],gear,kind)[0]
     maximum=max(maximum,max(abs((x-y)/2e-6-j[k])for x,y,j in zip(va,vb,jac)));checks+=len(values)
  assert maximum<1e-8
  # Bernstein straight lines in both gear directions; exact shared command contract.
  contract=__import__('importlib.util',fromlist=['spec_from_file_location']);spec=contract.spec_from_file_location('original_twist_contract',R/'experiments/v1288_baseline_interface/contract.py');m=contract.module_from_spec(spec);spec.loader.exec_module(m)
  for gear in[-1,1]:
   cx=[gear*i*.1 for i in range(11)];cy=[0.]*11;p=tracking.command(cx,cy,body=[.3,0.,0.,0.,0.],gear=gear,receipt_native=0,proposal_native=0);m.twist(*p['request'][:2]);assert abs(p['request'][0]-gear*.08)<1e-12
  negatives=0
  for kwargs in [dict(body=[.3,0.,0.,0.,0.],gear=1,receipt_native=1,proposal_native=0),dict(body=[.4,0.,0.,0.,0.],gear=1,receipt_native=0,proposal_native=0),dict(body=[.3,0.,0.,0.,0.],gear=-1,receipt_native=0,proposal_native=0)]:
   try:tracking.command([i*.1 for i in range(11)],[0.]*11,**kwargs);raise RuntimeError('EXPECTED_TRACKER_REJECTION')
   except AssertionError:negatives+=1
  try:tracking.command([i*.01 for i in range(11)],[i*.1 for i in range(11)],body=[.3,0.,0.,0.,0.],gear=1,receipt_native=0,proposal_native=0);raise RuntimeError('EXPECTED_CURVATURE_REJECTION')
  except AssertionError:negatives+=1
  for script,cpu in [('worker_filters.py',6),('worker_priest.py',4)]:
   p=subprocess.run(['taskset','-c',str(cpu),'/usr/bin/python3','-B',str(C/script)],cwd=R,capture_output=True,timeout=10);assert p.returncode!=0 and b'COMPONENT_ADMISSION.json'in p.stderr
  for p in C.glob('*.py'):ast.parse(p.read_text())
  result.update(passed=True,derivative_scalar_checks=checks,maximum_derivative_error=maximum,tracking_negative_cases=negatives,unadmitted_workers_refused_before_solver=True,original_twist_forward_reverse_satisfied=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 result['closed']=True;put(S/'SOFTWARE_CHECK_PROOF.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
