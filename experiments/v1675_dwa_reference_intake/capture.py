"""Pin a separate public DWA reference, zero source import/numerical calls."""
import base64,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
GH=R/'tools/phase_storage_20261107/vendor/gh';REPO='AtsushiSakai/PythonRobotics'
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def request(path):
 p=subprocess.run([str(GH),'api','repos/'+REPO+'/'+path],capture_output=True,timeout=20)
 assert p.returncode==0,'BOUNDED_GITHUB_REF_BLOB_READ';return json.loads(p.stdout)
def main():
 os.sched_setaffinity(0,{5});start=time.monotonic()
 with(O/'CAPTURE_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0,source_import=False,max_source_bytes=128*1024),f)
 result=dict(closed=False,passed=False,models=0,numerical_calls=0,physical_native=0,source_imported=False)
 try:
  repo=request('');branch=repo['default_branch'];assert branch in {'master','main'}
  commit=request('commits/'+branch);pin=commit['sha'];tree=commit['commit']['tree']['sha'];put(O/'COMMIT.json',commit)
  rows=[];total=0
  for name in ['PathPlanning/DynamicWindowApproach/dynamic_window_approach.py','LICENSE']:
   entry=request('contents/'+name+'?ref='+pin);assert entry['type']=='file'and entry['encoding']=='base64'and entry['size']<=128*1024
   raw=base64.b64decode(entry['content']);assert len(raw)==entry['size']and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==entry['sha']
   total+=len(raw);assert total<=128*1024
   target=O/'upstream'/name;target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb')as f:f.write(raw)
   rows.append(dict(repository=REPO,commit=pin,tree=tree,path=name,git_blob_sha1=entry['sha'],bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),saved_path=str(target.relative_to(R))))
  result.update(passed=True,default_branch=branch,commit=pin,tree=tree,rows=rows,source_bytes=total,original_G4C_source_restored=False,distinct_reference_identity=True)
 except BaseException as error:result['first_error']=repr(error)
 result.update(closed=True,wall_s=time.monotonic()-start);put(O/'CAPTURE_RESULT.json',result);print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
