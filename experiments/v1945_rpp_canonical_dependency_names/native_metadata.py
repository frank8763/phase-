"""Actual oneDLL load and six null/POD Ccalls, no RPP instance or solver."""
from pathlib import Path
import ctypes,hashlib,json,sys,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sys.path.insert(0,str(C));from binding import bind
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def maps():
 out={}
 for line in Path('/proc/self/maps').read_text().splitlines():
  cols=line.split(None,5)
  if len(cols)==6 and cols[5].startswith('/'):
   p=Path(cols[5]);
   if p.is_file()and not str(p).endswith(' (deleted)'):out[str(p)]=dict(sha256=sha(p),device=p.stat().st_dev,inode=p.stat().st_ino)
 return out

def main():
 start=time.monotonic();inputs=json.loads((O/'INPUT_BINDING.json').read_text());source=inputs['files'];before=maps();lib=bind(source,source_only=True);assert lib.phase_rpp_abi_version()==1;assert lib.phase_rpp_request_dimension()==5
 assert lib.phase_rpp_solve(None,0,None,None,0,None,0,0,0.,0.,0.,None,0,None)==-1
 assert lib.phase_rpp_call_count(None)==0 and lib.phase_rpp_poisoned(None)==1
 error=ctypes.create_string_buffer(256);assert lib.phase_rpp_error(error,256)==0 and error.value==b''
 after=maps();new={n:r for n,r in after.items()if n not in before};allowed=inputs['namespace_ELF_files_SHA256']
 for name,row in new.items():assert name in allowed and row['sha256']==allowed[name],'UNPINNED_RPP_NATIVE_DEPENDENCY:'+name
 result=dict(passed=True,closed=True,explicit_DLL_loads=1,metadata_and_null_FFI_calls=6,controller_constructors=0,costmap_constructors=0,solver_calls=0,models=0,physics=0,replay=0,new_loaded_objects=new,all_new_ELF_dependencies_exact=True,upstream_static_registration_counts_unknown=True,source_only=True,wall_s=time.monotonic()-start)
 (O/'NATIVE_METADATA_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
