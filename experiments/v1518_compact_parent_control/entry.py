"""New exact parent serialization source target; no numerical dependencies."""
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1518_metadata_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def main():
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(c.R)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(started_unix=time.time(),models=0),f)
 class NoNumeric(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','jax','jaxlib','mujoco','torch','rclpy','vehicle','factory'}:raise AssertionError('PARENT_METADATA_ONLY:'+name)
 finder=NoNumeric();sys.meta_path.insert(0,finder);c.guard();result=dict(passed=False,closed=False,models=0,response_model_native=0,physical_native=0,Allocator_recomputations=0,replay_native=0,optimizer_calls=0)
 try:
  with(c.R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
   prior=c.R/'runs/v1516_priest_origin_provenance';q=c.read(prior/'ENTRY_QUALIFICATION.json');assert q['passed']and q['closed']and not(prior/'NUMERIC_ONCE_CLAIM.json').exists();original=c.R/'experiments/v1516_priest_origin_provenance'
   for name in ['common.py','contract.py','driver.py','generator.py','audit.py','model_bridge.py','LIMITS.json']:assert(C/name).read_bytes()==(original/name).read_bytes()
   before=ast.parse((original/'owner.py').read_text());after=ast.parse((C/'owner.py').read_text())
   # Remove only the explicit encoder; normalize only parent_put and its preflight expression.
   after.body=[node for node in after.body if not isinstance(node,ast.FunctionDef)or node.name!='parent_bytes']
   before_funcs=[node for node in ast.walk(before)if isinstance(node,ast.FunctionDef)and node.name=='parent_put'];after_funcs=[node for node in ast.walk(after)if isinstance(node,ast.FunctionDef)and node.name=='parent_put'];assert len(before_funcs)==len(after_funcs)==1;after_funcs[0].body=before_funcs[0].body
   class Normalize(ast.NodeTransformer):
    def visit_Assert(self,node):
     if isinstance(node.msg,ast.Constant)and node.msg.value=='PARENT_LEDGER_CLOSE_BOUND_REFUSED':return ast.Assert(test=ast.Constant(True),msg=node.msg)
     return self.generic_visit(node)
   assert ast.dump(Normalize().visit(before))==ast.dump(Normalize().visit(after))
   owner=c.load('v1518_new_parent_codec',C/'owner.py');payload=owner.parent_bytes(parent);assert json.loads(payload)==parent and len(payload)+8192<=131072
   future=dict(parent,software_close_headroom_probe='x'*8192);future_payload=owner.parent_bytes(future);assert json.loads(future_payload)==future
   boundary=c.load('v1518_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py');budgets=c.load('v1518_original_writer_budget',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');task=c.O/'software_parent';task.mkdir();writer=budgets.WriterBudget(task,role='SUPERVISOR_LOG',maximum_bytes=512*1024,source_identity=c.digest({'prior_qualification_sha256':c.sha(prior/'ENTRY_QUALIFICATION.json')}))
   with boundary.OutputBoundary(task,writer.reserve):
    temporary=task/'LEDGER.json.tmp';temporary.write_bytes(payload);temporary.replace(task/'LEDGER.json');assert c.read(task/'LEDGER.json')==parent
    rejected=False
    try:owner.parent_bytes(dict(oversized='x'*131073))
    except AssertionError as error:rejected=True;message=repr(error)
    assert rejected and not(task/'OVERSIZED.json').exists()
   c.put(c.O/'PARENT_SERIALIZATION_QUALIFICATION.json',dict(passed=True,parent_original_file_sha256=c.sha(c.R/'runs/v1382_weekend_campaign/LEDGER.json'),original_pretty_bytes=len(json.dumps(parent,indent=2,allow_nan=False).encode()),new_compact_bytes=len(payload),maximum_control_bytes=131072,preflight_close_reserved_bytes=8192,prospective_close_probe_bytes=len(future_payload),roundtrip_exact_all_fields=True,software_atomic_stage_readback_passed=True,oversize_rejected=message,actual_parent_files_untouched=True,real_original_writer_debit=writer._read(),all_numerical_worker_sources_byte_exact=True,V1516originqualification_reused_not_reexecuted=True,models=0))
   c.put(c.O/'FIXED_INPUTS.json',c.read(prior/'FIXED_INPUTS.json'));files={str(p.relative_to(c.R)):c.sha(p)for p in C.iterdir()if p.is_file()}
   for path in [c.INPUT,c.PROPOSAL,c.SETUP,c.O/'FIXED_INPUTS.json',prior/'ENTRY_QUALIFICATION.json',prior/'ORIGIN_INTERFACE_QUALIFICATION.json',c.R/'runs/v1513_priest_binding_token_repair/BACKEND_BINDING_PROOF.json',c.R/'runs/v1509_priest_response_once/PARENT_RESERVATION_PROOF.json']:files[str(path.relative_to(c.R))]=c.sha(path)
   c.put(c.O/'SOURCE_FREEZE.json',dict(files=files,base_manifest=str(c.BASE.relative_to(c.R)),base_manifest_sha256=c.sha(c.BASE),entry_passed=True));c.sources();result.update(passed=True,source_frozen=True,metadata_only=True,old_origin_bootstrap_and_byte_targets_not_rerun=True,exact_all_field_parent_roundtrip=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:result['closed']=True;c.put(c.O/'ENTRY_QUALIFICATION.json',result);sys.meta_path.remove(finder)
 if result['passed']:
  freeze=c.read(c.O/'SOURCE_FREEZE.json')
  for path in [c.O/'ENTRY_QUALIFICATION.json',c.O/'PARENT_SERIALIZATION_QUALIFICATION.json']:freeze['files'][str(path.relative_to(c.R))]=c.sha(path)
  c.put(c.O/'SOURCE_FREEZE.json',freeze)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
