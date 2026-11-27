"""Additional unused CLOSED upper credits from already-pinned exact inventories.

Use CURRENT band uppers, never the old pre-credit values. No files are deleted
and the immutable historical baseline and all existing credits remain intact.
"""
from pathlib import Path
import os,json,hashlib,subprocess,math
R=Path(__file__).resolve().parents[2];S=R/'runs'/Path(__file__).resolve().parent.name;M=1024**2
assert os.sched_getaffinity(0)=={5}and not(S/'ADDITIONAL_CLOSED_UPPER_CREDIT.json').exists()
read=lambda p:json.loads(p.read_bytes())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for x in iter(lambda:f.read(M),b''):h.update(x)
 return h.hexdigest()
parent=R/'runs/v2169_sccr_owner_proof_binding_recovery';b=read(parent/'BASELINE_DRAFT.json');assert b['frozen_prior_baseline_bytes']==14873092096 and b['additional_exact_closed_increment_credit_bytes']==19*M
I=R/'runs/v2162_pcbf_conditioned_current100/CLOSED_INCREMENT_INVENTORY.json';J=R/'runs/v2165_sccr_dual_actor_component/CLOSED_PARENT_INVENTORY.json'
assert sha(I)==b['closed_increment_inventory_sha256']and sha(J)==b['new_closed_scope_inventory_sha256']
i=read(I);j=read(J);groups=[]
for g in i['groups']:
 assert b[g['key']]==g['new_upper'];groups.append(dict(key=g['key'],roots=['runs/'+x for x in g['roots']],current_upper=b[g['key']],inventory_path=str(I.relative_to(R)),inventory_sha256=sha(I)))
groups.append(dict(key='new_closed_band_upper_bytes',roots=i['closed_band_roots'],current_upper=b['new_closed_band_upper_bytes'],inventory_path=str(I.relative_to(R)),inventory_sha256=sha(I)))
groups.append(dict(key='additional_closed_scope_upper_bytes',roots=j['roots'],current_upper=b['additional_closed_scope_upper_bytes'],inventory_path=str(J.relative_to(R)),inventory_sha256=sha(J)))
tables={str(I.relative_to(R)):{z['path']:z for z in i['rows']},str(J.relative_to(R)):{z['path']:z for z in j['rows']}}
verified=set();total_credit=0
for group in groups:
 table=tables[group['inventory_path']];found=set();allocated=0
 for name in group['roots']:
  root=R/name;assert root!=R/'runs/v2152_weekend_research_program'
  allocated+=int(subprocess.check_output(['du','-sx','-B1',str(root)],timeout=10).split()[0])
  found.update(str(p.relative_to(R))for p in root.rglob('*')if p.is_file()and not p.is_symlink())
 expected={n for n in table if any(n.startswith(root+'/')for root in group['roots'])};assert found==expected,'CLOSED_CREDIT_PATH_SET_CHANGED'
 for n in sorted(found):
  if n in verified:continue
  row=table[n];p=R/n;st=p.stat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==(row['bytes'],row['allocated'],row['mtime_ns'],row['device'],row['inode'])and sha(p)==row['sha256'],'CLOSED_CREDIT_BYTES_OR_IDENTITY_CHANGED:'+n
  verified.add(n)
 new_upper=((allocated+M-1)//M)*M;assert new_upper<=group['current_upper']
 group.update(actual_allocated_with_directories=allocated,new_upper=new_upper,additional_credit_bytes=group['current_upper']-new_upper,member_count=len(found),all_exact_SHA_size_blocks_mtime_device_inode_verified=True,path_set_sha256=hashlib.sha256('\n'.join(sorted(found)).encode()).hexdigest());total_credit+=group['additional_credit_bytes']
assert total_credit>=6397952
# The newest failed component is a NEW retained increment, independently pinned.
assert read(parent/'components/SCCR/POST_COMPONENT_STORAGE_BARRIER.json')['passed'];rows=[]
for p in sorted(parent.rglob('*')):
 if p.is_file()and not p.is_symlink():
  st=p.stat();rows.append(dict(path=str(p.relative_to(R)),bytes=st.st_size,allocated=st.st_blocks*512,mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino,sha256=sha(p)))
allocated=int(subprocess.check_output(['du','-sx','-B1',str(parent)],timeout=10).split()[0]);upper=((allocated+M-1)//M)*M
inventory=S/'CLOSED_V2169_INVENTORY.json';assert not inventory.exists();inventory.write_text(json.dumps(dict(root=str(parent.relative_to(R)),rows=rows,allocated_bytes=allocated,upper_bytes=upper,passed=True,closed=True),indent=2)+'\n')
newprior=b['all_prior_evidence_upper_bytes']+upper-total_credit
room=b['limit_bytes']-newprior-b['preparation_bytes']-b['metadata_bytes']-(272+512)*M
peak=newprior+sum(b[k]for k in ['preparation_bytes','retained_future_closed_bytes','task_bytes','archive_bytes','download_bytes','metadata_bytes','root_bytes','parallel_math_bytes'])
assert room>=17*M+64*1024+8192 and peak<=b['old_joint_peak_upper_bytes']<b['limit_bytes']
v=dict(passed=True,closed=True,groups=groups,old_already_applied_credit_bytes=19*M,new_additional_credit_bytes=total_credit,newest_closed_increment_upper_bytes=upper,newest_closed_increment_inventory_sha256=sha(inventory),new_all_prior_evidence_upper_bytes=newprior,proposed_initial_task_root_room_bytes=room,proposed_peak_bytes=peak,parent_baseline_path=str((parent/'BASELINE_DRAFT.json').relative_to(R)),parent_baseline_sha256=sha(parent/'BASELINE_DRAFT.json'),exact_verified_members=len(verified),original_frozen_baseline_unchanged=True,all_existing_verified_credits_retained=True,no_deletion=True,no_cap_expansion=True,no_baseline_reset=True,not_actual_model_admission=True,models=0,physics=0)
(S/'ADDITIONAL_CLOSED_UPPER_CREDIT.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:x for k,x in v.items()if k!='groups'}))
