"""Production one-case dispatcher: functional or technical closes before deciding; zero models."""
import os,time,types,json,traceback
from context import R,C,SOURCE as S,read,put,load

def main():
 assert os.sched_getaffinity(0)=={4};result=dict(passed=False,models=0,optimizer_queries=0,physical=0);cases=[]
 try:
  for label,technical in [('functional_closed',False),('technical_closed',True)]:
   root=S/'dispatcher_software'/label;root.mkdir(parents=True);fakeR=root/'repo';fakeS=fakeR/'runs/fixture';fakeS.mkdir(parents=True)
   for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
    p=fakeR/n;p.parent.mkdir(parents=True,exist_ok=True);p.touch()
   (fakeR/'REVIEW_PENDING').write_text('explicit software fixture')
   auth=dict(absolute_end_unix=time.time()+9000,required_reserve_before_new_component_s=6900,fixed_order=['PCBF'])
   b=dict(retained_future_closed_bytes=0,all_prior_evidence_upper_bytes=15226404864,preparation_bytes=16*1024**2,metadata_bytes=8*1024**2)
   for n,v in [('POST_SOURCE_STORAGE_BARRIER.json',dict(passed=True)),('SOURCE_FREEZE.json',dict(files={})),('AUTHORIZATION.json',auth),('BASELINE_DRAFT.json',b),('CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(source_commit='software_only'))]:put(fakeS/n,v)
   (fakeS/'components/PCBF').mkdir(parents=True)
   d=load('conditioned_dispatcher_fixture_'+label,C/'dispatcher.py');d.R=fakeR;d.S=fakeS;d.ready=lambda:True;d.sha=lambda p:'4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';d.subprocess=types.SimpleNamespace(check_output=lambda *a,**kw:b'1 fixture')
   d.os=types.SimpleNamespace(sched_setaffinity=lambda *a:None,nice=lambda *a:None,getpriority=lambda *a:19,PRIO_PROCESS=os.PRIO_PROCESS,getpid=os.getpid)
   calls=[]
   def process(name,argv,cap,*,method=None):
    calls.append(name);o=fakeS/'components'/method
    if name.endswith('_owner'):
     put(o/'COMPLETION.json',dict(closed=True,passed=False,all_source_SHA_after_child=True,actual_native=200,own_replay_native=200,independent_audit=dict(passed=True),machine_secondary_errors=[],machine_first_error=dict(error='TECHNICAL_FAULT'if technical else'FILTER_CURRENT_CYCLE_COMPLETE_STOP_REFUSED')))
    elif name.endswith('_delivery'):
     t=fakeS/'runtime_archives'/method;t.mkdir(parents=True);put(t/'FULL_REMOTE_VERIFIED.json',dict(passed=True));put(t/'TRANSPORT_CLEANUP.json',dict(passed=True))
    return 1 if name.endswith('_owner')else 0
   d.process=process;d.main();answer=read(fakeS/'DISPATCH_RESULT.json')
   assert calls==['PCBF_owner','PCBF_archive','PCBF_ref','PCBF_delivery']and answer['finite_queue_completed']is(not technical)
   assert read(fakeS/'components/PCBF/POST_COMPONENT_STORAGE_BARRIER.json')['passed']
   cases.append(dict(case=label,calls=calls,finite_completed=answer['finite_queue_completed'],barrier_before_disposition=True))
  d=load('conditioned_ready_gate',C/'dispatcher.py');d.predecessors_closed=lambda:True;assert d.ready()
  assert d.decision(False,True,False)=='WAIT'and d.decision(True,False,False)=='DEADLINE_STOP'and d.decision(True,True,True)=='USER_STOP'
  result.update(passed=True,cases=cases,actual_production_main_tested=True,maximum_owners=1,both_failures_archived_before_disposition=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 result['closed']=True;put(S/'DISPATCHER_SOFTWARE_PROOF.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
