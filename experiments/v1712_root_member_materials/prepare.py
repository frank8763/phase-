"""Bind the unchanged material plan and already closed failed predecessor."""
import ast,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert not(C/'CONFIG.json').exists()and not(O/'BATCHES_LOCKED.json').exists()
 read=lambda p:json.loads(p.read_text());old=R/'runs/v1710_native_build_materials';prior=old/'rounds/01_boost_headers_01';b=read(prior/'POST_ROUND_STORAGE_BARRIER.json');assert b['passed']and all(sha(R/n)==h for n,h in b['proof_paths_SHA256'].items())
 assert read(O/'SOFTWARE_REVIEW.json')['passed'];plan=read(old/'BATCHES_LOCKED.json')
 for p in [old/'BATCHES_LOCKED.json',prior/'RESULT.json',prior/'RAW_PACKAGE_FAILURE_SUPPLEMENT.json',prior/'POST_ROUND_STORAGE_BARRIER.json']:
  plan['source_inputs_SHA256'][str(p.relative_to(R))]=sha(p)
 (O/'BATCHES_LOCKED.json').write_text(json.dumps(plan,indent=2,allow_nan=False)+'\n')
 (C/'CONFIG.json').write_text(json.dumps(dict(plan_sha256=sha(O/'BATCHES_LOCKED.json'),batch_ids=[x['id']for x in plan['batches']],task_cap_bytes=224*1024**2,metadata_root_cap_bytes=8*1024**2),indent=2)+'\n')
 files=[p for folder in [C,R/'experiments/v1713_root_member_recovery']for p in folder.iterdir()if p.is_file()]
 for p in files:
  if p.suffix=='.py':ast.parse(p.read_text())
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);peak=used+(4*224+8+32+32+512)*1024**2;assert peak<15*1024**3
 (O/'PRELAUNCH_CHECKPOINT.json').write_text(json.dumps(dict(AST_valid=True,source_files_SHA256={str(p.relative_to(R)):sha(p)for p in files},plan_sha256=sha(O/'BATCHES_LOCKED.json'),software_review_sha256=sha(O/'SOFTWARE_REVIEW.json'),fixed_batches=[x['id']for x in plan['batches']],packages=plan['total_packages'],allruns_bytes=used,conservative_allfour_task_peak_bytes=peak,models=0,compiler_authority=False,unix=time.time()),indent=2)+'\n')
 cur=read(R/'CURRENT_EXPERIMENT.json');cur.update(status='PREPARING_ROOT_DIRECTORY_REPAIRED_MATERIALS_NO_MODELS',next_experiment=C.name,next_preparation=C.name);cur['next_comparison_step']['required']='Complete the unchanged fixed native material plan through exact root-directory parser repair, then separate originalauthor CPU4 compilation.';(R/'CURRENT_EXPERIMENT.json').write_text(json.dumps(cur,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
 print(json.dumps(dict(packages=plan['total_packages'],allruns_bytes=used,peak_bytes=peak,models=0)))
if __name__=='__main__':main()
