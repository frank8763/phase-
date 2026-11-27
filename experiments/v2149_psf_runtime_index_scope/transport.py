"""Runtime-index-only adapter; no scientific imports or modifications."""
from pathlib import Path
import sys,os,json,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
P=R/'experiments/v2148_psf_transport_scope_recovery';sys.path.insert(0,str(P));import transport as old
assert Path(old.__file__).resolve()==P/'transport.py'
# Use an explicit name on import from run.py, avoiding the same-name alias.
def put(path,value):
 path=Path(path)
 if path.name!='ARCHIVE_INDEX.json':return old.put(path,value)
 raw=json.dumps(value,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<=10*1024**2,'RUNTIME_INDEX_10MIB_BOUND'
 temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_bytes(raw);temporary.replace(path)
def bound():
 b=old.bound();b['put']=put;b['C']=C
 # Both archive/source logic are unchanged, but only RUNTIME is callable here.
 return b
if __name__=='__main__':
 os.sched_setaffinity(0,{5});stage=sys.argv[1];assert len(sys.argv)==3 and sys.argv[2]=='PSF'
 if stage=='archive':bound()['archive']('PSF')
 elif stage=='ref':old.ref('PSF')
 elif stage=='deliver':raise SystemExit(bound()['deliver']('PSF'))
 else:raise AssertionError(stage)
