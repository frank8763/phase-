"""Retain parent baseline and every band; add only exact closed16MiB upper."""
from common import R,S,read,sha
from pathlib import Path
import subprocess
M=1024**2
def admission():
 b=read(S/'BASELINE_DRAFT.json');p=R/b['parent_baseline_path'];assert sha(p)==b['parent_baseline_sha256'];old=read(p)
 for k,v in old.items():
  if k not in {'parent_baseline_path','parent_baseline_sha256','preparation_bytes','all_prior_evidence_upper_bytes'}:assert b[k]==v,('OLD_BUDGET_BAND_CHANGED',k)
 assert b['all_prior_evidence_upper_bytes']==old['all_prior_evidence_upper_bytes']+16*M and b['frozen_prior_baseline_bytes']==14873092096
 assert b['preparation_bytes']==4*M and b['archive_bytes']==16*M and b['task_bytes']==224*M and b['metadata_bytes']==8*M and b['download_bytes']==32*M and b['root_bytes']==512*M
 inv=S/'CLOSED_PARENT_INVENTORY.json';assert sha(inv)==b['new_closed_scope_inventory_sha256'];v=read(inv);found=set();allocated=0
 for n in v['roots']:
  folder=R/n;allocated+=int(subprocess.check_output(['du','-sx','-B1',str(folder)],timeout=10).split()[0]);found.update(str(p.relative_to(R))for p in folder.rglob('*')if p.is_file()and not p.is_symlink())
 assert found=={z['path']for z in v['rows']}and allocated<=v['upper']==16*M
 for z in v['rows']:
  p=R/z['path'];st=p.stat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==(z['bytes'],z['allocated'],z['mtime_ns'],z['device'],z['inode'])and sha(p)==z['sha256']
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes']);assert peak<=b['old_joint_peak_upper_bytes']==16095019008<b['limit_bytes']==16106127360
 assert b['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 own=int(subprocess.check_output(['du','-sx','-B1',str(S)],timeout=10).split()[0])
 for folder in [S/'recovery',S/'runtime_archives',S/'components/POLICY']:
  if folder.exists():own-=int(subprocess.check_output(['du','-sx','-B1',str(folder)],timeout=10).split()[0])
 assert own<=b['preparation_bytes']
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],computed_peak_bytes=peak,closed_parent_allocated=allocated,closed_parent_upper_bytes=16*M,original_baseline_unchanged=True,original_task_IO_root_limit_unchanged=True)
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*M
