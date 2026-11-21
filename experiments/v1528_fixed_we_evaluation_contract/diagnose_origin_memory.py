"""One saved-request conditional-state diagnosis; no response model calls."""
import ast,fcntl,hashlib,importlib.abc,importlib.util,json,os,time,traceback
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,value):
 raw=json.dumps(value,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<2*1024**2;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));start=time.monotonic()
 with(O/'MEMORY_DIAGNOSIS_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
 result=dict(closed=False,source_diagnosis_completed=False,models=0,analytical_native=0,physical_native=0,Allocator_recomputations=0,replay_native=0,optimizer_calls=0)
 try:
  class NoNumerical(importlib.abc.MetaPathFinder):
   def find_spec(self,name,*args):
    if name.split('.')[0]in {'numpy','jax','jaxlib','torch','mujoco','rclpy'}:raise AssertionError('CONDITIONAL_SOURCE_DIAGNOSIS_ONLY:'+name)
  import sys
  sys.meta_path.insert(0,NoNumerical())
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized'];assert time.time()<1795395600
   seen=set();usage=0
   for root,ds,fs in os.walk(R/'runs',followlinks=False):
    for p in [Path(root)]+[Path(root)/n for n in fs]:
     st=p.lstat();key=(st.st_dev,st.st_ino)
     if key not in seen:seen.add(key);usage+=st.st_blocks*512
   assert usage+554*1024**2<10*1024**3
   base=read(R/'runs/v1507_priest_response_evidence/SOURCE_FREEZE.json')['files'];spec=importlib.util.spec_from_file_location('new_exact_receipt_source',C/'source_receipts.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
   root=R/'runs/v1479_retirement_scope_binding/first_event';recovery=R/'runs/v1479_retirement_scope_binding/actual_runtime_delivery';current,rows,proof=m.saved_prefix(journal=root/'ACTUAL_OWNER_JOURNAL.jsonl',event_input=root/'bridge_events/event0000/CURRENT_INPUT.json',index=recovery/'ARCHIVE_INDEX.json',remote_proof=recovery/'FULL_REMOTE_VERIFIED.json',source_manifest=base)
   model=R/'experiments/v1159_bounded_steering_load/model.py';graph=read(O/'SOURCE_GRAPH.json');expected=next(x['sha256']for x in graph['rows']if x['path']==str(model.relative_to(R)));assert sha(model)==expected
   tree=ast.parse(model.read_text());step=next(x for x in ast.walk(tree)if isinstance(x,ast.FunctionDef)and x.name=='step');conditional=next(x for x in step.body if isinstance(x,ast.If)and ast.unparse(x.test)=='parked or v <= -0.005');assert len(conditional.body)==1 and len(conditional.orelse)==1 and isinstance(conditional.orelse[0],ast.If)
   for x in ast.walk(conditional):assert not isinstance(x,ast.Call)
   code=compile(ast.Module(body=[conditional],type_ignores=[]),str(model),'exec');owner=SimpleNamespace(steering_load_episode=None);first_known=None;transitions=[]
   for row in rows:
    v=row['request'][0];assert type(v)in(int,float)and type(row['before_native'])is int;before=owner.steering_load_episode;exec(code,dict(self=owner,v=v,parked=row['parked_target']is not None))
    after=owner.steering_load_episode
    if before is not after:
     transitions.append(dict(before_native=row['before_native'],actual_applied_v=v,parked_target=row['parked_target'],before=before,after=after))
    if first_known is None and type(after)is bool:first_known=row['before_native']+1
   result.update(source_diagnosis_completed=True,scope='SOURCE_DERIVED_CONDITIONAL_METHOD_MEMORY_ON_RECORDED_RPP_REQUESTS_NOT_ACTUAL_RPCCR_FLAG',origin_native=current['origin']['native_tick'],initial_load_epoch_unknown=True,canonical_initial_flag_not_assumed=False,first_resolved_after_native=first_known,source_derived_hypothetical_carried_load_at_origin=owner.steering_load_episode,transitions=transitions,original_model_source_sha256=expected,extracted_conditional_source=ast.unparse(conditional),original_observer_entry_explicit_reset=False,actual_load_sensor_observed=False,physical_model_fit_or_projection_qualified=False,not_an_origin_conversion_or_new_method=True,old_input_or_proposal_not_changed=True,actual_RPP_prefix_not_RPCCR_navigation=True,source_proof=proof,allruns_before_bytes=usage,source_scope_peak=usage+554*1024**2)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'ORIGIN_MEMORY_DIAGNOSIS.json',result);print(json.dumps({k:result[k]for k in ['closed','source_diagnosis_completed','models','analytical_native','source_derived_hypothetical_carried_load_at_origin']if k in result}))
if __name__=='__main__':main()
