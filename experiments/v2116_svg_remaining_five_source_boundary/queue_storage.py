"""Same144MiB closed reserve, future04..12 only; old evidence in frozen baseline."""
from context import R,SOURCE,STUDY,read,put,sha
from pathlib import Path
import fcntl,subprocess,time
def admit(O):
 from reserved_census import admission
 reserve=admission();rid=O.name;ids=read(SOURCE/'AUTHORIZATION.json')['finite_formal_assignments'];i=ids.index(rid)
 assert not(O/'STORAGE_ADMISSION.json').exists()and not(O/'PILOT_ONCE_CLAIM.json').exists()
 lock=(SOURCE/'retention.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX)
 p=SOURCE/'RETENTION_STATE.json';old=read(p)if p.exists()else dict(last=None,charged=[],retained_actual_bytes=0)
 if i:
  prev=ids[i-1];P=STUDY/'rounds'/prev;assert old['last']==prev and read(P/'POST_ROUND_STORAGE_BARRIER.json')['passed']
  assert read(SOURCE/'closed_cache'/prev/'RESULT.json')['passed'],'CLOSED_CACHE_RETIREMENT_MUST_BE_COMPLETE'
  assert prev not in old['charged'];old['charged'].append(prev)
 else:assert old['last']is None and read(STUDY/'rounds/common_07__SVGMPPI/POST_ROUND_STORAGE_BARRIER.json')['passed']
 sizes={}
 for prev in old['charged']:
  P=STUDY/'rounds'/prev;assert read(P/'COMPLETION.json')['closed']and read(P/'POST_ROUND_STORAGE_BARRIER.json')['passed']
  sizes[prev]=int(subprocess.check_output(['du','-sx','-B1',str(P/'actual')],timeout=10).split()[0])
 old['retained_actual_bytes']=sum(sizes.values());assert old['retained_actual_bytes']<=96*1024**2,'FUTURE_CLOSED96_RESERVE_EXHAUSTED_BEFORE_CLAIM'
 assert sum(x.stat().st_blocks*512 for x in SOURCE.rglob('*')if x.is_file()and not x.is_relative_to(SOURCE/'runtime_archives'))<16*1024**2
 old['last']=rid;put(p,old);put(O/'STORAGE_ADMISSION.json',dict(passed=True,unix=time.time(),joint_peak_bytes=reserve['joint_peak_bytes'],retained_actual_bytes=old['retained_actual_bytes'],frozen_baseline_includes_all_old_cases=True,future_retained_96MiB_only=True,actual_sizes=sizes,no_baseline_renewal=True))
