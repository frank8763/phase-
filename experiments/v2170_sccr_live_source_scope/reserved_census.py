"""Validate only explicit additional CLOSED credits, retain every other old band."""
from context import R,SOURCE as S,O,read,sha
from pathlib import Path
import os,subprocess,hashlib
M=1024**2
def exact_inventory(root,rows):
 found={str(p.relative_to(R))for p in root.rglob('*')if p.is_file()and not p.is_symlink()};assert found==set(rows),'CLOSED_SOURCE_PATH_SET_CHANGED'
 for n,row in rows.items():
  p=R/n;st=p.stat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==(row['bytes'],row['allocated'],row['mtime_ns'],row['device'],row['inode'])and sha(p)==row['sha256'],'CLOSED_SOURCE_IDENTITY_CHANGED:'+n
 return int(subprocess.check_output(['du','-sx','-B1',str(root)],timeout=10).split()[0])
def admission():
 b=read(S/'BASELINE_DRAFT.json');parent=R/b['parent_baseline_path'];assert sha(parent)==b['parent_baseline_sha256'];old=read(parent)
 p=S/'ADDITIONAL_CLOSED_UPPER_CREDIT.json';assert sha(p)==b['additional_closed_credit_v2170_sha256'];credit=read(p);assert credit['passed']and credit['new_additional_credit_bytes']==b['additional_exact_closed_credit_v2170_bytes']==9*M
 allowed={'parent_baseline_path','parent_baseline_sha256','all_prior_evidence_upper_bytes'}|{g['key']for g in credit['groups']}
 for k,v in old.items():
  if k not in allowed:assert b[k]==v,('OLD_BAND_CHANGED',k)
 tables={};checked=0
 for g in credit['groups']:
  inv=R/g['inventory_path'];assert sha(inv)==g['inventory_sha256'];name=str(inv)
  if name not in tables:tables[name]={x['path']:x for x in read(inv)['rows']}
  allocated=0;found=set()
  for n in g['roots']:
   rows={k:v for k,v in tables[name].items()if k.startswith(n+'/')};allocated+=exact_inventory(R/n,rows);found.update(rows);checked+=len(rows)
  assert allocated==g['actual_allocated_with_directories']and allocated<=g['new_upper']==b[g['key']]and g['current_upper']==old[g['key']]
  assert hashlib.sha256('\n'.join(sorted(found)).encode()).hexdigest()==g['path_set_sha256']
 assert checked==credit['exact_verified_members']
 inv=S/'CLOSED_V2169_INVENTORY.json';assert sha(inv)==b['closed_V2169_inventory_sha256'];v=read(inv);allocated=exact_inventory(R/v['root'],{x['path']:x for x in v['rows']});assert allocated<=v['upper_bytes']==b['prior_V2169_closed_upper_bytes']==11*M
 assert b['all_prior_evidence_upper_bytes']==old['all_prior_evidence_upper_bytes']+11*M-9*M==credit['new_all_prior_evidence_upper_bytes']
 assert b['frozen_prior_baseline_bytes']==14873092096 and b['verified_duplicate_credit_bytes']==121692160 and b['additional_exact_closed_increment_credit_bytes']==19*M
 assert b['preparation_bytes']==4*M and b['archive_bytes']==12*M and b['task_bytes']==224*M and b['download_bytes']==32*M and b['metadata_bytes']==8*M and b['root_bytes']==512*M
 peak=b['all_prior_evidence_upper_bytes']+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes']);assert peak<=b['old_joint_peak_upper_bytes']==16095019008<b['limit_bytes']==16106127360
 assert b['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 own=int(subprocess.check_output(['du','-sx','-B1',str(S)],timeout=10).split()[0])
 for folder in [S/'recovery',S/'runtime_archives',O/'actual']:
  if folder.exists():own-=int(subprocess.check_output(['du','-sx','-B1',str(folder)],timeout=10).split()[0])
 assert own<=b['preparation_bytes'];room=b['limit_bytes']-b['all_prior_evidence_upper_bytes']-b['preparation_bytes']-b['metadata_bytes']-(272+512)*M;assert room>=17*M+64*1024+8192
 return dict(passed=True,joint_peak_bytes=b['old_joint_peak_upper_bytes'],computed_peak_bytes=peak,initial_task_root_room_bytes=room,preparation_allocated_bytes=own,additional_exact_closed_credit_bytes=9*M,old_19MiB_credit_retained_without_double_count=True,all_caps_and_original_baseline_unchanged=True,no_deletion_or_compression_credit=True)
def measure(output,limits):
 b=read(S/'BASELINE_DRAFT.json');output=Path(output).resolve();assert output==O/'actual'and os.sched_getaffinity(0)=={2}and limits['maximum_task_evidence_bytes']==224*M
 own=int(subprocess.check_output(['du','-sx','-B1',str(output)],timeout=10).split()[0]);upper=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['retained_future_closed_bytes']+b['metadata_bytes']+b['parallel_math_bytes']+own
 assert upper+(12+32+512)*M<=b['old_joint_peak_upper_bytes'];return own,upper
def transport_current_upper():return admission()['joint_peak_bytes']-(32+512)*M
