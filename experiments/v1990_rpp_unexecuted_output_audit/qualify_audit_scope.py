"""Actual old/new audit block seam, synthetic commands only, no old reaudit."""
from context import R,C,O,read,put,sha
import ast,copy,os

def check():
 os.sched_setaffinity(0,{7});import numpy as np
 old=R/'experiments/v1983_rpp_bounded_console_queue/audit_component.py';new=C/'audit_component.py'
 def block(path,old_scope):
  tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit');loop=next(n for n in fn.body if isinstance(n,ast.For)and "native_reply.json"in ast.unparse(n.iter));nodes=loop.body
  if old_scope:items=[next(n for n in nodes if isinstance(n,ast.If)and ast.unparse(n.test)=="raw['passed']")]
  else:
   start=next(i for i,n in enumerate(nodes)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='executed'for t in n.targets));items=nodes[start:]
  return compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(items),type_ignores=[])),str(path),'exec')
 oldcode=block(old,True);newcode=block(new,False)
 class File:
  def __init__(self,exists):self.present=exists
  def exists(self):return self.present
 class Root:
  def __init__(self,present):self.present=present
  def __truediv__(self,n):return File(self.present)
 def run(code,*,executed,gear,vr=.1,rawpassed=True,applied=.1):
  scope=dict(raw=dict(passed=rawpassed,twist=[vr,0.]),record=dict(gear=gear),out=Root(executed),base='synthetic',read=lambda p:dict(kind='RPP_control_cycle'),origin=dict(origin_native=0),commands=np.tile([0.,applied,0.,0.,0.,0.],[5,1]),np=np,math=__import__('math'))
  exec(code,scope)
 try:run(oldcode,executed=False,gear=-1)
 except AssertionError:old_red=True
 else:raise AssertionError('OLD_AUDIT_WRONG_GEAR_NOT_REPRODUCED')
 run(newcode,executed=False,gear=-1);run(newcode,executed=True,gear=1);negative=[]
 for name,kw in [('executed_wrong_gear',dict(executed=True,gear=-1)),('executed_bad_domain',dict(executed=True,gear=1,vr=.2)),('executed_failed_native',dict(executed=True,gear=1,rawpassed=False)),('executed_mismatched_command',dict(executed=True,gear=1,applied=.09))]:
  try:run(newcode,**kw)
  except AssertionError:negative.append(name)
  else:raise AssertionError('BAD_EXECUTED_OUTPUT_ACCEPTED:'+name)
 unchanged=[]
 for name in ['navigation.py','response.py','driver.py','native_client.py','native_worker.py','capture.py','evidence_service.py','runtime_binding.py','console_codec.py','request_dictionary.py']:
  expected=(old.parent/name).read_text().replace('v1983_rpp_bounded_console_queue',C.name);assert(C/name).read_text()==expected,'NUMERIC_OR_CONTROL_MODULE_CHANGED:'+name;unchanged.append(name)
 proof=dict(passed=True,old_block_reproduces_unexecuted_wronggear_assertion=old_red,new_block_ignores_only_unexecuted_output_for_applied_control_safety=True,applied_safe_command_still_checked=True,executed_bad_outputs_refused=negative,decision_response_capture_and_transport_modules_namespace_only=unchanged,old_closed_case_not_reaudited_replayed_or_relaunched=True,models=0,DLL_calls=0,solver_calls=0,physical_native=0,replay_native=0);put(O/'AUDIT_SCOPE_SOFTWARE_PROOF.json',proof);print(__import__('json').dumps(proof));return proof
if __name__=='__main__':check()
