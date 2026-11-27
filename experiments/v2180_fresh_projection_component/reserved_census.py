"""Charge exact closed predecessor increment, keep original baseline and all caps."""
from context import R,C,SOURCE as ROOT,read,put,sha,predecessors_closed
from pathlib import Path
import os,subprocess,math,fcntl
P=R/'runs/v2177_priest_vector_orientation'
M=1024**2
BANDS=['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes']
def idle():
 handles=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);handles.append(f)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert predecessors_closed();return handles
def inventory():
 assert not(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json').exists();handles=idle();rows=[]
 for p in sorted(P.rglob('*')):
  if not(p.is_symlink()or p.is_file()):continue
  st=p.lstat();link=os.readlink(p)if p.is_symlink()else None
  rows.append(dict(path=str(p.relative_to(R)),bytes=st.st_size,allocated=st.st_blocks*512,mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino,sha256=__import__('hashlib').sha256(os.fsencode(link)).hexdigest()if link is not None else sha(p),link=link))
 allocated=int(subprocess.check_output(['du','-sx','-B1',str(P)]).split()[0]);upper=math.ceil(allocated/M)*M
 put(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json',dict(passed=True,rows=rows,allocated_bytes=allocated,upper_bytes=upper,closed=True));validate_inventory()
 b=read(P/'BASELINE_DRAFT.json');assert b['all_prior_evidence_upper_bytes']==15261007872 and b['frozen_prior_baseline_bytes']==14873092096
 b.update(parent_baseline_path=str((P/'BASELINE_DRAFT.json').relative_to(R)),parent_baseline_sha256=sha(P/'BASELINE_DRAFT.json'),prior_V2177_closed_upper_bytes=upper,closed_V2177_inventory_sha256=sha(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json'),all_prior_evidence_upper_bytes=b['all_prior_evidence_upper_bytes']+upper,archive_bytes=12*M,source_archive_upper_bytes=2*M,runtime_archive_upper_bytes=22*M,parallel_math_bytes=0)
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in BANDS);assert peak<=b['old_joint_peak_upper_bytes']<b['limit_bytes'];b['held_peak_bytes']=peak;put(ROOT/'BASELINE_DRAFT.json',b);return admission()
def validate_inventory():
 x=read(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json');names=set()
 for row in x['rows']:
  p=R/row['path'];st=p.lstat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==tuple(row[k]for k in ['bytes','allocated','mtime_ns','device','inode'])
  assert(__import__('hashlib').sha256(os.fsencode(os.readlink(p))).hexdigest()if row['link']is not None else sha(p))==row['sha256'];names.add(p)
 assert names=={p for p in P.rglob('*')if p.is_symlink()or p.is_file()};assert int(subprocess.check_output(['du','-sx','-B1',str(P)]).split()[0])==x['allocated_bytes'];return x
def admission():
 b=read(ROOT/'BASELINE_DRAFT.json');assert sha(P/'BASELINE_DRAFT.json')==b['parent_baseline_sha256'];assert sha(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json')==b['closed_V2177_inventory_sha256'];validate_inventory()
 proof=read(ROOT/'ADDITIONAL_CLOSED_PRIEST_CREDIT.json');assert proof['passed']and sha(ROOT/'ADDITIONAL_CLOSED_PRIEST_CREDIT.json')==b['additional_exact_closed_PRIEST_credit_sha256']and sha(ROOT/'CLOSED_PRIEST_INVENTORY.json')==b['closed_PRIEST_inventory_sha256']
 credit_inventory=read(ROOT/'CLOSED_PRIEST_INVENTORY.json')
 for row in credit_inventory['rows']:
  p=R/row['path'];st=p.lstat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==tuple(row[k]for k in ['bytes','allocated','mtime_ns','device','inode']);assert(__import__('hashlib').sha256(os.fsencode(os.readlink(p))).hexdigest()if row['link']is not None else sha(p))==row['sha256']
 assert {z['path']for z in credit_inventory['rows']}=={str(p.relative_to(R))for name in credit_inventory['roots']for p in (R/name).rglob('*')if p.is_file()or p.is_symlink()}
 assert b['all_prior_evidence_upper_bytes']==read(P/'BASELINE_DRAFT.json')['all_prior_evidence_upper_bytes']+b['prior_V2177_closed_upper_bytes']-proof['additional_credit_bytes']and b['prior_PRIEST_closed_evidence_upper_bytes']==proof['new_PRIEST_band']
 own=int(subprocess.check_output(['du','-sx','-B1',str(ROOT)]).split()[0])
 for folder in [ROOT/'recovery',ROOT/'runtime_archives',ROOT/'components/PROJ/actual']:
  if folder.exists():own-=int(subprocess.check_output(['du','-sx','-B1',str(folder)]).split()[0])
 assert own<4*M,'OWN_PREPARATION_4MiB'
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in BANDS);assert peak==b['held_peak_bytes']<=b['old_joint_peak_upper_bytes']<16106127360
 actual=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],timeout=20).split()[0]);assert actual+(24+32+512)*M<16106127360,'ACTUAL_CROSSCHECK_ONLY_NOT_BASELINE_RESET'
 room=b['limit_bytes']-b['all_prior_evidence_upper_bytes']-b['preparation_bytes']-b['metadata_bytes']-(272+512)*M;assert room>=17*M+64*1024+8192
 return dict(passed=True,initial_task_root_room_bytes=room,joint_peak_bytes=peak,own_allocated_bytes=own,original_baseline=b['frozen_prior_baseline_bytes'],actual_all_runs_crosscheck_bytes=actual,models_authorized=False,source_archive_upper_bytes=2*M,runtime_archive_upper_bytes=22*M)
def measure(output,limits):
 b=read(ROOT/'BASELINE_DRAFT.json');output=Path(output).resolve();assert output==ROOT/'components/PROJ/actual'and os.sched_getaffinity(0)=={2}and limits['maximum_task_evidence_bytes']==224*M
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)]).split()[0]);upper=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['metadata_bytes']+own
 assert upper+(24+32+512)*M<=b['old_joint_peak_upper_bytes'];return own,upper
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*M
if __name__=='__main__':print(__import__('json').dumps(inventory()))
