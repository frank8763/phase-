"""One already sealed runtime recovery, preserving original failures."""
from pathlib import Path
import ast,fcntl,hashlib,importlib.util,inspect,json,os,sys,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;W=R/'runs'/C.name
S=R/'runs/v2109_evening_multialgorithm';RID='common_07__SVGMPPI'
O=R/'runs/v2095_svg_common_full_route/rounds'/RID;T=S/'runtime_archives'/RID
FOLDER='remote_delivery_recovery_2114'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,d):
 with p.open('x')as f:json.dump(d,f,indent=2,allow_nan=False)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def gone(i):
 p=Path('/proc',str(i['pid']),'stat');return not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
def prepare(helper):
 tree=ast.parse(inspect.getsource(helper.deliver));fn=tree.body[0]
 fn.args.args.append(ast.arg(arg='preview'));fn.args.defaults.append(ast.Constant(False))
 body=[]
 for n in fn.body:
  if isinstance(n,ast.If)and isinstance(n.test,ast.Name)and n.test.id=='recovery':continue
  if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='census':
   patch="""text=text.replace("O=D/'remote_delivery';", "O=D/"+repr(FOLDER)+";")
old="assert not alias.exists();alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())"
new="assert not alias.exists()or sha(alias)==sha(D/'ARCHIVE_INDEX.json');\\n        if not alias.exists():alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())"
assert text.count(old)==1
text=text.replace(old,new)
if preview:return text
"""
   # This patch source must itself contain a real newline in the string value.
   nodes=ast.parse(patch).body
   newnode=next(x for x in nodes if isinstance(x,ast.Assign)and x.targets[0].id=='new')
   newnode.value=ast.Constant("assert not alias.exists()or sha(alias)==sha(D/'ARCHIVE_INDEX.json');\n        if not alias.exists():alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())")
   body.extend(nodes)
  body.append(n)
 fn.body=body;ast.fix_missing_locations(tree)
 scope=dict(helper.__dict__,FOLDER=FOLDER);exec(compile(tree,'<V2114-transport-wrapper>','exec'),scope)
 generated=scope['deliver'](RID,preview=True);compile(generated,'<V2114-generated-transport>','exec')
 assert "\\n        if not alias.exists():"not in generated
 return scope['deliver'],generated
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert time.time()<read(S/'AUTHORIZATION.json')['absolute_end_unix']-40
 assert read(O/'COMPLETION.json')['closed']and gone(read(O/'OWNED_CHILD.json'))and gone(read(S/'LAUNCH_IDENTITY.json'))
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 locks=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 receipts=[read(p)for p in(T/'remote_delivery/http_receipts').glob('*.json')]
 assert len(receipts)==6 and all(x['call']==1 and x['method']=='GET'and not x['passed']for x in receipts)
 assert read(T/'remote_delivery/RESULT.json')['closed']and not(T/'FULL_REMOTE_VERIFIED.json').exists()and not(T/FOLDER).exists()
 helper=load('V2114_original_transport_helper',R/'experiments/v2109_evening_multialgorithm/evidence.py')
 assert all(sha(R/n)==h for n,h in helper.read(S/'SOURCE_FREEZE.json')['files'].items())
 index=read(T/'ARCHIVE_INDEX.json');assert len(index['files'])==5850 and index['archive_bytes']==50887609 and index['archive_sha256']=='b22916f417d2d0f61b6f727d579cee13749f8987000ab02077d63a6705792909'
 for x in index['parts']:
  p=T/'archive'/x['name'];assert p.stat().st_size==x['bytes']and sha(p)==x['sha256']
 deliver,generated=prepare(helper)
 put(W/'COMPILE_PROOF.json',dict(passed=True,complete_generated_module_compiles=True,generated_sha256=hashlib.sha256(generated.encode()).hexdigest(),old_helper_sha256=sha(Path(helper.__file__)),late_helper_sha256=sha(Path(__file__)),models=0,remote_executed=False))
 put(W/'CLAIM.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),unix=time.time(),maximum_IO_s=600,no_push_ref_reseal_models=True))
 result=dict(closed=False,passed=False,models=0,solver_calls=0,replay=0,new_safety_audits=0,new_push_ref_reseal=False)
 before=sys.path[:];sys.path.insert(0,str(Path(helper.__file__).parent))
 try:
  code=deliver(RID);result.update(returncode=code,passed=code==0)
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
 finally:
  sys.path[:]=before;result.update(closed=True,transport_worker=FOLDER);put(W/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
