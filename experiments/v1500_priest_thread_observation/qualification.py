"""New metadata target only: a real thread exit, strict negative queries, AST reuse."""
import ast
import errno
import importlib.util
import json
import os
from pathlib import Path
import threading
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def qualify():
 assert sorted(os.sched_getaffinity(0))==[4]
 observer=load('v1500_new_metadata_target',C/'thread_observation.py')
 live=observer.observe('NEW_SOURCE_METADATA_ENTRY')
 stop=threading.Event();ready=threading.Event();identity=[]
 def temporary():identity.append(threading.get_native_id());ready.set();stop.wait(2)
 thread=threading.Thread(target=temporary);thread.start();assert ready.wait(1);tid=identity[0];real=os.sched_getaffinity
 task=Path('/proc/self/task');scan=lambda:[int(p.name)for p in task.iterdir()]
 def exit_at_query(value):
  if value==tid:stop.set();thread.join(1);assert not thread.is_alive()
  return real(value)
 try:race=observer._observe('REAL_THREAD_EXIT_BETWEEN_ENUMERATION_AND_QUERY',scan,exit_at_query,lambda value:(task/str(value)).exists(),os.getpid())
 finally:stop.set();thread.join(1)
 assert race['passed']and any(v['tid']==tid and v['affinity']is None for v in race['confirmed_exited'])
 negatives=[]
 def bad(name,scan,query,exists):
  try:observer._observe(name,scan,query,exists,os.getpid())
  except observer.ObservationError as error:negatives.append(dict(name=name,error=str(error),proof=error.proof))
  else:raise AssertionError('THREAD_NEGATIVE_ACCEPTED:'+name)
 main=os.getpid()
 bad('OBSERVED_NON_CPU4',lambda:[main],lambda _: {5},lambda _:True)
 def denied(_):raise PermissionError(errno.EPERM,'injected query denial')
 bad('NON_ESRCH',lambda:[main],denied,lambda _:True)
 def esrch(_):raise ProcessLookupError(errno.ESRCH,'injected visible query failure')
 bad('ESRCH_STILL_VISIBLE',lambda:[main],esrch,lambda _:True)
 calls=[0]
 def changing():calls[0]+=1;return [main]if calls[0]<=2 else [main,2147483000]
 bad('UNOBSERVED_FINAL_TASK',changing,lambda _:{4},lambda _:True)
 # Exact numerical call graph and loader are changed only at admission path.
 old=R/'experiments/v1498_priest_saved_proposal'
 for name in ['optimizer_call.py','kernel_loader.py']:
  expected=(old/name).read_text().replace('runs/v1498_priest_saved_proposal/OPTIMIZER_ONLY_ADMISSION.json','runs/v1500_priest_thread_observation/OPTIMIZER_ONLY_ADMISSION.json')
  assert ast.dump(ast.parse(expected))==ast.dump(ast.parse((C/name).read_text()))
 for name in ['common.py','sandbox.py']:assert(C/name).read_bytes()==(old/name).read_bytes()
 proof=dict(passed=True,scope='NEW_THREAD_METADATA_SOURCE_ONLY',real_live_census=live,actual_thread_exit= race,negative_cases=negatives,original_numerical_body_and_callgraph_AST_exact=True,unchanged_OS_target_not_rerun=True,original_V1498_failure_preserved=True,JAX_or_author_imported=False,optimizer_calls=0,models=0,physical_native=0)
 (O/'THREAD_OBSERVATION_QUALIFICATION.json').write_text(json.dumps(proof,indent=2,allow_nan=False)+'\n')
 return proof
