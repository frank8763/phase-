import ast,copy,json,os,subprocess,time,traceback,types
from context import R,C,SOURCE,O,read,put,sha,load
def main():
 assert os.sched_getaffinity(0)=={4};out=SOURCE/'software';result=dict(passed=False,closed=False,models=0,DLLs=0,optimizer_queries=0,physics=0,replay=0)
 try:
  ns=load('current_component_namespace',C/'run_phase.py');cmd=ns.namespace(C/'software_probe.py',out)
  p=subprocess.run(['taskset','-c','4',*cmd],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),capture_output=True,timeout=20);assert p.returncode==0,p.stderr.decode()[-2000:];probe=json.loads(p.stdout)
  # Actual unchanged native client with explicit software peer instead of optimizer.
  client=load('real_PRIEST_client_software',C/'native_client.py');original_read=client.read;original_load=client.load;now=time.time();mono=time.monotonic()
  window=dict(boot_id=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,normal_end_unix=now+4200)
  def fake_read(p):
   if p==O/'PILOT_TASK.json':return dict(output=str(out))
   if p==O/'PILOT_WINDOW.json':return window
   return original_read(p)
  def fake_load(name,p):
   m=original_load(name,p)
   if p==C/'native_namespace.py':
    command=m.command;m.command=lambda script,target:command(C/'software_peer.py',target)
   return m
  client.read=fake_read;client.load=fake_load;P=R/'runs/v2101_parallel_priest_vehicle/vehicle/actual';frame=dict(current=read(P/'PRIEST_CURRENT_INPUT.json'),request=read(P/'PRIEST_OPTIMIZER_REQUEST.json'),explicit_software_fixture=True)
  boundary=load('original_OutputBoundary_software',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');charges=[]
  def debit(p,n):
   assert p.is_relative_to(out.resolve());charges.append(n);assert sum(charges)<=4*1024**2
  with boundary.OutputBoundary(out,debit):answer=client.solve(frame,lambda n,v:put(out/n,v))
  assert answer['explicit_software_fixture']and answer['models']==answer['optimizer_queries']==0
  negative=[]
  for script in ['pilot_entry.py','run_phase.py']:
   p=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(C/script)],cwd=R,env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and b'NOT_ADMITTED'in p.stderr;negative.append(script+'_not_admitted')
  old=R/'experiments/v2101_parallel_priest_vehicle';same=[]
  for name in ['owner.py','driver.py','runtime_binding.py','current_request.py','response.py','capture.py','error_stop.py','work.py','resources.py','native_worker.py','native_client.py','native_namespace.py','input_frame.py','work_budget.py','thread_observation.py','cpu_policy.py','resource_policy.py','base_quota.py','granted_quota.py','quota.py','generic_audit.py','history_binding.py','evidence_service.py','observation.py','audit_budget.py']:
   if name=='driver.py':assert(C/name).read_text()==(old/name).read_text().replace("original_contract=True,weekend_contract_qualified=False","method_identity='PRIEST_POLYNOMIAL_GEOMETRIC_PP_0P6_SPEED_0P08',polynomial_timing_preserved=False,original_contract=True,weekend_contract_qualified=False")
   else:assert(C/name).read_bytes()==(old/name).read_bytes(),name;same.append(name)
  assert(C/'optimizer_call.py').read_text()==(old/'optimizer_call.py').read_text().replace('runs/v2101_parallel_priest_vehicle/vehicle/actual/PRIEST_OPTIMIZER_ADMISSION.json','runs/v2121_priest_geometric_vehicle/vehicle/actual/PRIEST_OPTIMIZER_ADMISSION.json')
  for name in ['navigation.py','audit_component.py']:assert(C/name).read_text()==(old/name).read_text().replace("R/'experiments/v2076_priest_current_control/interface.py'","C/'preview_adapter.py'")
  d=load('actual_wait_dispatcher_software',C/'dispatcher.py');assert d.decision(False,True,False)=='WAIT'and d.decision(True,True,False)=='RUN'and d.decision(True,False,False)=='DEADLINE_STOP'and d.decision(True,True,True)=='USER_STOP'
  for p in C.glob('*.py'):ast.parse(p.read_text())
  result.update(passed=True,preview_phase_runtime_proof=probe,real_native_client_and_readonly_peer=True,client_fixture_charged_bytes=sum(charges),negative_cases=negative,unchanged_low_level_modules=same,driver_only_adds_identity_fields=True,navigation_and_auditor_only_replace_preview_module=True,author_call_only_changes_admission_path=True,dispatcher_wait_run_stop_decisions_verified=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 result['closed']=True;put(SOURCE/'COMPONENT_INTERFACE_PROOF.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
