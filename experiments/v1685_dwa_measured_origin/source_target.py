"""Once new packet receipt qualification; reuse prior numerical proofs by SHA."""
import ast,copy,ctypes,fcntl,importlib.abc,json,runpy,sys,time,traceback
from context import C,O,R,read,sha,load,put,digest
P=R/'experiments/v1683_dwa_complete_source_chain';PO=R/'runs'/P.name

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy
 resource_policy.apply();load('v1685_originalguard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','bindings'}:raise AssertionError('SOURCE_NO_MODELS:'+name)
 sys.meta_path.insert(0,Ban());original=ctypes.CDLL
 def banned(*a,**k):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=banned
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(PO/'SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,reference_query_calls=0,actual_runtime_qualified=False)
 try:
  assert read(PO/'COMPLETION.json')['closed']and not read(PO/'COMPLETION.json')['passed']
  barrier=read(PO/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']
  assert all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
  assert read(PO/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for name in ['PILOT_TASK.json','REFERENCE_CONFIG.json','LIMITS_DRAFT.json']:
   p=O/name;source[str(p.relative_to(R))]=sha(p)
  for name in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','COMPLETION.json','RUNTIME_CLOSED_REVIEW.json','POST_ROUND_STORAGE_BARRIER.json','PACKET_BINDING_DIAGNOSIS.json']:
   p=PO/name;source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  reused=[]
  for name in ['capture.py','resources.py','quota.py','work.py','history_binding.py','transforms.py','runtime_binding.py','error_stop.py','obstacles.py','pilot_entry.py','context.py','source_owner.py']:
   assert sha(C/name)==sha(P/name);reused.append(name)
  for name in ['REFERENCE_CONFIG.json','LIMITS_DRAFT.json']:assert sha(O/name)==sha(PO/name)
  newtask=read(O/'PILOT_TASK.json');oldtask=read(PO/'PILOT_TASK.json')
  assert {k:v for k,v in newtask.items()if k not in {'output','run_root','run_id'}}=={k:v for k,v in oldtask.items()if k not in {'output','run_root','run_id'}}
  # Exactly the explicit receipt plumbing changes. All numerical statements stay.
  old=(P/'component.py').read_text();expected=old.replace('def run(v,binding,task,source,out,save,quota):','def run(v,binding,task,source,out,save,quota,measured_origin):').replace("p0=packet(v);assert p0['native_tick']==0 and p0['sim_time']==0.","p0=copy.deepcopy(measured_origin);assert p0['native_tick']==0 and p0['sim_time']==0.").replace('current=packet(v);block=requests[i:i+5]','current=copy.deepcopy(p0)if i==0 else packet(v);block=requests[i:i+5]')
  assert(C/'component.py').read_text()==expected,'ONLY_EXPLICIT_MEASURED_ORIGIN_COMPONENT_CHANGE'
  olddriver=(P/'driver.py').read_text();expected=olddriver.replace("result['component']=component.run(v,binding,task,source,out,save,quota)","origin_binding=load('v1685_single_measured_origin',C/'origin.py')\n    measured_origin=origin_binding.acquire(v,binding,read(out/'CANONICAL_INITIAL_PACKET.json'),save)\n    result['component']=component.run(v,binding,task,source,out,save,quota,measured_origin)")
  assert(C/'driver.py').read_text()==expected,'ONLY_EXPLICIT_ORIGIN_DRIVER_CHANGE'
  audit=load('v1685_generic_auditor_identity',C/'audit_component.py');fn,seam=audit.generic_ast(source)
  assert seam==read(PO/'SOURCE_QUALIFICATION.json')['original_generic_actual_audit_seam']
  oldaudit=ast.parse((P/'audit_component.py').read_text());newaudit=ast.parse((C/'audit_component.py').read_text())
  assert ast.dump(oldaudit.body[5],include_attributes=False)==ast.dump(newaudit.body[5],include_attributes=False),'GENERIC_AUDIT_FUNCTION_UNCHANGED'
  audit_expected=(P/'audit_component.py').read_text().replace(" proof=read(out/'CURRENT_SHADOW_CERTIFICATE.json');assert proof['passed']and proof['origin_packet']==p0 and proof['origin_packet_sha256']==__import__('hashlib').sha256(__import__('json').dumps(p0,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()"," origin_binding=load('v1685_independent_origin_receipt',C/'origin.py');origin=origin_binding.verify_receipt(read(out/'CURRENT_MEASURED_ORIGIN.json'),p0)\n proof=read(out/'CURRENT_SHADOW_CERTIFICATE.json');assert proof['passed']and proof['origin_packet']==origin and proof['origin_packet_sha256']==origin_binding.digest(origin)\n solver=read(out/'CURRENT_SOLVER_INPUT.json')['origin'];proposal=read(out/'DWA_SELECTED_CURRENT_PROPOSAL.json');assert solver['origin_packet']==origin and solver['origin_packet_sha256']==origin_binding.digest(origin)and proposal['source_packet']==origin").replace("for row in receipts:\n  one=row['proof'];","assert receipts[0]['proof']['origin_packet']==origin and receipts[0]['proof']['origin_packet_sha256']==origin_binding.digest(origin)\n for row in receipts:\n  one=row['proof'];")
  assert(C/'audit_component.py').read_text()==audit_expected,'ALL_OTHER_INDEPENDENT_NUMERIC_AUDIT_GATES_UNCHANGED'
  text=(C/'audit_component.py').read_text();assert 'verify_receipt'in text and "solver['origin_packet']==origin"in text and "proposal['source_packet']==origin"in text and "receipts[0]['proof']['origin_packet']==origin"in text
  origin=load('v1685_actual_receipt_software',C/'origin.py')
  # Representative non-numerical packet metadata only, no old controls in plant.
  base=dict(body=[-4.,-2.,0.,0.,0.],body_lateral=0.,native_tick=0,sim_time=0.,body_measured_at=time.monotonic()-1,sent_at=0.,dynamic_discovered=False,steering=dict(position=[0.,0.],velocity=[0.,0.],native_tick=0,measured_at=0.),controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=0.),coupled_episode=False,steering_motion_active=False)
  base['sent_at']=base['steering']['measured_at']=base['body_measured_at'];saved={};calls=[]
  def packet(v):
   calls.append(v);p=copy.deepcopy(base);t=time.monotonic();p['body_measured_at']=p['sent_at']=p['steering']['measured_at']=t;return p
  answer=origin.acquire('SOFTWARE_ONLY',dict(packet=packet),base,lambda name,value:saved.update({name:copy.deepcopy(value)}))
  assert len(calls)==1 and len(saved)==1
  receipt=saved['CURRENT_MEASURED_ORIGIN.json'];assert answer==origin.verify_receipt(receipt,base)and answer!=base
  assert base['body_measured_at']<answer['body_measured_at']and origin.digest(base)!=origin.digest(answer)
  answer['body'][0]=999.;assert receipt['packet']['body'][0]==-4.,'DETACHED_COPY'
  negatives=[]
  def rejected(name,change,rehash=True):
   r=copy.deepcopy(receipt);change(r)
   if rehash:r['packet_sha256']=origin.digest(r['packet'])
   try:origin.verify_receipt(r,base)
   except(AssertionError,KeyError):negatives.append(name)
   else:raise AssertionError('SOFTWARE_NEGATIVE_ACCEPTED:'+name)
  rejected('body_change',lambda r:r['packet']['body'].__setitem__(0,-3.))
  rejected('memory_change',lambda r:r['packet']['controller_memory'].__setitem__('integral',.1))
  rejected('native_change',lambda r:r['packet'].__setitem__('native_tick',1))
  rejected('sim_clock_change',lambda r:r['packet'].__setitem__('sim_time',.01))
  rejected('outside_acquisition_clock',lambda r:r.__setitem__('acquisition_after_monotonic',r['acquisition_before_monotonic']-.1))
  rejected('cross_channel_timestamp',lambda r:r['packet'].__setitem__('sent_at',r['packet']['sent_at']+.001))
  rejected('more_than_one_acquisition',lambda r:r.__setitem__('packet_acquisitions',2))
  rejected('wrong_bootstrap',lambda r:r.__setitem__('bootstrap_packet_sha256','0'*64))
  rejected('tampered_packet_SHA',lambda r:r.__setitem__('packet_sha256','0'*64),False)
  rejected('missing_receipt',lambda r:r.pop('packet'))
  for name in ['pilot_entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='DWA_LIVE_COMPONENT_NOT_ADMITTED';negatives.append('actual_'+name+'_unadmitted')
   else:raise AssertionError('CLI_ACCEPTED')
  assert all(sha(R/n)==h for n,h in source.items())
  put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),negative_cases=negatives,exact_pipeline_modules_reused=reused,original_generic_actual_audit_seam=seam,sourcepass_not_actualpass=True,one_measurement_receipt_software_passed=True,separate_bootstrap_preserved=True,single_query_shadow_first_admission_origin=True,numerical_component_statements_byteidentical_except_explicit_packet_plumbing=True,old_failed_case_not_reaudited=True,previous_source_proof_sha256=sha(PO/'SOURCE_QUALIFICATION.json'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
