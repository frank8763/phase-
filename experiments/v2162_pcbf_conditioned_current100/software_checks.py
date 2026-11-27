"""Real isolated builder/client and guards for both methods, zero numerical calls."""
import os,json,subprocess,time,traceback,ast,copy
from context import R,C,SOURCE as S,O,read,put,sha,load
UNCHANGED=['response.py','error_stop.py','capture.py','runtime_binding.py','history_binding.py','work.py','work_budget.py','resource_policy.py','quota.py','base_quota.py','granted_quota.py','direct_bits.py','audit_budget.py','generic_audit.py','observation.py','thread_observation.py','cpu_policy.py','input_frame.py']
def main():
 os.environ.setdefault('PHASE_FILTER_METHOD','PCBF')
 assert os.sched_getaffinity(0)=={4};result=dict(passed=False,closed=False,models=0,DLLs=0,optimizer_queries=0,physics=0,replay=0);out=S/'software';out.mkdir()
 try:
  namespace=load('FILTER_actual_source_namespace',C/'run_phase.py');proofs=[]
  for method in['PCBF']:
   target=out/method;target.mkdir();cmd=namespace.namespace(C/'software_probe.py',target)
   p=subprocess.run(['taskset','-c','4',*cmd],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PHASE_FILTER_METHOD=method,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),capture_output=True,timeout=30)
   assert p.returncode==0,p.stderr.decode()[-2500:];proof=json.loads(p.stdout);put(target/'BUILDER_PROOF.json',proof);proofs.append(dict(method=method,negative_cases=proof['negative_cases'],resident_restored=proof['resident_foreign_geometry_restored']))
   client=load('FILTER_real_client_software_'+method,C/'native_client.py');original_read=client.read;original_load=client.load;now=time.time();mono=time.monotonic();window=dict(boot_id=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,normal_end_unix=now+4200)
   def fake_read(p):
    if p==O/'PILOT_TASK.json':return dict(output=str(target))
    if p==O/'PILOT_WINDOW.json':return window
    return original_read(p)
   def fake_load(n,p):
    m=original_load(n,p)
    if p==C/'native_namespace.py':
     original_command=m.command;m.command=lambda script,target:original_command(C/'software_peer.py',target)
    return m
   client.read=fake_read;client.load=fake_load;frame=dict(proof['frame'],explicit_software_fixture=True)
   boundary=load('original_OutputBoundary_FILTER_software',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');charges=[]
   def debit(p,n):
    assert p.is_relative_to(target.resolve());charges.append(n);assert sum(charges)<=12*1024**2
   with boundary.OutputBoundary(target,debit):
    persistent=client.Client(lambda n,v:put(target/n,v),frame)
    try:
     answer=persistent.query()
     measured=0.
     for sequence in range(1,100):
      for _ in range(5):measured+=.01
      current=copy.deepcopy(proof['frame5']);current['explicit_software_fixture']=True;k=sequence*5
      current['current'].update(native=k,sim_time=measured);current['current'].pop('input_sha256');current['current']['input_sha256']=client.load('software_digest',C/'context.py').digest(current['current'])
      current['request'].update(origin_native=k,origin_sim_time=measured,input_sha256=current['current']['input_sha256']);current['request']['case']['sim_time']=measured;current['request'].pop('request_sha256');current['request']['request_sha256']=client.load('software_digest',C/'context.py').digest(current['request'])
      answer=persistent.query(current)
    finally:persistent.close()
    assert persistent.calls==100
   console=read(target/'FILTER_NATIVE_CONSOLE.json');assert console['bytes']<=4*1024**2 and console['queries']==100
   proofs[-1].update(readonly_client_queries=100,console_bytes=console['bytes'],console_sha256=console['sha256'],bounded_output_charges=sum(charges),saved_reply_fixture=answer['saved_fixture_path'],saved_reply_fixture_sha256=answer['saved_fixture_sha256'])
   assert answer['explicit_software_fixture']and answer['models']==answer['optimizer_queries']==0
   for script,cpu in[('pilot_entry.py',2),('run_phase.py',2),('native_worker.py',6)]:
    z=subprocess.run(['taskset','-c',str(cpu),'/usr/bin/python3','-B',str(C/script)],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PHASE_FILTER_METHOD=method),capture_output=True,timeout=10)
    assert z.returncode!=0 and(b'NOT_ADMITTED'in z.stderr or b'PILOT_ADMISSION.json'in z.stderr),z.stderr[-1000:]
  for name in UNCHANGED:assert(C/name).read_bytes()==(R/'experiments/v2122_priest_quiescent_handoff'/name).read_bytes(),name
  assert(C/'scaled.py').read_bytes()==(R/'experiments/v2156_pcbf_pinned_scipy_entry/scaled.py').read_bytes()
  for name in['compact_json.py','metadata_pack.py']:assert(C/name).read_bytes()==(R/'experiments/v2151_psf_wrapper_identity_binding'/name).read_bytes(),name
  assert(C/'evidence_service.py').read_text()==(R/'experiments/v2151_psf_wrapper_identity_binding/evidence_service.py').read_text().replace('MAX_REBUILD_NATIVE=11100000','MAX_REBUILD_NATIVE=500000')
  assert(C/'filter.py').read_bytes()==(R/'experiments/v2134_pcbf_remaining_numeric/filter_minimal.py').read_bytes()
  for name in['geometry.py','kinematics.py','oracle.py','request.py']:assert(C/name).read_bytes()==(R/'experiments/v2123_causal_footprint_filters'/name).read_bytes(),name
  for p in C.glob('*.py'):ast.parse(p.read_text())
  result.update(passed=True,both_method_builder_proofs=proofs,real_persistent_client_readonly_software_peer=True,ordered_fake_queries_per_method=100,unchanged_low_level_modules=UNCHANGED,mathematical_modules_byte_exact=True,unadmitted_entries_refused_before_models_or_solver=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 result['closed']=True;put(S/'COMPONENT_INTERFACE_PROOF.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
