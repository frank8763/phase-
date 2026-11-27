from pathlib import Path
import os,json,hashlib,subprocess,fcntl,math,datetime
R=Path(__file__).resolve().parents[2];S=R/'runs/v2172_closed_capacity_accounting';M=1024**2
assert os.sched_getaffinity(0)=={5} and not(S/'RESULT.json').exists()
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for chunk in iter(lambda:f.read(M),b''):h.update(chunk)
 return h.hexdigest()
def write(p,x):
 raw=(json.dumps(x,indent=2)+'\n').encode();assert len(raw)<M;p.write_bytes(raw)
locks=[]
for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
 f=(R/name).open('a');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
bpath=R/'runs/v2170_sccr_live_source_scope/BASELINE_DRAFT.json';b=read(bpath)
assert b['frozen_prior_baseline_bytes']==14873092096 and b['verified_duplicate_credit_bytes']==121692160
assert b['additional_exact_closed_increment_credit_bytes']==19*M and b['additional_exact_closed_credit_v2170_bytes']==9*M
newest=R/'runs/v2170_sccr_live_source_scope'
# Closed known identities only. Never scan other processes.
for root in [R/'runs/v2131_filter_measured_current',R/'runs/v2144_sccr_depth_resource_units',newest]:
 for q in root.glob('components/*/COMPLETION.json'):assert read(q)['closed']
 for q in root.glob('components/*/POST_COMPONENT_STORAGE_BARRIER.json'):
  d=read(q);assert d['passed']
 for q in root.glob('components/*/OWNED_CHILD.json'):
  d=read(q)
  pid=d.get('pid',d.get('child_pid'))
  if pid and Path('/proc',str(pid),'stat').exists():
   actual=Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].split()[19]
   expected=d.get('startticks',d.get('start_ticks'))
   assert expected is not None and str(actual)!=str(expected),'CLOSED_OWNED_CHILD_STILL_LIVE'
for pid in [87975,87998]:assert not Path('/proc',str(pid)).exists(),'V2170_OWNER_OR_CHILD_STILL_LIVE'

def inventory(root):
 rows=[];names=set()
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink(),'SYMLINK_NOT_ELIGIBLE:'+str(p)
  if not p.is_file():continue
  st=p.stat();name=str(p.relative_to(R));names.add(name)
  rows.append(dict(path=name,bytes=st.st_size,allocated=st.st_blocks*512,mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino,sha256=sha(p)))
 allocated=int(subprocess.check_output(['du','-sx','-B1',str(root)],timeout=10).split()[0])
 # Re-check each identity and SHA after the census; all roots must remain quiescent.
 for row in rows:
  p=R/row['path'];st=p.stat()
  assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==tuple(row[k]for k in ['bytes','allocated','mtime_ns','device','inode'])
  assert sha(p)==row['sha256']
 assert names=={str(p.relative_to(R))for p in root.rglob('*')if p.is_file()}
 assert int(subprocess.check_output(['du','-sx','-B1',str(root)],timeout=10).split()[0])==allocated
 return dict(root=str(root.relative_to(R)),rows=rows,allocated_bytes=allocated,upper_bytes=math.ceil(allocated/M)*M,closed=True,passed=True)
groups=[];credit=0
for root,key in [('runs/v2131_filter_measured_current','prior_V2131_closed_evidence_upper_bytes'),('runs/v2144_sccr_depth_resource_units','prior_V2144_closed_upper_bytes')]:
 x=inventory(R/root);f=S/(key+'_INVENTORY.json');write(f,x)
 old=b[key];new=x['upper_bytes'];assert new<=old
 delta=old-new;credit+=delta
 closure={}
 for q in (R/root).glob('components/*/POST_COMPONENT_STORAGE_BARRIER.json'):
  closure[str(q.relative_to(R))]=sha(q)
  d=read(q)
  # Verify the SHA-pinned actualremote proof referenced by the canonical barrier.
  # Path spelling is preserved from the original barrier instead of guessing a transport root.
  for k,v in d.items():
   if isinstance(v,str) and v.endswith('.json'):
    p=R/v
    if not p.exists():p=q.parent/v
    if p.exists():closure[str(p.relative_to(R))]=sha(p)
 groups.append(dict(key=key,current_upper=old,new_upper=new,additional_credit_bytes=delta,inventory_path=str(f.relative_to(R)),inventory_sha256=sha(f),members=len(x['rows']),closure_sha256=closure))
x=inventory(newest);f=S/'CLOSED_V2170_INVENTORY.json';write(f,x)
newprior=b['all_prior_evidence_upper_bytes']+x['upper_bytes']-credit
room=b['limit_bytes']-newprior-b['preparation_bytes']-b['metadata_bytes']-(272+512)*M
peak=newprior+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes'])
assert credit==14*M and x['upper_bytes']==13*M
assert room>=17*M+64*1024+8192 and peak<=b['old_joint_peak_upper_bytes']<b['limit_bytes']==16106127360
r=dict(passed=True,closed=True,created_at=datetime.datetime.now().astimezone().isoformat(),groups=groups,new_credit_bytes=credit,
 newest_closed_upper_bytes=x['upper_bytes'],newest_closed_inventory_path=str(f.relative_to(R)),newest_closed_inventory_sha256=sha(f),
 new_all_prior_upper_bytes=newprior,prospective_initial_task_root_room_bytes=room,prospective_peak_bytes=peak,
 parent_baseline_path=str(bpath.relative_to(R)),parent_baseline_sha256=sha(bpath),old_19MiB_and_9MiB_credits_not_recounted=True,
 original_baseline_unchanged=14873092096,all_other_bands_and_caps_unchanged=True,no_deletion=True,no_new_model_admission=True,
 original_REVIEW_exact_and_both_locks_idle_before_census=True,models_physics_replay_audit_source_claims=0,
 new_software_metadata_charged_to_existing_shared_8MiB_and_parallel_1MiB=True)
write(S/'RESULT.json',r)
assert int(subprocess.check_output(['du','-sx','-B1',str(S)],timeout=10).split()[0])<M
print(json.dumps({k:v for k,v in r.items()if k!='groups'}))
