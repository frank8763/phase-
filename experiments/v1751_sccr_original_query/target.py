"""One synthetic fixed-input original SCCR query; never constructs a plant."""
import ast,fcntl,importlib.abc,os,sys,time,traceback
from round_common import *
def main():
 mode='query' if '--query' in sys.argv else 'source';start=time.monotonic()
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1751_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0] in {'mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','route_tools','ctypes'} or (mode=='source' and name.split('.')[0]=='numpy'):raise AssertionError('SCCR_UNAUTHORIZED_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with (R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  claim=O/('QUERY_ONCE_CLAIM.json' if mode=='query' else 'SOURCE_ONCE_CLAIM.json')
  with claim.open('x')as f:f.write('{}\n')
  result=dict(passed=False,closed=False,scope='SYNTHETIC_FIXED_INPUT_GEOMETRIC_CORE_QUERY' if mode=='query' else 'NEW_QUERY_ENTRY_SOURCE_QUALIFICATION',models=0,analytical_native=0,physical_native=0,replay_native=0,original_SCCR_query_attempts=0,original_SCCR_query_returns=0,whole_navigation_passed=None,real_measured_receipt=False)
  source=read(R/'runs/v1749_sccr_public_interface/SOURCE_FREEZE.json')['files'].copy()
  try:
   assert read(R/'runs/v1749_sccr_public_interface/POST_SOURCE_STORAGE_BARRIER.json')['passed']
   for p in [p for folder in [C,R/'experiments/v1752_sccr_query_source_recovery',R/'experiments/v1753_sccr_query_runtime_recovery'] for p in folder.iterdir()]:
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     source[str(p.relative_to(R))]=sha(p)
   assert all(sha(R/n)==h for n,h in source.items()),'SOURCE_CHANGED'
   if mode=='source':
    assert not (O/'CURRENT_QUERY_ADMISSION.json').exists()
    # New query authority is checked before importing the original numerical module.
    tree=ast.parse((C/'target.py').read_text());assert len([n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='run'])==1
    fixture=read(C/'FIXED_FIXTURE.json');assert fixture['synthetic_software_fixture'] and not fixture['real_measured_receipt']
    put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False));result.update(passed=True,source_members=len(source),reused_source_qualification_sha256=sha(R/'runs/v1749_sccr_public_interface/SOURCE_QUALIFICATION.json'),new_entry_AST_checked=True,fixture_explicitly_synthetic=True)
   else:
    authority=read(O/'CURRENT_QUERY_ADMISSION.json');assert authority['query_authorized'] and not authority['physical_admission'] and authority['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')
    assert authority['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and time.time()<authority['deadline_unix'] and time.monotonic()<authority['deadline_monotonic']
    assert read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
    sys.path.insert(0,str(R/'experiments/v1749_sccr_public_interface'))
    contract=load('v1751_frozen_public_contract',R/'experiments/v1749_sccr_public_interface/contract.py')
    fixture=read(C/'FIXED_FIXTURE.json');receipt=fixture['receipt'];assert receipt['packet_sha256']==contract.digest(receipt['packet'])
    config=read(R/'experiments/v1749_sccr_public_interface/PLANNER_CONFIG.json')['values']
    payload=contract.causal_input(receipt,fixture['known'],fixture['public_route'],config)
    # Synthetic timing metadata exercises the interface; never relabel it as acquired measurement.
    put(O/'FIXED_QUERY_INPUT.json',dict(payload=payload,synthetic_software_fixture=True,real_measured_receipt=False,input_source_sha256=sha(C/'FIXED_FIXTURE.json')))
    query=load('v1751_frozen_original_query',R/'experiments/v1749_sccr_public_interface/query.py');query.O=O
    result['original_SCCR_query_attempts']=None;put(O/'QUERY_PROGRESS.json',dict(interface_call_entered=True,original_core_attempt_unknown_until_return=True))
    answer=query.run(payload,source)
    put(O/'ORIGINAL_QUERY_RESPONSE.json',answer)
    result.update(passed=bool(answer.get('query_called')and answer.get('query_returns')==1),original_SCCR_query_attempts=answer.get('query_attempts',0),original_SCCR_query_returns=answer.get('query_returns',0),candidate_found=answer.get('candidate_found'),candidate_count=answer.get('candidate_count'),interface_response_reason=answer.get('reason'),original_numerical_body_unchanged=True,internal_numerical_work_unknown=True,algorithm_navigation_success_not_tested=True)
  except BaseException as e:
   result.update(first_error=repr(e),traceback=traceback.format_exc())
   if mode=='source':put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
  finally:
   result.update(closed=True,wall_s=time.monotonic()-start);put(O/('QUERY_RESULT.json' if mode=='query' else 'SOURCE_QUALIFICATION.json'),result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
