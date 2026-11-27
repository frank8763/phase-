"""One exact fully closed V2168 increment, no baseline reset or deleted evidence."""
from context import R,SOURCE as S,O,read,sha
from pathlib import Path
import os,subprocess
MIB=1024**2
def admission():
 b=read(S/'BASELINE_DRAFT.json');p=R/b['parent_baseline_path'];assert sha(p)==b['parent_baseline_sha256'];old=read(p)
 for k,v in old.items():
  if k not in {'parent_baseline_path','parent_baseline_sha256','all_prior_evidence_upper_bytes'}:assert b[k]==v,('OLD_BAND_CHANGED',k)
 assert b['all_prior_evidence_upper_bytes']==old['all_prior_evidence_upper_bytes']+MIB and b['frozen_prior_baseline_bytes']==14873092096
 inv=S/'CLOSED_V2168_INVENTORY.json';assert sha(inv)==b['closed_V2168_inventory_sha256'];v=read(inv);root=R/v['root']
 assert{str(p.relative_to(R))for p in root.rglob('*')if p.is_file()and not p.is_symlink()}=={x['path']for x in v['rows']}
 size=int(subprocess.check_output(['du','-sx','-B1',str(root)],timeout=10).split()[0]);assert size<=v['upper_bytes']==MIB
 for row in v['rows']:
  p=R/row['path'];st=p.stat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==(row['bytes'],row['allocated'],row['mtime_ns'],row['device'],row['inode'])and sha(p)==row['sha256']
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes'])
 assert peak<=b['old_joint_peak_upper_bytes']==16095019008<b['limit_bytes']==16106127360
 assert b['preparation_bytes']==4*MIB and b['archive_bytes']==12*MIB and b['task_bytes']==224*MIB and b['root_bytes']==512*MIB and b['download_bytes']==32*MIB and b['metadata_bytes']==8*MIB
 assert b['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 own=int(subprocess.check_output(['du','-sx','-B1',str(S)],timeout=10).split()[0])
 for folder in [S/'recovery',S/'runtime_archives',O/'actual']:
  if folder.exists():own-=int(subprocess.check_output(['du','-sx','-B1',str(folder)],timeout=10).split()[0])
 assert own<=b['preparation_bytes']
 room=b['limit_bytes']-b['all_prior_evidence_upper_bytes']-b['preparation_bytes']-b['metadata_bytes']-(272+512)*MIB;assert room>=17*MIB+64*1024+8192
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],computed_peak_bytes=peak,closed_V2168_allocated_bytes=size,closed_V2168_upper_bytes=MIB,preparation_allocated_bytes=own,initial_task_root_room_bytes=room,all_caps_baseline_bands_credits_unchanged=True,no_deletion_or_compression_credit=True)
def measure(output,limits):
 b=read(S/'BASELINE_DRAFT.json');output=Path(output).resolve();assert output==O/'actual'and os.sched_getaffinity(0)=={2}and limits['maximum_task_evidence_bytes']==224*MIB
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)],timeout=10).split()[0]);upper=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['retained_future_closed_bytes']+b['metadata_bytes']+b['parallel_math_bytes']+own
 assert upper+(12+32+512)*MIB<=b['old_joint_peak_upper_bytes'];return own,upper
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*MIB
