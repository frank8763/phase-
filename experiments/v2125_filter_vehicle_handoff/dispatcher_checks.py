"""Exercise production dispatcher.main continuation and technical-stop paths, no models."""
import os,time,types,json,traceback
from pathlib import Path
from context import R,C,SOURCE as S,read,put,load

def main():
 assert os.sched_getaffinity(0)=={4};result=dict(passed=False,models=0,optimizer_queries=0,physical=0);cases=[]
 try:
  for label,technical in[('functional_continue',False),('technical_stop',True)]:
   root=S/'dispatcher_software'/label;root.mkdir(parents=True);fakeR=root/'repo';fakeS=fakeR/'runs/fixture';fakeS.mkdir(parents=True)
   for n in['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
    p=fakeR/n;p.parent.mkdir(parents=True,exist_ok=True);p.touch()
   (fakeR/'REVIEW_PENDING').write_text('explicit software fixture')
   auth=dict(absolute_end_unix=time.time()+18000,required_reserve_before_new_component_s=6900,fixed_order=['PSF','PCBF'])
   b=dict(retained_future_closed_bytes=20*1024**2,all_prior_evidence_upper_bytes=14998921216,preparation_bytes=4*1024**2,metadata_bytes=8*1024**2)
   for n,v in [('POST_SOURCE_STORAGE_BARRIER.json',dict(passed=True)),('SOURCE_FREEZE.json',dict(files={})),('AUTHORIZATION.json',auth),('BASELINE_DRAFT.json',b),('CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(source_commit='software_only'))]:put(fakeS/n,v)
   for method in['PSF','PCBF']:(fakeS/'components'/method).mkdir(parents=True)
   d=load('FILTER_actual_dispatcher_fixture_'+label,C/'dispatcher.py');d.R=fakeR;d.S=fakeS;d.ready=lambda:True;d.sha=lambda p:'4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';d.subprocess=types.SimpleNamespace(check_output=lambda *a,**kw:b'1\tfixture\n')
   # Change own affinity calls only within this explicit software fixture.
   d.os=types.SimpleNamespace(sched_setaffinity=lambda *a:None,nice=lambda *a:None,getpriority=lambda *a:19,PRIO_PROCESS=os.PRIO_PROCESS,getpid=os.getpid)
   calls=[]
   def process(name,argv,cap,*,method=None):
    calls.append(name);O=fakeS/'components'/method
    if name.endswith('_owner'):
     error='TECHNICAL_FAULT'if technical and method=='PSF'else'FILTER_CURRENT_CYCLE_COMPLETE_STOP_REFUSED'
     put(O/'COMPLETION.json',dict(closed=True,passed=False,all_source_SHA_after_child=True,actual_native=200,own_replay_native=200,independent_audit=dict(passed=True),machine_secondary_errors=[],machine_first_error=dict(error=error)))
    elif name.endswith('_delivery'):
     t=fakeS/'runtime_archives'/method;t.mkdir(parents=True);put(t/'FULL_REMOTE_VERIFIED.json',dict(passed=True));put(t/'TRANSPORT_CLEANUP.json',dict(passed=True))
    return 1 if name.endswith('_owner')else 0
   d.process=process;d.main();answer=read(fakeS/'DISPATCH_RESULT.json')
   assert calls.count('PSF_owner')==1 and calls.count('PCBF_owner')==(0 if technical else 1)
   assert answer['finite_queue_completed']is(not technical)
   cases.append(dict(case=label,calls=calls,finite_completed=answer['finite_queue_completed']))
  # Real ready() sees a completed prerequisite whose actual writer is still alive.
  d=load('FILTER_actual_ready_fixture',C/'dispatcher.py');f=S/'dispatcher_software/ready';prior=f/'runs/v2122_priest_quiescent_handoff';prior.mkdir(parents=True)
  put(prior/'DISPATCH_RESULT.json',dict(closed=True,remote_and_cleanup_closed=True));i=dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19]);put(prior/'LAUNCH_IDENTITY.json',i)
  d.R=f;calls=[];d.predecessors_closed=lambda:calls.append(True)or True;assert d.ready()is False and not calls
  for n in['LAUNCH_IDENTITY.json','workers/vehicle_owner.IDENTITY.json','vehicle/OWNED_CHILD.json']:
   p=prior/n;p.parent.mkdir(parents=True,exist_ok=True);put(p,dict(i,start_ticks='0'))
  assert d.ready()is True and calls==[True]
  assert d.decision(False,True,False)=='WAIT'and d.decision(True,False,False)=='DEADLINE_STOP'and d.decision(True,True,True)=='USER_STOP'
  result.update(passed=True,cases=cases,actual_production_main_tested=True,closed_result_before_parent_exit_waits=True,one_owner_per_method=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 result['closed']=True;put(S/'DISPATCHER_SOFTWARE_PROOF.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
