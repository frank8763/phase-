"""One original owner; redirect only runtime archive IO to bounded index adapter."""
from pathlib import Path
import ast,os,sys,json,time,hashlib,importlib.util
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;P=R/'experiments/v2148_psf_transport_scope_recovery'
sys.path.insert(0,str(P));import transport as old
assert Path(old.__file__).resolve()==P/'transport.py'
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def main():
 assert os.sched_getaffinity(0)=={5}and not(S/'ADAPTER_ONCE.json').exists()
 assert old.read(old.S/'SOURCE_CHAIN_CLOSED.json')['passed'];idx={x['path']:x for x in old.read(old.D/'ARCHIVE_INDEX.json')['files']}
 for p in P.iterdir():
  if p.is_file():assert idx[str(p.relative_to(R))]['sha256']==old.sha(p)
 files={str(p.relative_to(R)):old.sha(p)for p in C.iterdir()if p.is_file()};assert files
 for p in C.glob('*.py'):ast.parse(p.read_text())
 # Exact generated original48MiB runtime archive, new index writer10MiB.
 adapter=load('runtime_index_io_adapter',C/'transport.py');space=adapter.bound();assert space['C']==C and space['put']is adapter.put
 for rid in [None,'PSF']:compile(space['deliver'](rid,preview=True),'bounded-index-deliver','exec')
 old.put(S/'ADAPTER_ONCE.json',dict(unix=time.time(),pid=os.getpid(),models=0,NLP=0,physics=0,replay=0,late_helper_files=files,original_vehicle_source_unchanged=True,archive_plus_two_indices_bound_bytes=68*1024**2,original_archive_plus_metadata_bound_bytes=72*1024**2,source_commit='95006747a0f4d5bfafcd638be85bc33351357d9a',not_in_original_Git_or_sourceRelease=True,will_be_runtime_Release_members=True))
 module=load('once_finite_original_v2148_orchestrator',P/'run.py');process=module.process
 def io_redirect(label,argv,cap,owner=False):
  a=list(argv)
  if str(P/'transport.py')in a:a[a.index(str(P/'transport.py'))]=str(C/'transport.py')
  return process(label,a,cap,owner)
 module.process=io_redirect
 try:module.main()
 finally:
  assert all(old.sha(R/n)==h for n,h in files.items());old.put(S/'ADAPTER_CLOSED.json',dict(closed=True,late_helper_SHA_unchanged=True,models_executed_by_adapter=0,original_orchestrator_result_path=str((old.S/'DISPATCH_RESULT.json').relative_to(R)),finished_unix=time.time()))
if __name__=='__main__':main()
