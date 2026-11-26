"""Source-only derivative and actual campaign-state-machine tests, no solvers."""
import ast,copy,fcntl,importlib.abc,json,os,sys,time,types,traceback,subprocess
from pathlib import Path
import evidence as e
R=e.R;C=e.C;S=e.ROOT
def main():
 os.sched_setaffinity(0,{4});O=S/'software';O.mkdir(exist_ok=False)
 result=dict(passed=False,models=0,DLLs=0,solvers=0,physics=0,replay=0)
 try:
  class Ban(importlib.abc.MetaPathFinder):
   def find_spec(self,n,*a):
    if n.split('.')[0]in{'scipy','jax','torch','mujoco','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('SOURCE_SOFTWARE_NO_NUMERICAL_MODELS:'+n)
  sys.meta_path.insert(0,Ban());import numpy as np
  d=e.load('math_source_derivative_validation',C/'nonlinear_development.py')
  x0=[1.4,.1,.3];u=np.linspace(-.2,.2,16);v,j=d.constraint_values_jac(np,u,x0,'PCBF');maximum=0.
  for k in range(16):
   a=u.copy();b=u.copy();a[k]+=1e-6;b[k]-=1e-6;numeric=(d.constraint_values_jac(np,a,x0,'PCBF')[0]-d.constraint_values_jac(np,b,x0,'PCBF')[0])/2e-6;maximum=max(maximum,float(np.max(abs(j[:,k]-numeric))))
  assert maximum<1e-8,'ANALYTIC_JACOBIAN_MISMATCH'
  tests=[]
  for label,technical,cutoff in [('functional_refusal_continues',False,False),('technical_only_vehicle_lane_stops',True,False),('09_clock_stops_new_case',False,True)]:
   F=O/label;F.mkdir();(F/'owner.lock').touch();(F/'POST_SOURCE_STORAGE_BARRIER.json').write_text('{"passed":true}');(F/'SOURCE_FREEZE.json').write_text('{"files":{}}');fake_study=F/'study';(fake_study/'rounds').mkdir(parents=True)
   auth=dict(absolute_end_unix=time.time()+10000,finite_formal_assignments=['common_04__SVGMPPI','common_05__SVGMPPI'])
   (F/'AUTHORIZATION.json').write_text(json.dumps(auth));camp=e.load('actual_campaign_logic_'+label,C/'campaign.py');camp.S=F;camp.STUDY=fake_study;elapsed=[0.];real=time.time
   camp.time=types.SimpleNamespace(time=lambda:real()+elapsed[0],monotonic=time.monotonic,sleep=lambda _:None)
   camp.e=types.SimpleNamespace(read=lambda p:json.loads(Path(p).read_text()),put=lambda p,v:Path(p).write_text(json.dumps(v)),sha=e.sha)
   ran=[];closed=[];summaries=[]
   def process(name,args,cap,env=None,cpu=5,rid=None):
    assert name.endswith('_owner')and args[-1].endswith('owner.py');ran.append(rid);p=fake_study/'rounds'/rid;p.mkdir();(p/'COMPLETION.json').write_text('{"closed":true,"passed":false}')
    if cutoff:elapsed[0]=4000.
    return 1
   camp.run_process=process;camp.component=lambda k:dict(closed=True,passed=False,scope='EXPLICIT_MODEL_FREE_SOFTWARE_FIXTURE',name=k)
   def close(rid,components):
    assert set(components)=={'MATH','EVIDENCE'};closed.append(rid);return dict(round_id=rid,qualified_success=False,valid_finite_method_refusal=not technical,technical_censor=technical,applicability_censor=False)
   camp.close_case=close;camp.checkpoint=lambda *a:None;camp.summary=lambda rows,components,why:summaries.append(dict(rows=rows,components=components,why=why))
   camp.main()
   expected=1 if technical or cutoff else 2;assert len(ran)==len(closed)==expected and len(summaries)==1
   assert len(summaries[0]['components'])==2 and all(x['closed']for x in summaries[0]['components'].values())
   tests.append(dict(name=label,actual_main_invoked=True,owner_calls=len(ran),component_lines_closed_even_on_vehicle_failure=True,reason=summaries[0]['why']))
  # Production native/vehicle/math/evidence entries refuse before numerical imports.
  for script,cpu,expected in [('pilot_entry.py',2,b'NOT_ADMITTED'),('run_phase.py',2,b'NOT_ADMITTED')]:
   p=subprocess.run(['taskset','-c',str(cpu),'/usr/bin/python3','-B',str(C/script)],cwd=R,env=dict(os.environ,PHASE_COMMON_ASSIGNMENT='common_04__SVGMPPI',PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and expected in p.stderr
  ns=e.load('tested_component_namespace',C/'namespace.py')
  for script,cpu,folder,expected in [('math_worker.py',6,'math',b'MATH_ADMISSION.json'),('evidence_worker.py',4,'evidence_lane',b'EVIDENCE_ADMISSION.json')]:
   cmd=ns.command(C/script,S/folder);p=subprocess.run(['taskset','-c',str(cpu),*cmd],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1'),capture_output=True,timeout=15);assert p.returncode!=0 and expected in p.stderr,(script,p.stderr[-1000:])
  # Source scientific modules are reused by byte SHA, no numerical requalification.
  same=[];old=R/'experiments/v2099_svg_direct_array_scope';changed={'context.py','pilot_entry.py','run_phase.py','queue_storage.py','reserved_census.py','reservation.py','evidence.py','software_checks.py','qualify_source.py','owner.py'}
  for p in old.glob('*.py'):
   if p.name not in changed and(C/p.name).exists():assert(C/p.name).read_bytes()==p.read_bytes(),p.name;same.append(p.name)
  assert(C/'owner.py').read_bytes()==(old/'owner.py').read_bytes()
  for p in C.glob('*.py'):ast.parse(p.read_text())
  result.update(passed=True,analytic_jacobian_maximum_difference=maximum,actual_campaign_state_machine_tests=tests,unchanged_numerical_modules=same,original_owner_byte_exact=True,production_unadmitted_refused_before_numerical_import=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:result['closed']=True;e.put(S/'SOFTWARE_CHECK_PROOF.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
