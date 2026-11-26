"""Original archive only, bounded qualified process-local transport substitution."""
from pathlib import Path
import ast,fcntl,hashlib,importlib.util,inspect,json,os,sys,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs/v2045_remaining_parallel_source';D=R/'runs'/C.name
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def recover(rid,episode):
 os.sched_setaffinity(0,{5});assert rid in [f'common_{i:02d}__MPPI'for i in range(9,13)]and episode in [1,2];assert read(D/'SOFTWARE_RESULT.json')['passed'];O=S/'rounds'/rid;T=S/'runtime_archives'/rid;assert read(O/'COMPLETION.json')['closed']and not(T/'FULL_REMOTE_VERIFIED.json').exists()
 i=read(O/'OWNED_CHILD.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 locks=[]
 for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/name).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 helper=load('frozen_original_archive_binding',R/'experiments/v2045_remaining_parallel_source/evidence.py');assert all(helper.sha(R/n)==h for n,h in helper.read(S/'SOURCE_FREEZE.json')['files'].items())
 index=read(T/'ARCHIVE_INDEX.json')
 for row in index['parts']:
  p=T/'archive'/row['name'];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
 W=D/(rid+'_episode'+str(episode));W.mkdir();put(W/'CLAIM.json',dict(pid=os.getpid(),unix=time.time(),maximum_IO_s=600,models=0,index_sha256=sha(T/'ARCHIVE_INDEX.json'),net_sha256=sha(C/'net.py'),no_push_ref_reseal=True))
 target='remote_delivery_dualroute_2062_'+str(episode);assert not(T/target).exists();function=inspect.getsource(helper.deliver);needle='text=target.read_text()';assert function.count(needle)==1
 old="assert not alias.exists();alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())";new="assert not alias.exists()or sha(alias)==sha(D/'ARCHIVE_INDEX.json');\n        if not alias.exists():alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())"
 inject=';text=text.replace('+repr("O=D/'remote_delivery';")+','+repr("O=D/"+repr(target)+";")+');text=text.replace('+repr('experiments/v1940_content_addressed_runtime_recovery/net.py')+','+repr(str((C/'net.py').relative_to(R)))+');text=text.replace('+repr(old)+','+repr(new)+')'
 function=function.replace(needle,needle+inject);ast.parse(function);put(W/'PATCH_PROOF.json',dict(original_helper_sha256=sha(Path(helper.__file__)),net_sha256=sha(C/'net.py'),software_proof_sha256=sha(D/'SOFTWARE_RESULT.json'),archive_index_sha256=sha(T/'ARCHIVE_INDEX.json'),transport_only_no_numerical_change=True,patched_function_AST_sha256=hashlib.sha256(ast.dump(ast.parse(function)).encode()).hexdigest()))
 space=dict(helper.__dict__);exec(compile(function,str(helper.__file__),'exec'),space);code=space['deliver'](rid);put(W/'RESULT.json',dict(closed=True,passed=code==0,models=0,physics=0,replay=0,transport_worker=target));return code
def barrier(rid):
 O=S/'rounds'/rid;T=S/'runtime_archives'/rid;x=read(O/'RUNTIME_CLOSED_REVIEW.json');assert read(T/'FULL_REMOTE_VERIFIED.json')['passed']and read(T/'TRANSPORT_CLEANUP.json')['passed'];assert not(O/'POST_ROUND_STORAGE_BARRIER.json').exists()
 paths=[O/n for n in ['COMPLETION.json','RUNTIME_CLOSED_REVIEW.json','FORMAL_REGISTERED.json','FORMAL_CLOSED_EVENT.json']]+[T/n for n in ['ARCHIVE_INDEX.json','FULL_REMOTE_VERIFIED.json','TRANSPORT_CLEANUP.json']]+[C/'net.py',D/'SOFTWARE_RESULT.json']
 for W in T.glob('remote_delivery_dualroute_2062_*'):
  assert read(W/'RESULT.json')['closed'];i=read(W/'CLAIM.json');assert not Path('/proc',str(i['pid'])).exists();paths.append(W/'RESULT.json')
 put(O/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,whole_navigation_passed=x['whole_navigation_passed'],valid_finite_method_refusal=x['valid_finite_method_refusal'],technical_censor=x['technical_censor'],proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},all_physical_raw_retained=True,original_transport_failures_retained=True,new_bounded_dual_route_client=True,no_push_ref_reseal_or_numerical_calls=True,models_authorized=False))
if __name__=='__main__':
 if sys.argv[1]=='barrier':barrier(sys.argv[2])
 else:raise SystemExit(recover(sys.argv[1],int(sys.argv[2])))
