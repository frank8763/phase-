"""Move the previous closed case into a bounded retained-evidence reservation."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];S=R/'runs/v2045_remaining_parallel_source'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<2*1024**2;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def admit(O):
 plan=read(S/'PLAN_LOCKED.json');row=next(x for rows in plan['methods'].values()for x in rows if R/x['root']==O);method=row['method'];rows=plan['methods'][method];idx=rows.index(row);proof=O/'STORAGE_ADMISSION.json';assert not proof.exists()and not(O/'PILOT_ONCE_CLAIM.json').exists()
 from reserved_census import global_admission
 reserve=global_admission(require_launch=True);lock=(S/'retention.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX)
 statepath=S/'RETENTION_STATE.json';state=read(statepath)if statepath.exists()else dict(prior_closed_actual_allocated_bytes=0,lanes={},charged_previous_cases=[])
 if idx==0:
  assert method not in state['lanes'];prior=plan['prior_closed_barriers'][method];p=R/prior['prior_path'];assert sha(p)==prior['sha256']and read(p)['passed']
 else:
  prev=rows[idx-1];assert state['lanes'][method]==prev['round_id'];P=R/prev['root'];assert read(P/'POST_ROUND_STORAGE_BARRIER.json')['passed'];i=read(P/'OWNED_CHILD.json');q=Path('/proc',str(i['pid']));assert not q.exists()or q.joinpath('stat').read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
  value=int(subprocess.check_output(['du','-sx','-B1',str(P/'actual')],timeout=10).split()[0]);assert prev['round_id']not in state['charged_previous_cases'];state['prior_closed_actual_allocated_bytes']+=value;state['charged_previous_cases'].append(prev['round_id'])
  assert state['prior_closed_actual_allocated_bytes']<=144*1024**2,'RETAINED_CLOSED_CASE_RESERVATION_EXHAUSTED_BEFORE_NEW_FORMAL_CLAIM'
 # Own prior rounds and transports are closed, and this is the sole lane writer.
 metadata=0
 for item in rows:
  for folder in [R/item['root'],S/'runtime_archives'/item['round_id']]:
   if not folder.exists():continue
   for p in folder.rglob('*'):
    if p.is_file()and 'actual'not in p.relative_to(folder).parts:metadata+=p.lstat().st_blocks*512
 assert metadata+2*1024**2<=16*1024**2,'LANE_METADATA_RESERVATION_EXHAUSTED_BEFORE_CLAIM'
 state['lanes'][method]=row['round_id'];put(statepath,state);put(proof,dict(passed=True,method=method,round_id=row['round_id'],prior_closed_actual_allocated_bytes=state['prior_closed_actual_allocated_bytes'],prior_closed_reserve_bytes=144*1024**2,own_prior_metadata_allocated_bytes=metadata,joint_peak_bytes=reserve['joint_peak_bytes'],no_global_live_du=True,no_cold_cache_deletion=True,unix=time.time()))
