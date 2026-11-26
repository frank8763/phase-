from pathlib import Path
import ast,hashlib,importlib.util,inspect,json,os,sys,time,traceback,fcntl
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;S=R/'runs/v2045_remaining_parallel_source';RID='common_08__MPPI';CASE=S/'rounds'/RID;D=S/'runtime_archives'/RID
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(O/'ONCE.json').exists();put(O/'ONCE.json',dict(pid=os.getpid(),unix=time.time(),maximum_IO_s=600,new_models=0));result=dict(passed=False,closed=False,models=0,physics=0,replay=0)
 try:
  assert read(R/'runs/v2051_mppi_remaining_seven_resume/RESULT.json')['closed']and read(CASE/'COMPLETION.json')['closed'];assert read(CASE/'RUNTIME_CLOSED_REVIEW.json')['valid_finite_method_refusal'];assert not(D/'FULL_REMOTE_VERIFIED.json').exists()
  assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
   with(R/n).open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  p=R/'experiments/v2045_remaining_parallel_source/evidence.py';spec=importlib.util.spec_from_file_location('frozen_same_archive_IO',p);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h);assert all(h.sha(R/n)==v for n,v in h.read(S/'SOURCE_FREEZE.json')['files'].items())
  index=read(D/'ARCHIVE_INDEX.json');assert sha(D/'ARCHIVE_INDEX.json')=='c60e4b8da851a6274e5eaeab859cbf746ae8c58f3ccf68589656da0913f5f3b5'
  for row in index['parts']:q=D/'archive'/row['name'];assert q.stat().st_size==row['bytes']and h.sha(q)==row['sha256']
  source=inspect.getsource(h.deliver);needle="text=target.read_text()";assert source.count(needle)==1;source=source.replace(needle,needle+';text=text.replace("O=D/\'remote_delivery\';", "O=D/\'remote_delivery_recovery_2057\';")');ast.parse(source)
  put(O/'METADATA_PATCH_PROOF.json',dict(original_helper_sha256=sha(p),old_failed_result_sha256=sha(D/'remote_delivery/RESULT.json'),second_failed_result_sha256=sha(D/'remote_delivery_resume_2051/RESULT.json'),original_archive_index_sha256=sha(D/'ARCHIVE_INDEX.json'),transport_worker_directory_only=True,patched_function_AST_sha256=hashlib.sha256(ast.dump(ast.parse(source)).encode()).hexdigest(),no_new_archive_or_Git_or_numerical_calls=True));namespace=dict(h.__dict__);exec(compile(source,str(p),'exec'),namespace);code=namespace['deliver'](RID);assert code==0;result['passed']=True
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result['closed']=True;put(O/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
