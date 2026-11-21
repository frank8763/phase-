"""Exactly two immutable-commit source downloads, no second push."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def put(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
 rows=[]
 try:
  sync=json.loads((R/'runs/v1494_priest_worker_source_recovery/SYNC_RESULT.json').read_text());assert sync['remote_verified'];head=sync['head']
  frozen=json.loads((R/'runs/v1493_priest_numeric_once/NUMERIC_SOURCE_FREEZE.json').read_text())['files']
  for name in ['experiments/v1487_priest_optimizer_contract/PROTOCOL.md','experiments/v1487_priest_optimizer_contract/kernel_loader.py']:
   p=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/frank8763/phase-/contents/'+name+'?ref='+head],cwd=R,capture_output=True,timeout=15)
   assert p.returncode==0 and len(p.stdout)<=128*1024,'SUPPLEMENTARY_GIT_SOURCE_READ_REFUSED'
   value=json.loads(p.stdout);assert value['type']=='file'and value['path']==name and value['encoding']=='base64'
   raw=base64.b64decode(value['content']);digest=hashlib.sha256(raw).hexdigest();gitsha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
   assert len(raw)==value['size']and gitsha==value['sha']and digest==frozen[name]and raw==(R/name).read_bytes()
   target=O/Path(name).name;target.write_bytes(raw)
   rows.append(dict(path=name,bytes=len(raw),sha256=digest,git_blob_sha1=gitsha,commit=head,actual_remote_source_downloaded=True,local_copy=str(target.relative_to(R))))
  put(O/'FULL_REMOTE_SOURCE_VERIFIED.json',dict(passed=True,closed=True,source_commit=head,files=rows,requests=2,models=0,archive_resealed=False,second_push_executed=False,not_in_V1494_archive=True,verified_unix=time.time()))
 except BaseException as e:put(O/'ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),completed=rows,models=0));raise
if __name__=='__main__':main()
