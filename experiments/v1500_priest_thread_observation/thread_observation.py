"""Two finite live-task censuses. Confirm exited tasks without inventing masks."""
import errno
import os
from pathlib import Path
import time

class ObservationError(AssertionError):
 def __init__(self,reason,proof):
  super().__init__(reason);self.proof=proof

def _observe(phase,scan,query,exists,main_tid):
 proof=dict(phase=phase,started_monotonic=time.monotonic(),passes=[],observed={},confirmed_exited=[],unobserved_final_live=[],historical_transient_affinity_unknown=True,universal_affinity_claim=False,passed=False)
 def refuse(reason):raise ObservationError(reason,proof)
 for index in range(2):
  tids=sorted(scan());proof['passes'].append(tids)
  if not tids or len(tids)>256 or any(not isinstance(t,int)or t<=0 for t in tids):refuse('THREAD_CENSUS_INVALID_OR_LIMIT')
  for tid in tids:
   try:mask=sorted(query(tid))
   except OSError as error:
    if error.errno!=errno.ESRCH:refuse('THREAD_AFFINITY_QUERY_ERROR:'+repr(error))
    if exists(tid):refuse('THREAD_ESRCH_STILL_VISIBLE')
    proof['confirmed_exited'].append(dict(tid=tid,pass_index=index,affinity=None,reason='ESRCH_AND_TASK_PATH_ABSENT'))
    continue
   proof['observed'][str(tid)]=mask
   if mask!=[4]:refuse('PRIEST_OBSERVED_HELPER_AFFINITY_CHANGED')
 final=set(scan());proof['final_live']=sorted(final);proof['unobserved_final_live']=sorted(final-{int(t)for t in proof['observed']})
 if not final or len(final)>256 or main_tid not in final or str(main_tid)not in proof['observed']:refuse('THREAD_MAIN_NOT_OBSERVED_LIVE')
 if proof['unobserved_final_live']:refuse('THREAD_CENSUS_UNSTABLE_UNOBSERVED_LIVE')
 proof.update(passed=True,ended_monotonic=time.monotonic());return proof

def observe(phase):
 task=Path('/proc/self/task')
 return _observe(phase,lambda:[int(p.name)for p in task.iterdir()],os.sched_getaffinity,lambda tid:(task/str(tid)).exists(),os.getpid())
