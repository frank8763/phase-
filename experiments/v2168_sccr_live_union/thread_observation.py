"""Bind inherited procfs task IDs to current PID namespace before affinity query."""
import errno
import hashlib
import os
from pathlib import Path
import time

class ObservationError(AssertionError):
 def __init__(self,message,proof):super().__init__(message);self.proof=proof

def fields(text):
 result={}
 for line in text.splitlines():
  if ':'in line:
   k,v=line.split(':',1)
   if k in {'Pid','Tgid','NSpid'}:result[k]=[int(x)for x in v.split()]
 assert all(k in result for k in ['Pid','Tgid','NSpid']),'THREAD_NSPID_FIELDS_ABSENT'
 return result

def bind_status(text,proc_tid,process):
 value=fields(text);chain=value['NSpid']
 assert value['Pid']==[proc_tid]and value['Tgid']==process['Tgid'],'THREAD_PROC_ID_OR_GROUP_CHANGED'
 assert chain and chain[0]==proc_tid and len(chain)==len(process['NSpid'])and all(x>0 for x in chain),'THREAD_NSPID_CHAIN_INVALID'
 return dict(proc_tid=proc_tid,current_namespace_tid=chain[-1],NSpid=chain,status_sha256=hashlib.sha256(text.encode()).hexdigest())

def observe(phase):
 task=Path('/proc/self/task');process=fields(Path('/proc/self/status').read_text());main=os.getpid()
 proof=dict(phase=phase,started_monotonic=time.monotonic(),current_namespace_pid=main,procfs_process_ids=process,pid_namespace=os.readlink('/proc/self/ns/pid'),passes=[],observed={},confirmed_exited=[],passed=False,historical_transient_affinity_unknown=True,universal_affinity_claim=False)
 def refuse(reason):raise ObservationError(reason,proof)
 if not process['NSpid']or process['NSpid'][-1]!=main:refuse('THREAD_PROCESS_NAMESPACE_NOT_BOUND')
 def scan():
  raw=sorted(int(p.name)for p in task.iterdir())
  if not raw or len(raw)>256:refuse('THREAD_CENSUS_LIMIT')
  records=[]
  for tid in raw:
   try:text=(task/str(tid)/'status').read_text()
   except FileNotFoundError:proof['confirmed_exited'].append(dict(proc_tid=tid,current_namespace_tid=None,affinity=None,reason='STATUS_DISAPPEARED'));continue
   try:records.append(bind_status(text,tid,process))
   except AssertionError as error:refuse(str(error))
  return records
 for index in range(2):
  records=scan();proof['passes'].append(records)
  for record in records:
   tid=record['current_namespace_tid'];key=str(record['proc_tid'])+':'+str(tid)
   try:mask=sorted(os.sched_getaffinity(tid))
   except OSError as error:
    if error.errno!=errno.ESRCH:refuse('THREAD_AFFINITY_QUERY_ERROR:'+repr(error))
    if(task/str(record['proc_tid'])).exists():refuse('THREAD_MAPPED_ESRCH_STILL_VISIBLE')
    proof['confirmed_exited'].append(dict(record,pass_index=index,affinity=None,reason='MAPPED_ESRCH_AND_PROC_PATH_ABSENT'));continue
   proof['observed'][key]=dict(record,affinity=mask)
   if mask!=[6]:refuse('PRIEST_OBSERVED_HELPER_AFFINITY_CHANGED')
 final=scan();proof['final_live']=final;unseen=[v for v in final if str(v['proc_tid'])+':'+str(v['current_namespace_tid'])not in proof['observed']];proof['unobserved_final_live']=unseen
 if unseen or not any(v['current_namespace_tid']==main for v in final):refuse('THREAD_FINAL_LIVE_NOT_OBSERVED')
 proof.update(passed=True,ended_monotonic=time.monotonic());return proof
