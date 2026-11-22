"""Once metadata-only indexing scope; no numerical imports or authority."""
import ast,copy,fcntl,importlib.abc,importlib.util,json,os,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1617_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def main():
 start=time.monotonic();c.bootstrap();c.guard()
 lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as out:json.dump(dict(unix=time.time(),models_authorized=False),out)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,Allocator_recomputations=0,optimizer_calls=0,complete_actual_source_target_passed=False)
 class NoNumerics(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','OpenGL','torch','jax','jaxlib','rclpy','factory','vehicle','kernel','runtime'}:raise AssertionError('CLOSED_INDEX_NO_NUMERICS:'+name)
 finder=NoNumerics();sys.meta_path.insert(0,finder)
 def profile(frame,event,arg):
  if event=='call':
   p=Path(frame.f_code.co_filename)
   if p.is_absolute()and p.is_relative_to(c.R):assert frame.f_code.co_name not in {'create_vehicle','physical_binding','load_definitions','initial','simulate','step','predict','compute','advance'}
   assert time.monotonic()-start<120
 sys.setprofile(profile)
 try:
  parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['scientific_revisions']==12 and parent['active_round']is None and not parent['models_now_authorized']
  source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
  p=c.load('v1617_exact_parent_functions',C/'parent_payloads.py')
  old=ast.parse((c.R/'experiments/v1542_parent_preparation_payloads/parent_payloads.py').read_text());new=ast.parse((C/'parent_payloads.py').read_text())
  get=lambda tree:{n.name:ast.dump(n)for n in tree.body if isinstance(n,ast.FunctionDef)}
  assert get(old)==get(new)
  payload,candidate=p.plan(parent);assert p.hydrate(candidate,payload)==parent
  assert all(candidate[k]==v for k,v in parent.items()if k not in p.FIELDS)
  owner=c.load('v1617_unchanged_actual_parent_cap',c.R/'experiments/v1615_private_namespace_scope/supervisor.py')
  original=owner.parent_bytes(parent);encoded=owner.parent_bytes(candidate)
  assert len(encoded)+8192+4096<=131072,'CLOSED_INDEX_HEADROOM_STILL_INSUFFICIENT'
  wm=c.load('v1617_original_counter',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');io=c.load('v1617_original_IO',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py');codec=c.load('v1617_original_JSON_IO',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
  target=c.O/'source_target';target.mkdir();writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.digest(source));negative=[]
  with io.OutputBoundary(target,writer.reserve):
   def save(name,raw):codec.write_atomic(target/name,raw,writer)
   save('PARENT_ORIGINAL.json',original);save('PARENT_PAYLOADS.json',p.encoded(payload));save('PARENT_CANDIDATE.json',encoded)
   assert c.sha(target/'PARENT_PAYLOADS.json')==p.digest(payload)
   assert p.hydrate(c.read(target/'PARENT_CANDIDATE.json'),c.read(target/'PARENT_PAYLOADS.json'))==parent
   changed=copy.deepcopy(candidate);changed[p.FIELDS[0]]['payload_reference']['sha256']='0'*64
   try:p.hydrate(changed,payload)
   except AssertionError:negative.append('REFERENCE_SHA')
   else:raise AssertionError('REFERENCE_TAMPER_ACCEPTED')
   changed=copy.deepcopy(payload);changed['values'][p.FIELDS[0]]['models']='SOFTWARE_TAMPER'
   try:p.hydrate(candidate,changed)
   except AssertionError:negative.append('PAYLOAD_VALUE')
   else:raise AssertionError('PAYLOAD_TAMPER_ACCEPTED')
   try:p.plan(parent,fields=['rounds'])
   except AssertionError:negative.append('CANONICAL_FIELD_SCOPE')
   else:raise AssertionError('CANONICAL_FIELDS_MOVED')
   proof=dict(passed=True,models=0,source_only=True,no_real_parent_written=True,original_function_AST_exact=True,all_other_values_unchanged=True,full_hydration_exact=True,fields=p.FIELDS,original_compact_bytes=len(original),candidate_compact_bytes=len(encoded),cap_bytes=131072,close_reserve_bytes=8192,source_parent_digest=c.digest(parent),source_parent_file_sha256=c.sha(c.R/'runs/v1382_weekend_campaign/LEDGER.json'),candidate_parent_digest=c.digest(candidate),payload_sha256=p.digest(payload),negative=negative)
   save('PARENT_LOSSLESS_PROOF.json',codec.encoded(proof))
  c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,models_authorized=False,complete_actual_source_target_passed=False),maximum=4*1024**2)
  result.update(passed=True,negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],source_members=len(source),proof=proof)
 except BaseException as error:
  result.update(first_error=repr(error),traceback=traceback.format_exc())
  if 'source'in locals():c.put(c.O/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False),maximum=4*1024**2)
 finally:
  sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
 print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
