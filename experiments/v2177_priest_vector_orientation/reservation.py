"""Charge exact closed predecessor increment, keep original baseline and all caps."""
from context import R,C,ROOT,P,read,put,sha,predecessor_closed
from pathlib import Path
import os,subprocess,math,fcntl
M=1024**2
BANDS=['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes']
def idle():
 handles=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);handles.append(f)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert predecessor_closed();return handles
def inventory():
 assert not(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json').exists();handles=idle();rows=[]
 for p in sorted(P.rglob('*')):
  if not(p.is_symlink()or p.is_file()):continue
  st=p.lstat();link=os.readlink(p)if p.is_symlink()else None
  rows.append(dict(path=str(p.relative_to(R)),bytes=st.st_size,allocated=st.st_blocks*512,mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino,sha256=__import__('hashlib').sha256(os.fsencode(link)).hexdigest()if link is not None else sha(p),link=link))
 allocated=int(subprocess.check_output(['du','-sx','-B1',str(P)]).split()[0]);upper=math.ceil(allocated/M)*M
 put(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json',dict(passed=True,rows=rows,allocated_bytes=allocated,upper_bytes=upper,closed=True));validate_inventory()
 b=read(P/'BASELINE_DRAFT.json');assert b['all_prior_evidence_upper_bytes']==15249473536 and b['frozen_prior_baseline_bytes']==14873092096
 b.update(parent_baseline_path=str((P/'BASELINE_DRAFT.json').relative_to(R)),parent_baseline_sha256=sha(P/'BASELINE_DRAFT.json'),prior_V2176_closed_upper_bytes=upper,closed_V2176_inventory_sha256=sha(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json'),all_prior_evidence_upper_bytes=b['all_prior_evidence_upper_bytes']+upper,archive_bytes=4*M,source_archive_upper_bytes=2*M,runtime_archive_upper_bytes=2*M,parallel_math_bytes=M)
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in BANDS);assert peak<=b['old_joint_peak_upper_bytes']<b['limit_bytes'];b['held_peak_bytes']=peak;put(ROOT/'BASELINE_DRAFT.json',b);return admission()
def validate_inventory():
 x=read(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json');names=set()
 for row in x['rows']:
  p=R/row['path'];st=p.lstat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==tuple(row[k]for k in ['bytes','allocated','mtime_ns','device','inode'])
  assert(__import__('hashlib').sha256(os.fsencode(os.readlink(p))).hexdigest()if row['link']is not None else sha(p))==row['sha256'];names.add(p)
 assert names=={p for p in P.rglob('*')if p.is_symlink()or p.is_file()};assert int(subprocess.check_output(['du','-sx','-B1',str(P)]).split()[0])==x['allocated_bytes'];return x
def admission():
 b=read(ROOT/'BASELINE_DRAFT.json');assert sha(P/'BASELINE_DRAFT.json')==b['parent_baseline_sha256'];assert sha(ROOT/'CLOSED_PREDECESSOR_INVENTORY.json')==b['closed_V2176_inventory_sha256'];validate_inventory()
 own=int(subprocess.check_output(['du','-sx','-B1',str(ROOT)]).split()[0]);assert own<12*M,'OWN_PREP_MATH_ARCHIVE_METADATA_4_1_4_3_MiB'
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in BANDS);assert peak==b['held_peak_bytes']<=b['old_joint_peak_upper_bytes']<16106127360
 actual=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],timeout=20).split()[0]);assert actual+(4+32+512)*M<16106127360,'ACTUAL_CROSSCHECK_ONLY_NOT_BASELINE_RESET'
 return dict(passed=True,joint_peak_bytes=peak,own_allocated_bytes=own,original_baseline=b['frozen_prior_baseline_bytes'],actual_all_runs_crosscheck_bytes=actual,models_authorized=False,maximum_math_write_bytes=M)
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*M
if __name__=='__main__':print(__import__('json').dumps(inventory()))
