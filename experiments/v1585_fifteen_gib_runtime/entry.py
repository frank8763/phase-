"""Once new15GiB/round-barrier/applied-content source qualification, zero models."""
import ast,copy,fcntl,importlib.util,json,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1585_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
 start=time.monotonic();resources=c.bootstrap();c.guard()
 lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models_authorized=False),f)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,Allocator_recomputations=0,optimizer_calls=0,actual_runtime_qualified=False,complete_actual_source_target_passed=False,whole_route_passed=False)
 def profile(frame,event,arg):
  if event=='call':
   p=Path(frame.f_code.co_filename)
   if p.is_absolute()and p.is_relative_to(c.R):
    assert not(p.name in {'model.py','coupled_model.py','prediction.py','engine.py','coupled_control.py'}and frame.f_code.co_name in {'__init__','step','simulate','compute'}),'SOURCE_MODEL_OR_ALLOCATOR_FORBIDDEN'
    assert frame.f_code.co_name not in {'physical_binding','load_definitions','initial','all_future'},'SOURCE_NUMERICAL_BINDING_FORBIDDEN'
    assert not('gear_handoff.py'in str(p)and frame.f_code.co_name=='select'),'SOURCE_GEAR_FORBIDDEN'
 sys.setprofile(profile)
 try:
  source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
  target=c.O/'source_target';target.mkdir()
  writers=c.load('v1585_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');io=c.load('v1585_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
  writer=writers.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.sha(C/'entry.py'))
  negative=[]
  def refused(name,fn):
   try:fn()
   except BaseException as error:negative.append(dict(name=name,error=repr(error)));return
   raise AssertionError('NEW_SCOPE_NEGATIVE_ACCEPTED:'+name)
  with io.OutputBoundary(target,writer.reserve):
   budget=c.load('v1585_new_fifteen_budget',C/'budget.py');limits=budget.limits();limit=15*1024**3;extra=limits['full_scope_additional_bytes']
   assert budget.check_peak(limit-extra-1)['full_reserved_peak_bytes']==limit-1
   refused('exact15GiB_peak_refused',lambda:budget.check_peak(limit-extra))
   refused('beyond15GiB_refused',lambda:budget.check_peak(limit-extra+1))
   snapshot=budget.preflight();assert snapshot['full_reserved_peak_bytes']<limit
   # Source/authority barrier uses explicit SOFTWARE metadata and rejects the
   # first newer round without post-upload/cleanup proof; no oldround rerun.
   barrier=c.load('v1585_single_round_barrier',C/'round_barrier.py');parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
   assert barrier.before_next(parent,current_round=C.name)['passed']
   a=c.read(barrier.AUTH);bad=copy.deepcopy(parent);bad['rounds'].append(dict(id='SOFTWARE_UNBACKED_ROUND',status='CLOSED',started_unix=a['recorded_unix']+1))
   refused('next_before_previous_upload_cleanup',lambda:barrier.before_next(bad,current_round=C.name))
   # Three SOFTWARE array-shaped records test only content binding. They are
   # not simulator states, measured packets, safety branches or actual counts.
   binding=c.load('v1585_new_fullstate_receipt_content',C/'transition_binding.py')
   full=dict(time=[0.,.01,.02,.03],qpos=[[float(i),0.]for i in range(4)],qvel=[[0.,0.]for _ in range(4)],ctrl=[[0.,0.,0.,0.]for _ in range(4)],mocap_pos=[[[0.,0.,0.]]for _ in range(4)],mocap_quat=[[[1.,0.,0.,0.]]for _ in range(4)])
   method=dict(response_method_sha256='a'*64,base_method={'fixed_origin_native':0})
   events=[dict(kind='METHOD_MEMORY',receipt=dict(kind='DECLARED_OBSERVER_ENTRY_METHOD_EPOCH',epoch_native=0,covered_native=0,response_method_sha256='a'*64))];rows=[]
   for tick in range(3):
    packet=dict(native_tick=tick,explicit_SOFTWARE_not_sensor=True)
    row=dict(before_native=tick,applied=False,source_packet=packet,source_packet_sha256=binding.digest(packet),source_full_state_sha256=binding.digest(binding.fullstate_at(full,tick)),request=[0.,0.,False],parked_target=None)
    before=dict(kind='BEFORE_NATIVE',row=copy.deepcopy(row),source_row_sha256=binding.digest(row));events.append(before)
    row['applied']=True;after=dict(kind='AFTER_NATIVE',row=copy.deepcopy(row),source_row_sha256=before['source_row_sha256'],after_native=tick+1,root_native_count=tick+1,contact_records=tick+2,after_full_state_sha256=binding.digest(binding.fullstate_at(full,tick+1)))
    events.append(after);rows.append(row)
    transition=dict(before_native=tick,after_native=tick+1,epoch_native=0,response_method_sha256='a'*64,source_full_state_sha256=row['source_full_state_sha256'],after_full_state_sha256=after['after_full_state_sha256'],source_packet_sha256=row['source_packet_sha256'],actual_receipt_sha256=binding.digest(after),applied_body=[0.,0.],parked_target=None)
    events.append(dict(kind='METHOD_MEMORY',receipt=transition))
   baseline=binding.verify(fullstate=full,rows=rows,events=events,method=method,check=lambda:None);assert baseline['applied_transitions']==3
   for name,where,key,value in [('beforestate','memory','source_full_state_sha256','b'*64),('afterstate','memory','after_full_state_sha256','b'*64),('receipt','memory','actual_receipt_sha256','b'*64),('packet','memory','source_packet_sha256','b'*64),('root','after','root_native_count',99),('contact','after','contact_records',99),('rowhash','before','source_row_sha256','b'*64)]:
    changed=copy.deepcopy(events);kind={'memory':'METHOD_MEMORY','after':'AFTER_NATIVE','before':'BEFORE_NATIVE'}[where]
    event=next(e for e in changed if e['kind']==kind and(where!='memory'or'before_native'in e['receipt']))
    (event['receipt']if where=='memory'else event)[key]=value
    refused(name,lambda:binding.verify(fullstate=full,rows=rows,events=changed,method=method,check=lambda:None))
   refused('missing_after',lambda:binding.verify(fullstate=full,rows=rows,events=[e for i,e in enumerate(events)if i!=2],method=method,check=lambda:None))
   altered=copy.deepcopy(full);altered['qpos'][1][0]=100.
   refused('changed_actual_fullstate',lambda:binding.verify(fullstate=altered,rows=rows,events=events,method=method,check=lambda:None))
   c.put(target/'QUALIFICATION.json',dict(passed=True,software_only=True,fullstate_receipt_content=baseline,negative_cases=negative,storage_snapshot=snapshot,models=0,actual_native=0,old_suites_not_reexecuted=True))
  # The now-connected new audit wrapper is imported, not executed on any
  # historical actual record or any model expected state.
  c.load('v1585_bound_native_audit_wrapper',C/'actual_audit.py')
  reused=[]
  for name in ['tracker.py','carrier.py','witness.py','gates.py','current_reserve.py','reference.py','actual_sink.py','scoped_output.py','transaction.py','components.py','close.py','accounting.py']:
   before=(c.R/'experiments/v1582_owner_close_transaction'/name).read_text();after=(C/name).read_text().replace('v1585_fifteen_gib_runtime','v1582_owner_close_transaction').replace('v1585','v1582')
   assert ast.dump(ast.parse(before))==ast.dump(ast.parse(after)),name;reused.append(name)
  assert all(c.sha(c.R/n)==h for n,h in source.items())
  c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,models_authorized=False,complete_actual_source_target_passed=False),maximum=4*1024**2)
  result.update(passed=True,source_members=len(source),negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],resources=resources,source_reuse=reused,storage_snapshot=snapshot,storage_limit_bytes=limit,source_gates=dict(fifteen_GiB_and_round_barrier=True,applied_fullstate_receipt_content=True,complete_actual_source_target=False))
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  sys.setprofile(None);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
 print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
