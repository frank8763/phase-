"""Adopt only exact C2172 closed increment accounting, no renewed global baseline."""
from context import R,SOURCE as S,O,read,sha
from pathlib import Path
import os,subprocess,hashlib
M=1024**2

def exact_inventory(path):
 data=read(path);root=R/data['root'];rows=data['rows'];actual={str(p.relative_to(R))for p in root.rglob('*')if p.is_symlink()or p.is_file()}
 assert actual=={z['path']for z in rows},'CLOSED_PATH_SET_CHANGED'
 for z in rows:
  p=R/z['path'];link=z.get('kind')=='symlink_not_followed';st=p.lstat()if link else p.stat()
  assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==tuple(z[k]for k in ['bytes','allocated','mtime_ns','device','inode']),'CLOSED_MEMBER_IDENTITY_CHANGED:'+z['path']
  h=hashlib.sha256(os.fsencode(os.readlink(p))).hexdigest()if link else sha(p);assert h==z['sha256'],'CLOSED_MEMBER_SHA_CHANGED:'+z['path']
 allocated=int(subprocess.check_output(['du','-sx','-B1',str(root)],timeout=10).split()[0]);assert allocated==data['allocated_bytes']and allocated<=data['upper_bytes']
 return allocated

def admission():
 b=read(S/'BASELINE_DRAFT.json');parent=R/b['parent_baseline_path'];assert sha(parent)==b['parent_baseline_sha256'];old=read(parent)
 credit_path=R/b['closed_capacity_accounting_path'];assert sha(credit_path)==b['closed_capacity_accounting_sha256'];credit=read(credit_path)
 chain=R/'runs/v2172_closed_capacity_accounting/CLOSURE_CHAIN_CHECK.json';assert sha(chain)==b['closed_capacity_chain_sha256']and read(chain)['passed']and read(chain)['accounting_result_sha256']==sha(credit_path)
 allowed={'parent_baseline_path','parent_baseline_sha256','all_prior_evidence_upper_bytes','archive_bytes','runtime_archive_upper_bytes'}|{g['key']for g in credit['groups']}
 for k,v in old.items():
  if k not in allowed:assert b[k]==v,('OLD_BAND_CHANGED',k)
 assert credit['new_credit_bytes']==b['additional_exact_closed_credit_v2176_bytes']==14*M and credit['newest_closed_upper_bytes']==b['prior_V2170_closed_upper_bytes']==13*M
 for g in credit['groups']:
  p=R/g['inventory_path'];assert sha(p)==g['inventory_sha256'];assert old[g['key']]==g['current_upper']and b[g['key']]==g['new_upper'];assert exact_inventory(p)<=g['new_upper']
 p=R/credit['newest_closed_inventory_path'];assert sha(p)==credit['newest_closed_inventory_sha256'];assert exact_inventory(p)<=13*M
 assert b['all_prior_evidence_upper_bytes']==old['all_prior_evidence_upper_bytes']+13*M-14*M==credit['new_all_prior_upper_bytes']
 assert b['frozen_prior_baseline_bytes']==14873092096 and b['verified_duplicate_credit_bytes']==121692160 and b['additional_exact_closed_increment_credit_bytes']==19*M and b['additional_exact_closed_credit_v2170_bytes']==9*M
 assert b['preparation_bytes']==4*M and b['archive_bytes']==26*M and b['task_bytes']==224*M and b['download_bytes']==32*M and b['metadata_bytes']==8*M and b['root_bytes']==512*M
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes']);assert peak<=b['old_joint_peak_upper_bytes']==16095019008<b['limit_bytes']==16106127360
 assert b['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 own=int(subprocess.check_output(['du','-sx','-B1',str(S)],timeout=10).split()[0])
 for folder in [S/'recovery',S/'runtime_archives',O/'actual']:
  if folder.exists():own-=int(subprocess.check_output(['du','-sx','-B1',str(folder)],timeout=10).split()[0])
 assert own<=b['preparation_bytes'];room=b['limit_bytes']-b['all_prior_evidence_upper_bytes']-b['preparation_bytes']-b['metadata_bytes']-(272+512)*M;assert room>=17*M+64*1024+8192
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],computed_peak_bytes=peak,initial_task_root_room_bytes=room,preparation_allocated_bytes=own,additional_exact_closed_credit_bytes=14*M,charged_new_closed_V2170_bytes=13*M,old_19MiB_and_9MiB_credits_not_recounted=True,original_global_task_IO_root_caps_and_baseline_unchanged=True,new_component_archive_allocation_bytes=26*M,no_deletion_or_compression_credit=True)
def measure(output,limits):
 b=read(S/'BASELINE_DRAFT.json');output=Path(output).resolve();assert output==O/'actual'and os.sched_getaffinity(0)=={2}and limits['maximum_task_evidence_bytes']==224*M
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)],timeout=10).split()[0]);upper=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['retained_future_closed_bytes']+b['metadata_bytes']+b['parallel_math_bytes']+own
 assert upper+(26+32+512)*M<=b['old_joint_peak_upper_bytes'];return own,upper
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*M
