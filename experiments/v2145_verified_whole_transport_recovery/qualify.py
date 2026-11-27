"""One new IO-only helper qualification; never requalifies old algorithms."""
from pathlib import Path
import ast,hashlib,json,os,subprocess,time,traceback
from evidence import R,C,ROOT as S,P,read,put,sha,deliver
def statrow(p):
 s=p.stat();return dict(path=str(p.relative_to(R)),bytes=s.st_size,allocated=s.st_blocks*512,sha256=sha(p),device=s.st_dev,inode=s.st_ino,mtime_ns=s.st_mtime_ns,nlink=s.st_nlink)
def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0));out=dict(passed=False,closed=False,models=0,physics=0,replay=0,optimizer_calls=0,old_source_qualifications=0)
 try:
  old=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in old.items())and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'components/SCCR/POST_COMPONENT_STORAGE_BARRIER.json')['passed']
  tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=R).decode().split('\0'));protected={(p.stat().st_dev,p.stat().st_ino)for n in old if(p:=R/n).is_file()}
  plan=read(S/'PLAN.json');files=dict(old)
  for g in plan['groups']:
   row=g['whole_duplicate'];p=R/row['path'];assert p.is_file()and not p.is_symlink()and row==statrow(p)and row['nlink']==1 and row['path']not in tracked and(p.stat().st_dev,p.stat().st_ino)not in protected
   idx=R/g['index_path'];assert sha(idx)==g['index_sha256'];x=read(idx);assert row['sha256']==x['archive_sha256']and row['bytes']==x['archive_bytes'];h=hashlib.sha256();total=0
   for z in g['parts']:
    p=R/z['path'];assert p.stat().st_size==z['bytes']and sha(p)==z['sha256']
    with p.open('rb')as f:
     for b in iter(lambda:f.read(1024**2),b''):h.update(b);total+=len(b)
   assert h.hexdigest()==row['sha256']and total==row['bytes'];files[g['index_path']]=sha(idx)
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    files[str(p.relative_to(R))]=sha(p)
  for p in [S/'PLAN.json',S/'AUTHORIZATION.json']:files[str(p.relative_to(R))]=sha(p)
  for rid in [None]+[g['id']for g in plan['groups']]:compile(deliver(rid,preview=True),'existing_group_transport','exec')
  from reservation import admission
  io=admission();put(S/'IO_ADMISSION.json',io);files[str((S/'IO_ADMISSION.json').relative_to(R))]=sha(S/'IO_ADMISSION.json')
  put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if old.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  out.update(passed=True,source_members=len(files),delta_members=len(files)-len(old),groups=4,only_nlink1_whole_duplicates=True,original_parts_and_raw_retained=True,all_transport_scopes_compiled=True,local_whole_parts_SHA_equal=True)
 except BaseException as e:out.update(error=repr(e),traceback=traceback.format_exc())
 out['closed']=True;put(S/'SOURCE_QUALIFICATION.json',out);put(S/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=out['passed'],models=0));print(json.dumps(out));return 0 if out['passed']else 1
if __name__=='__main__':raise SystemExit(main())
