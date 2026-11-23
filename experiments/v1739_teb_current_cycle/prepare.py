"""Bind a new exposed TEB cycle, existing loader proof and fixed vehicle data."""
import ast,fcntl,json,os,subprocess,time
from context import C,O,R,read,put,sha
def main():
 os.sched_setaffinity(0,{5});assert not(O/'INPUT_BINDING.json').exists()
 prior=R/'runs/v1737_teb_exact_native_aliases';b=read(prior/'POST_ROUND_STORAGE_BARRIER.json')
 assert b['passed']and all(sha(R/n)==h for n,h in b['proof_paths_SHA256'].items())
 assert read(prior/'SOURCE_OUTER_CLOSED.json')['passed']and read(prior/'build/SOURCE_NATIVE_RESULT.json')['all_loaded_dependency_identities_exact']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 d=read(R/'CURRENT_EXPERIMENT.json');assert d['active_round']is None and not d['models_now_authorized']
 files=read(prior/'SOURCE_FREEZE.json')['files'].copy()
 for n in ['POST_ROUND_STORAGE_BARRIER.json','SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','build/SOURCE_NATIVE_RESULT.json','EXACT_NATIVE_ALIASES.json','BINARY_BINDING.json']:
  p=prior/n;files[str(p.relative_to(R))]=sha(p)
 for n in ['PILOT_TASK.json','REFERENCE_CONFIG.json','LIMITS_DRAFT.json','TEB_CONFIG.json','EXACT_NATIVE_ALIASES.json','BINARY_BINDING.json','NATIVE_BINDING.json']:
  p=O/n;files[str(p.relative_to(R))]=sha(p)
 for p in C.iterdir():
  if p.is_file():
   if p.suffix=='.py':ast.parse(p.read_text())
   files[str(p.relative_to(R))]=sha(p)
 assert all(sha(R/n)==h for n,h in files.items())
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);peak=used+1014*1024**2;assert peak<15*1024**3
 put(O/'INPUT_BINDING.json',dict(files_SHA256=files,external_SHA256=read(prior/'SOURCE_FREEZE.json')['external_SHA256'],prior_loader_root=str(prior.relative_to(R)),models_authorized=False))
 put(O/'PREPARATION_CHECKPOINT.json',dict(prepared=True,source_only_not_run=True,models_authorized=False,source_members=len(files),allruns_bytes=used,full_peak_bytes=peak,unix=time.time()))
 print(json.dumps(dict(prepared=True,models=0,source_members=len(files))))
if __name__=='__main__':main()
