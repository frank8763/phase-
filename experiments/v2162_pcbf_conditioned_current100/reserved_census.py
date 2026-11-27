"""Tighten exact CLOSED increment uppers; original baseline and all other bands retained."""
from pathlib import Path
import os,subprocess
from context import R,SOURCE as S,read,sha
MIB=1024**2

def admission():
 b=read(S/'BASELINE_DRAFT.json');parent=R/b['parent_baseline_path'];assert sha(parent)==b['parent_baseline_sha256'];old=read(parent)
 assert old['frozen_prior_baseline_bytes']==b['frozen_prior_baseline_bytes']==14873092096
 assert b['limit_bytes']==16106127360 and b['old_joint_peak_upper_bytes']==16095019008
 assert b['task_bytes']==224*MIB and b['archive_bytes']==16*MIB and b['preparation_bytes']==16*MIB and b['download_bytes']==32*MIB and b['metadata_bytes']==8*MIB and b['root_bytes']==512*MIB
 inv=S/'CLOSED_INCREMENT_INVENTORY.json';assert sha(inv)==b['closed_increment_inventory_sha256'];v=read(inv);assert v['passed']and v['credit_bytes']==b['additional_exact_closed_increment_credit_bytes']==19*MIB
 allowed={'preparation_bytes','archive_bytes','all_prior_evidence_upper_bytes','closed_increment_inventory_sha256'}|{g['key']for g in v['groups']}
 for key,value in old.items():
  if key not in allowed:assert b[key]==value,('OLD_BAND_CHANGED',key)
 assert b['all_prior_evidence_upper_bytes']==old['all_prior_evidence_upper_bytes']-v['credit_bytes']+v['new_closed_band_upper_bytes']
 assert v['new_closed_band_upper_bytes']==b['new_closed_band_upper_bytes']==48*MIB
 for group in v['groups']:assert old[group['key']]==group['old_upper']and b[group['key']]==group['new_upper']
 expected={z['path']for z in v['rows']};found=set()
 for group in v['groups']:
  roots=[R/'runs'/n for n in group['roots']]
  assert all(read(root/'DISPATCH_RESULT.json')['closed']for root in roots)
  assert sum(int(subprocess.check_output(['du','-sx','-B1',str(root)],timeout=10).split()[0])for root in roots)<=group['new_upper']
  for root in roots:found.update(str(p.relative_to(R))for p in root.rglob('*')if p.is_file()and not p.is_symlink())
 allocated=0
 for name in v['closed_band_roots']:
  root=R/name;assert root!=R/'runs/v2152_weekend_research_program'
  allocated+=int(subprocess.check_output(['du','-sx','-B1',str(root)],timeout=10).split()[0])
  found.update(str(p.relative_to(R))for p in root.rglob('*')if p.is_file()and not p.is_symlink())
 assert allocated<=v['new_closed_band_upper_bytes']and found==expected,'CLOSED_INVENTORY_PATH_SET_CHANGED'
 for z in v['rows']:
  p=R/z['path'];st=p.stat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==(z['bytes'],z['allocated'],z['mtime_ns'],z['device'],z['inode'])and sha(p)==z['sha256'],'CLOSED_INVENTORY_MEMBER_CHANGED'
 proof=R/'runs/v2145_verified_whole_transport_recovery/RESULT.json';assert sha(proof)==b['verified_duplicate_cleanup_sha256'];credit=read(proof)
 assert credit['passed']and credit['closed']and credit['freed_allocated_bytes']==b['verified_duplicate_credit_bytes']==121692160
 assert all(not(R/z['path']).exists()for z in credit['removed'])
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes'])
 assert peak<=b['old_joint_peak_upper_bytes']<b['limit_bytes']and b['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 own=int(subprocess.check_output(['du','-sx','-B1',str(S)],timeout=10).split()[0])
 for folder in [S/'recovery',S/'runtime_archives',S/'components/PCBF/actual']:
  if folder.exists():own-=int(subprocess.check_output(['du','-sx','-B1',str(folder)],timeout=10).split()[0])
 assert own<=b['preparation_bytes']
 room=b['limit_bytes']-b['all_prior_evidence_upper_bytes']-b['preparation_bytes']-b['metadata_bytes']-(272+512)*MIB
 assert room>=30*MIB,'INITIALIZER_TERMINAL_AND_FIXED_SCOPE_HEADROOM'
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],computed_peak_bytes=peak,limit_bytes=b['limit_bytes'],exact_closed_increment_credit_bytes=v['credit_bytes'],original_frozen_baseline_unchanged=True,original_duplicate_credit_bytes=b['verified_duplicate_credit_bytes'],new_closed_allocated=allocated,preparation_allocated=own,initial_task_root_room_bytes=room,no_deletion=True)

def measure(output,limits):
 from context import O
 b=read(S/'BASELINE_DRAFT.json');output=Path(output).resolve()
 assert output==O/'actual'and os.sched_getaffinity(0)=={2}and limits['maximum_task_evidence_bytes']==224*MIB
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)],timeout=10).split()[0])
 upper=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['retained_future_closed_bytes']+b['metadata_bytes']+b['parallel_math_bytes']+own
 assert upper+(16+32+512)*MIB<=b['old_joint_peak_upper_bytes'];return own,upper

def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*MIB
