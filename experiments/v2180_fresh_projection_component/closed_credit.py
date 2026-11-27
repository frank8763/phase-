"""Tighten only the closed PRIEST24MiB band from complete exact inventories."""
from context import R,C,SOURCE as S,read,put,sha
from pathlib import Path
import os,subprocess,math,hashlib,fcntl,json
assert os.sched_getaffinity(0)=={5}and not(S/'ADDITIONAL_CLOSED_PRIEST_CREDIT.json').exists()
M=1024**2;handles=[]
for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
 f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);handles.append(f)
assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
p=R/'runs/v2122_priest_quiescent_handoff';assert read(p/'COMPLETION.json')['closed']and read(p/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']and read(p/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
for name in ['LAUNCH_IDENTITY.json','vehicle/OWNED_CHILD.json']:
 f=p/name
 if f.exists():
  i=read(f);q=Path('/proc',str(i['pid']),'stat');assert not q.exists()or q.read_text().split(') ',1)[1].split()[19]!=str(i['start_ticks'])
full=p/'runtime_recovery/FULL_REMOTE_VERIFIED.json'
if not full.exists():
 candidates=list(p.rglob('FULL_REMOTE_VERIFIED.json'));full=next(z for z in candidates if sha(z)==read(p/'POST_COMPONENT_STORAGE_BARRIER.json')['runtime_proof_sha256'])
assert sha(full)==read(p/'POST_COMPONENT_STORAGE_BARRIER.json')['runtime_proof_sha256']and read(full)['passed']
rows=[];roots=['runs/v2119_parallel_components_release_scope','runs/v2120_priest_preview_adapter','runs/v2121_priest_geometric_vehicle','runs/v2122_priest_quiescent_handoff'];allocated=0
for name in roots:
 root=R/name;allocated+=int(subprocess.check_output(['du','-sx','-B1',str(root)]).split()[0])
 for f in sorted(root.rglob('*')):
  if not(f.is_symlink()or f.is_file()):continue
  st=f.lstat();target=os.readlink(f)if f.is_symlink()else None
  rows.append(dict(path=str(f.relative_to(R)),bytes=st.st_size,allocated=st.st_blocks*512,mtime_ns=st.st_mtime_ns,device=st.st_dev,inode=st.st_ino,link=target,sha256=hashlib.sha256(os.fsencode(target)).hexdigest()if target is not None else sha(f)))
for row in rows:
 f=R/row['path'];st=f.lstat();assert(st.st_size,st.st_blocks*512,st.st_mtime_ns,st.st_dev,st.st_ino)==tuple(row[k]for k in ['bytes','allocated','mtime_ns','device','inode']);assert(hashlib.sha256(os.fsencode(os.readlink(f))).hexdigest()if row['link']is not None else sha(f))==row['sha256']
assert {z['path']for z in rows}=={str(f.relative_to(R))for name in roots for f in (R/name).rglob('*')if f.is_file()or f.is_symlink()}
upper=math.ceil(allocated/M)*M;old=read(S/'BASELINE_DRAFT.json');assert old['prior_PRIEST_closed_evidence_upper_bytes']==24*M;credit=24*M-upper;assert credit>=9*M
# Preserve first rejected draft; no model/Source admission was consumed.
put(S/'BASELINE_ATTEMPT01_INITIALIZER_HEADROOM_REFUSAL.json',dict(passed=False,first_baseline=old,reason='Original fixed initializer16MiB+terminal1MiB+error reserve did not fit original272MiBIO/512root conservative bands',new_NLP_models_Source=0))
put(S/'CLOSED_PRIEST_INVENTORY.json',dict(passed=True,roots=roots,rows=rows,allocated_bytes=allocated,upper_bytes=upper,extra_prior_metadata_roots_included_conservatively=True))
proof=dict(passed=True,closed=True,original_PRIEST_band=24*M,new_PRIEST_band=upper,additional_credit_bytes=credit,inventory_sha256=sha(S/'CLOSED_PRIEST_INVENTORY.json'),all_original_closed_prior_runtime_proof_sha256=sha(full),no_new_HTTP_audit_replay_deletion=True,old_baseline_and_all_other_bands_unchanged=True,original_frozen_baseline=14873092096)
put(S/'ADDITIONAL_CLOSED_PRIEST_CREDIT.json',proof)
b=dict(old);b.update(prior_PRIEST_closed_evidence_upper_bytes=upper,additional_exact_closed_PRIEST_credit_bytes=credit,additional_exact_closed_PRIEST_credit_sha256=sha(S/'ADDITIONAL_CLOSED_PRIEST_CREDIT.json'),all_prior_evidence_upper_bytes=old['all_prior_evidence_upper_bytes']-credit,closed_PRIEST_inventory_sha256=sha(S/'CLOSED_PRIEST_INVENTORY.json'));b['held_peak_bytes']-=credit;put(S/'BASELINE_DRAFT.json',b);print(json.dumps(proof))
