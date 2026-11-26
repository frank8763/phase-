"""Admit only the next original unclaimed SVG task after evidence closure."""
from context import R,SOURCE,read,put,sha
from pathlib import Path
import fcntl,subprocess,time

def admit(O):
 from reserved_census import admission
 reserve=admission();rows=read(SOURCE/'PLAN_LOCKED.json')['tasks'];row=next(x for x in rows if R/x['root']==O);idx=rows.index(row)
 assert not(O/'STORAGE_ADMISSION.json').exists()and not(O/'PILOT_ONCE_CLAIM.json').exists()
 lock=(SOURCE/'retention.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX)
 statepath=SOURCE/'RETENTION_STATE.json';state=read(statepath)if statepath.exists()else dict(last=None,retained_actual_bytes=0,charged=[])
 if idx:
  prev=rows[idx-1];P=R/prev['root'];assert state['last']==prev['round_id']and read(P/'POST_ROUND_STORAGE_BARRIER.json')['passed']
  i=read(P/'OWNED_CHILD.json');proc=Path('/proc',str(i['pid']),'stat');assert not proc.exists()or proc.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
  assert prev['round_id']not in state['charged'];state['retained_actual_bytes']+=int(subprocess.check_output(['du','-sx','-B1',str(P/'actual')],timeout=10).split()[0]);state['charged'].append(prev['round_id'])
 else:assert state['last']is None
 assert state['retained_actual_bytes']<=144*1024**2,'RETAINED_RESERVATION_EXHAUSTED_BEFORE_CLAIM'
 metadata=sum(p.lstat().st_blocks*512 for p in SOURCE.rglob('*')if p.is_file()and'actual'not in p.relative_to(SOURCE).parts)
 assert metadata+2*1024**2<=16*1024**2,'METADATA_RESERVATION_EXHAUSTED_BEFORE_CLAIM'
 state['last']=row['round_id'];put(statepath,state);put(O/'STORAGE_ADMISSION.json',dict(passed=True,unix=time.time(),joint_peak_bytes=reserve['joint_peak_bytes'],retained_actual_bytes=state['retained_actual_bytes'],metadata_bytes=metadata,no_data_deleted=True))
