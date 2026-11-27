"""Append exact closed increments; retain every prior baseline/band/credit."""
from pathlib import Path
import os,subprocess
from context import R,SOURCE as S,O,read,sha
MIB=1024**2
def admission():
 b=read(S/'BASELINE_DRAFT.json');parent=R/b['parent_baseline_path'];assert sha(parent)==b['parent_baseline_sha256'];old=read(parent)
 allowed={'parent_baseline_path','parent_baseline_sha256','all_prior_evidence_upper_bytes','archive_bytes'}
 for k,v in old.items():
  if k not in allowed:assert b[k]==v,('PRIOR_BAND_CHANGED',k)
 assert b['all_prior_evidence_upper_bytes']==old['all_prior_evidence_upper_bytes']+MIB
 assert b['frozen_prior_baseline_bytes']==14873092096 and b['verified_duplicate_credit_bytes']==121692160 and b['additional_exact_closed_increment_credit_bytes']==19*MIB
 assert b['preparation_bytes']==4*MIB and b['archive_bytes']==12*MIB and b['task_bytes']==224*MIB and b['download_bytes']==32*MIB and b['metadata_bytes']==8*MIB and b['root_bytes']==512*MIB
 p=S/'CLOSED_V2166_V2167_INVENTORY.json';assert sha(p)==b['closed_V2166_V2167_inventory_sha256'];inv=read(p);assert inv['upper_bytes']==MIB
 found=set();allocated=0
 for name in inv['roots']:
  root=R/name;assert root!=R/'runs/v2152_weekend_research_program'
  found.update(str(p.relative_to(R))for p in root.rglob('*')if p.is_file()and not p.is_symlink())
  allocated+=int(subprocess.check_output(['du','-sx','-B1',str(root)],timeout=10).split()[0])
 assert found=={z['path']for z in inv['rows']}and allocated<=MIB,'CLOSED_INCREMENT_PATH_OR_ALLOCATION_CHANGED'
 for z in inv['rows']:
  p=R/z['path'];st=p.stat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==(z['bytes'],z['allocated'],z['mtime_ns'],z['device'],z['inode'])and sha(p)==z['sha256'],'CLOSED_INCREMENT_MEMBER_CHANGED'
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes'])
 assert peak<=b['old_joint_peak_upper_bytes']==16095019008<b['limit_bytes']==16106127360
 assert b['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 own=int(subprocess.check_output(['du','-sx','-B1',str(S)],timeout=10).split()[0])
 for folder in [S/'recovery',S/'runtime_archives',O/'actual']:
  if folder.exists():own-=int(subprocess.check_output(['du','-sx','-B1',str(folder)],timeout=10).split()[0])
 assert own<=b['preparation_bytes']
 room=b['limit_bytes']-b['all_prior_evidence_upper_bytes']-b['preparation_bytes']-b['metadata_bytes']-(272+512)*MIB
 # This short zero-actuation component has the unchanged16MiB initializer
 # grant +1MiB terminal hold +64KiB error reserve. Later writes still receive
 # fresh measured grants; no assumed compression or future credit is spent.
 assert room>=(16+1)*MIB+64*1024+2*4096,'INITIALIZER_TERMINAL_ERROR_HEADROOM'
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],computed_peak_bytes=peak,limit_bytes=b['limit_bytes'],closed_increment_allocated_bytes=allocated,closed_increment_upper_bytes=MIB,preparation_allocated_bytes=own,initial_task_root_room_bytes=room,original_baseline_and_credits_retained=True,no_deletion_or_compression_credit=True,subsequent_capture_grants_still_required=True)
def measure(output,limits):
 b=read(S/'BASELINE_DRAFT.json');output=Path(output).resolve()
 assert output==O/'actual'and os.sched_getaffinity(0)=={2}and limits['maximum_task_evidence_bytes']==224*MIB
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)],timeout=10).split()[0])
 upper=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['retained_future_closed_bytes']+b['metadata_bytes']+b['parallel_math_bytes']+own
 assert upper+(12+32+512)*MIB<=b['old_joint_peak_upper_bytes'];return own,upper
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*MIB
