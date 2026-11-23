"""Bind unchanged runtime batch and all closed successful/failed material inputs."""
import ast,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert not(C/'CONFIG.json').exists();read=lambda p:json.loads(p.read_text());old=R/'runs/v1712_root_member_materials';plan=read(old/'BATCHES_LOCKED.json')
 for row in plan['batches']:
  p=old/'rounds'/row['id']/'POST_ROUND_STORAGE_BARRIER.json';v=read(p);assert v['passed']and all(sha(R/k)==h for k,h in v['proof_paths_SHA256'].items());plan['source_inputs_SHA256'][str(p.relative_to(R))]=sha(p)
 assert read(O/'SOFTWARE_REVIEW.json')['passed'];row=plan['batches'][-1];row['predecessor']=None;plan['batches']=[row];plan['total_packages']=len(row['packages']);plan['download_bytes']=row['download_bytes'];plan['declared_installed_bytes']=row['declared_installed_bytes']
 (O/'BATCHES_LOCKED.json').write_text(json.dumps(plan,indent=2)+'\n');(C/'CONFIG.json').write_text(json.dumps(dict(plan_sha256=sha(O/'BATCHES_LOCKED.json'),batch_ids=[row['id']],task_cap_bytes=224*1024**2,metadata_root_cap_bytes=8*1024**2),indent=2)+'\n')
 files=[p for folder in [C,R/'experiments/v1717_catalog_material_recovery']for p in folder.iterdir()if p.is_file()]
 for p in files:
  if p.suffix=='.py':ast.parse(p.read_text())
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);peak=used+(224+8+32+32+512)*1024**2;assert peak<15*1024**3
 (O/'PRELAUNCH_CHECKPOINT.json').write_text(json.dumps(dict(source_files_SHA256={str(p.relative_to(R)):sha(p)for p in files},software_review_sha256=sha(O/'SOFTWARE_REVIEW.json'),packages=85,reuse_exact_old_raws=83,new_downloads_max=2,allruns_bytes=used,peak_bytes=peak,models=0,unix=time.time()),indent=2)+'\n');print(json.dumps(dict(packages=85,models=0,peak_bytes=peak)))
if __name__=='__main__':main()
