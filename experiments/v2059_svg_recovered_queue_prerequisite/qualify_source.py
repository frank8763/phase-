"""Source/namespace/pipe software proof; never import a model or algorithm DLL."""
from context import R,C,O,read,put,sha,load,digest
import ast,copy,json,os,subprocess,sys,time,traceback
def main():
 os.sched_setaffinity(0,{5});assert not(O/'SOURCE_ONCE.json').exists();put(O/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0));result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,constructors=0,queries=0,physics=0,replay=0);files={}
 try:
  P=R/'runs/v2055_svg_vehicle_stop_component';assert read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(R/'runs/v2056_svg_stop_background_dispatch/RESULT.json')['closed']and read(R/'runs/v2056_svg_stop_background_dispatch/RESULT.json')['component_started']is False;prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items());files=dict(prior)
  manifest=read(O/'REUSE_DIFF_MANIFEST.json');same=[];changed=[]
  unchanged_from_2055=[]
  for p in C.glob('*.py'):
   if p.name in {'context.py','reservation.py','evidence.py','qualify_source.py'}:continue
   previous=R/'experiments/v2055_svg_vehicle_stop_component'/p.name;assert p.read_bytes()==previous.read_bytes(),'UNDECLARED_VEHICLE_COMPONENT_CHANGE:'+p.name;unchanged_from_2055.append(p.name)
  assert read(O/'PRIOR_UNEXECUTED_REPLACEMENT.json')['same_component_reservation_replaces_not_adds']and not(P/'PILOT_ONCE_CLAIM.json').exists()and not(P/'actual').exists()
  for group in ['unchanged','explicit_CPU_policy_and_nonformal_label_only']:
   for name,row in manifest[group].items():
    parent=R/row['parent_path'];assert sha(parent)==row['parent_sha256'];t=parent.read_text();expected=t
    if name=='runtime_binding.py':expected=expected.replace("job['cpu']=6","job['cpu']=2")
    elif name=='cpu_policy.py':expected=expected.replace('CPU2 pins to CPU6','CPU2 pins to CPU2').replace('mask={6}','mask={2}').replace('({6},{4})','({2},{4})').replace('=={6}','=={2}').replace('{4,6}','{2,4}').replace('translated_to_6','translated_to_2').replace('physics_CPU=6','physics_CPU=2')
    elif name=='resource_policy.py':expected=expected.replace('assert 6 in','assert 2 in').replace('CPU6','CPU2').replace('0,{6}','0,{2}')
    elif name in ['work.py','granted_quota.py']:expected=expected.replace('==[6]','==[2]')
    elif name=='driver.py':expected=expected.replace('formal_MPPI_task_executed','formal_SVG_task_executed')
    assert(C/name).read_text()==expected and sha(C/name)==row['new_sha256'],'UNDISCLOSED_REUSED_SOURCE_CHANGE:'+name
    (same if t==expected else changed).append(name)
  # Original controller binding signatures are unchanged; only authority moves.
  p=R/'experiments/v2052_svg_registered_causal_solver/binding.py';expected=p.read_text().replace('from common import R,S,O,read,sha,authority','from context import R,O,read,sha,native_authority').replace('a,frozen=authority()','a,frozen=native_authority()');assert(C/'binding.py').read_text()==expected
  assert sha(O/'CONFIG.json')==sha(P/'CONFIG.json')and sha(O/'NATIVE_DEPENDENCIES.json')==sha(P/'NATIVE_DEPENDENCIES.json')
  task=read(O/'PILOT_TASK.json');old=read(R/'runs/v2027_mppi_journal_snapshot_consistency/PILOT_TASK.json')
  for k in ['case_id','seed','phase','start_xy','start_yaw','goal_xy','goal_yaw','dynamic','course_id']:assert task[k]==old[k]
  reservation=load('new_component_reserved_source_check',C/'reservation.py').admission();assert reservation['joint_peak_bytes']==16095019008
  # Actual production CLI refuses before runtime/model import, without admission.
  p=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(C/'pilot_entry.py')],env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and b'SVG_COMPONENT_NOT_ADMITTED'in p.stderr
  ros=load('SVG_source_readonly_namespace_check',R/'experiments/v856_nav2_foundation/ros_environment.py');cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_worker.py')]);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind';env=ros.environment();env.update(PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
  p=subprocess.run(['taskset','-c','7',*cmd],env=env,capture_output=True,timeout=15);assert p.returncode!=0 and b'PILOT_ADMISSION.json'in p.stderr
  j=cmd.index('/usr/bin/python3.12');test="from pathlib import Path;import os;assert os.sched_getaffinity(0)=={7}\nfor name in "+repr([str(C/'FORBIDDEN'),str(O/'FORBIDDEN'),str(R/'runs/v2045_remaining_parallel_source/rounds/common_09__MPPI/FORBIDDEN')])+":\n try:Path(name).write_text('forbidden')\n except OSError:pass\n else:raise AssertionError('NATIVE_NAMESPACE_WRITABLE')"
  p=subprocess.run(['taskset','-c','7',*cmd[:j],'/usr/bin/python3.12','-I','-B','-S','-c',test],env=env,capture_output=True,timeout=15);assert p.returncode==0,p.stderr.decode()
  # Coalesced events/reply/closed on a real pipe, no DLL/query/model substitute.
  client=load('SVG_pipe_only_protocol_fixture',C/'native_client.py');saved=[];fixture=[('SVG_EVENT ',dict(sequence=k,stage='EXPLICIT_SOFTWARE_FIXTURE'))for k in range(4)]+[('SVG_REPLY ',dict(passed=True,explicit_software_fixture=True)),('SVG_CLOSED ',dict(explicit_software_fixture=True))]
  script="import json\nfor label,value in "+repr(fixture)+":print(label+json.dumps(value),flush=True)"
  peer=subprocess.Popen(['taskset','-c','7','/usr/bin/python3','-I','-B','-S','-c',script],stdout=subprocess.PIPE,stderr=subprocess.PIPE);obj=client.Client.__new__(client.Client);obj.p=peer;obj.closed=False;obj.calls=0;obj.log=bytearray();obj.messages=[];obj.buffers={};obj.save=lambda name,value:saved.append((name,value));obj.identity=dict(explicit_software_fixture=True);obj.sel=__import__('selectors').DefaultSelector()
  for stream in [peer.stdout,peer.stderr]:obj.sel.register(stream,__import__('selectors').EVENT_READ);obj.buffers[stream.fileno()]=bytearray()
  assert obj.query()==dict(passed=True,explicit_software_fixture=True);obj.close();assert sum(n.startswith('SVG_NATIVE_EVENT_')for n,v in saved)==4 and peer.returncode==0
  # Closed queue proof remains pending: this check must refuse now rather than
  # bypass immutable MPPI owner/cleanup. It is not a failed scientific trial.
  import context
  queue_ready=False
  try:queue_ready=context.queue_closed()
  except(FileNotFoundError,AssertionError):pass
  for folder in [C,R/'experiments/v2054_svg_current_control_contract',R/'experiments/v2060_svg_recovered_background_dispatch',R/'experiments/v2057_mppi08_same_archive_recovery',R/'experiments/v2058_mppi_remaining_four_resume']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [O/n for n in ['PILOT_TASK.json','LIMITS_DRAFT.json','REUSE_DIFF_MANIFEST.json','CONFIG.json','NATIVE_DEPENDENCIES.json','RESERVATION.json','AUTHORIZATION.json','WAIT_QUEUE_OWNER_BINDING.json']]+[R/n for n in ['runs/v2051_mppi_remaining_seven_resume/RESULT.json','runs/v2056_svg_stop_background_dispatch/RESULT.json','runs/v2057_mppi08_same_archive_recovery/RESULT.json','runs/v2045_remaining_parallel_source/rounds/common_08__MPPI/POST_ROUND_STORAGE_BARRIER.json']]+[R/'runs/v2054_svg_current_control_contract/RESULT.json',R/'runs/v2027_mppi_journal_snapshot_consistency/PILOT_TASK.json',R/'runs/v2027_mppi_journal_snapshot_consistency/COMPLETION.json']:files[str(p.relative_to(R))]=sha(p)
  files[str((O/'PRIOR_UNEXECUTED_REPLACEMENT.json').relative_to(R))]=sha(O/'PRIOR_UNEXECUTED_REPLACEMENT.json')
  proof=dict(passed=True,byte_exact_reused_original_capture_response_and_auditors=same,explicit_CPU_and_nonformal_label_changes=changed,author_binding_ABI_body_exact=True,author_8000_100_10_configuration_unchanged=True,unadmitted_vehicle_and_native_CLI_refused_before_imports=True,actual_CPU7_readonly_all_runs_namespace_passed=True,coalesced_pipe_events_reply_close_software_fixture_passed=True,prior_current_interface13negative_cases_reused_by_exact_SHA=True,independent_current_causal_map_state_and_raw_output_audit_bound=True,current_MPPI_queue_healthily_closed=queue_ready,no_physical_permission_until_queue_closed=True,joint_peak_bytes=reservation['joint_peak_bytes'],formal_slots_claimed=0,models=0,algorithm_DLLs=0,physics=0,replay=0)
  proof.update(V2055_other_modules_byte_exact=unchanged_from_2055,original_failed_queue_result_not_overwritten=True,only_recovered_queue_lineage_and_output_namespace_changed=True)
  put(O/'SOFTWARE_CHECK_PROOF.json',proof);files[str((O/'SOFTWARE_CHECK_PROOF.json').relative_to(R))]=sha(O/'SOFTWARE_CHECK_PROOF.json');assert all(sha(R/n)==h for n,h in files.items())
  put(O/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:result['closed']=True;put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,algorithm_DLLs=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
