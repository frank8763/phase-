"""Only regenerable caches, duplicate archives, and byte-identical model replicas."""
import json,hashlib,fcntl,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'records/navigation_review_20261112';O=R/'runs/navigation_review_20261112'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def confined(s):
 p=R/s;assert p.resolve().is_relative_to(R)and not p.is_symlink();assert all(not q.is_symlink()for q in p.parents if q!=R and q.is_relative_to(R));return p
def main():
 assert not(D/'CLEANUP_RESULT.json').exists();assert(R/'REVIEW_PENDING').exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert json.loads((R/'runs/v1082_guarded_saved_continuation/COMPLETION.json').read_text())['closed'];tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'));freeze=json.loads((R/'experiments/v1082_guarded_saved_continuation/SOURCE_FREEZE.json').read_text())['files'];actions=[];cachebytes=0;archivebytes=0;modelbytes=0
 for x in json.loads((O/'CACHE_CANDIDATES.json').read_text()):
  s=x['path'];p=confined(s);assert s not in tracked and s not in freeze and p.suffix in ['.pyc','.pyo']and'__pycache__'in p.parts
  if not p.exists():continue
  h=sha(p);size=p.stat().st_size;p.unlink();cachebytes+=size;actions.append(dict(path=s,action='removed_regenerable_untracked_bytecode',bytes=size,sha256=h))
 for x in json.loads((D/'DUPLICATE_ARCHIVE_PLAN.json').read_text()):
  keep=confined(x['keep']);assert sha(keep)==x['sha256']
  for s in x['remove']:
   p=confined(s);assert s not in tracked and s not in freeze and sha(p)==x['sha256']and p.stat().st_size==keep.stat().st_size
   size=p.stat().st_size;p.unlink();archivebytes+=size;actions.append(dict(path=s,action='removed_identical_archive_replica',bytes=size,sha256=x['sha256'],retained_identical_copy=x['keep']))
 cache=R/'runs/model_cache';cache.mkdir(exist_ok=True);model_actions=[]
 for x in json.loads((D/'MODEL_DEDUP_PLAN.json').read_text()):
  paths=[confined(s)for s in x['paths']];assert all(sha(p)==x['sha256']for p in paths);canonical=cache/(x['sha256']+'.mjb')
  if canonical.exists():assert not canonical.is_symlink()and sha(canonical)==x['sha256']
  else:os.link(paths[0],canonical)
  for p in paths:
   old=p.stat();already=old.st_ino==canonical.stat().st_ino and old.st_dev==canonical.stat().st_dev
   if not already:
    tmp=p.with_name(p.name+'.dedup-tmp');assert not tmp.exists();os.link(canonical,tmp);os.replace(tmp,p);modelbytes+=old.st_size
   assert sha(p)==x['sha256']and p.stat().st_ino==canonical.stat().st_ino
   model_actions.append(dict(path=str(p.relative_to(R)),action='immutable_content_identical_hardlink',bytes_unchanged=True,sha256=x['sha256'],canonical=str(canonical.relative_to(R)),already_shared=already))
 assert all(sha(R/p)==h for p,h in freeze.items()),'FROZEN_EVIDENCE_OR_SOURCE_CHANGED'
 result=dict(completed=True,models_or_integrations=0,cache_bytes_removed=cachebytes,duplicate_archive_bytes_removed=archivebytes,model_replica_logical_bytes_coalesced=modelbytes,total_redundant_logical_bytes_removed_or_coalesced=cachebytes+archivebytes+modelbytes,unique_evidence_deleted=False,frozen_sources_and_inputs_all_sha_unchanged=True,guard_preserved=True,stage_accessed=False,cache_and_archive_actions=actions,model_paths_preserved=model_actions)
 (D/'CLEANUP_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if not isinstance(v,list)},indent=2))
if __name__=='__main__':main()
