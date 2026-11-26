"""One metadata-only recovery, immutable first formal source/actual/archive."""
import ast,fcntl,hashlib,importlib.util,inspect,json,os,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;W=R/'runs'/C.name;S=R/'runs/v2105_svg03_exact_transport_parent';RID='common_03__SVGMPPI';O=R/'runs/v2095_svg_common_full_route/rounds'/RID;T=S/'runtime_archives'/RID;NET=R/'experiments/v2062_bounded_dual_route_transport/net.py'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def gone(i):
 p=Path('/proc',str(i['pid']),'stat');return not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
def recover():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert read(O/'COMPLETION.json')['closed']and gone(read(O/'OWNED_CHILD.json'))and gone(read(S/'LAUNCH_IDENTITY.json'))
 assert read(R/'runs/v2062_bounded_dual_route_transport/SOFTWARE_RESULT.json')['passed']and sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 locks=[]
 for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/name).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert not(T/'FULL_REMOTE_VERIFIED.json').exists()and read(T/'remote_delivery/RESULT.json')['closed']and not read(T/'remote_delivery/RESULT.json')['passed']
 receipts=[read(p)for p in (T/'remote_delivery/http_receipts').glob('*.json')];assert len(receipts)==6 and all(x['call']==1 and x['method']=='GET'and not x['passed']for x in receipts),'ORIGINAL_EPISODE_MUST_BE_PREMUTATION_METADATA_FAILURE'
 helper=load('SVG_frozen_actual_archive_helper',R/'experiments/v2105_svg03_exact_transport_parent/evidence.py');assert all(sha(R/n)==h for n,h in helper.read(S/'SOURCE_FREEZE.json')['files'].items())
 index=read(T/'ARCHIVE_INDEX.json');assert len(index['files'])==5795 and index['archive_bytes']==51193922
 for row in index['parts']:
  p=T/'archive'/row['name'];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
 put(W/'CLAIM.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),unix=time.time(),maximum_IO_s=600,index_sha256=sha(T/'ARCHIVE_INDEX.json'),no_push_ref_reseal_or_models=True))
 function=inspect.getsource(helper.deliver);needle='text=target.read_text()';assert function.count(needle)==1
 old="assert not alias.exists();alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())";new="assert not alias.exists()or sha(alias)==sha(D/'ARCHIVE_INDEX.json');\n        if not alias.exists():alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())"
 folder='remote_delivery_recovery_2107';assert not(T/folder).exists()
 inject=';text=text.replace('+repr("O=D/'remote_delivery';")+','+repr("O=D/"+repr(folder)+";")+');text=text.replace('+repr('experiments/v1940_content_addressed_runtime_recovery/net.py')+','+repr(str(NET.relative_to(R)))+');text=text.replace('+repr(old)+','+repr(new)+')'
 function=function.replace(needle,needle+inject);ast.parse(function)
 put(W/'PATCH_PROOF.json',dict(original_helper_sha256=sha(Path(helper.__file__)),new_helper_sha256=sha(Path(__file__)),qualified_net_sha256=sha(NET),qualified_software_proof_sha256=sha(R/'runs/v2062_bounded_dual_route_transport/SOFTWARE_RESULT.json'),archive_index_sha256=sha(T/'ARCHIVE_INDEX.json'),patched_function_AST_sha256=hashlib.sha256(ast.dump(ast.parse(function)).encode()).hexdigest(),transport_only_no_numerical_change=True,late_helper_not_in_original_source_or_runtime_archive=True))
 result=dict(closed=False,passed=False,models=0,physical_native=0,replay=0,new_audit=False)
 try:
  scope=dict(helper.__dict__);exec(compile(function,str(helper.__file__),'exec'),scope);before=sys.path[:];sys.path.insert(0,str(Path(helper.__file__).parent))
  try:code=scope['deliver'](RID)
  finally:sys.path[:]=before
  result.update(passed=code==0,returncode=code)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result.update(closed=True,transport_worker=folder);put(W/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(recover())
