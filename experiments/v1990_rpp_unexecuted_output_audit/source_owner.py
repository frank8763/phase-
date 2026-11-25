"""Bounded metadata-only SOURCE owner; continuous two idle-model locks."""
from context import R,C,O,read,put,sha
import fcntl,os,signal,subprocess,time,traceback

def main():
 os.sched_setaffinity(0,{5});start=time.monotonic();assert not(O/'SOURCE_OUTER_ONCE_CLAIM.json').exists()and not(O/'SOURCE_QUALIFICATION.json').exists();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 locks=[]
 for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/name).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and not current['models_now_authorized'];used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(8+32+32+512)*1024**2<15*1024**3
 put(O/'SOURCE_OUTER_ONCE_CLAIM.json',dict(unix=time.time(),maximum_wall_s=150,models=0));result=dict(passed=False,closed=False,models=0,physical_native=0)
 try:
  p=subprocess.run(['/usr/bin/python3','-B',str(C/'prepare_source.py')],cwd=R,capture_output=True,timeout=150,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES=''));(O/'source.console').write_bytes(p.stdout+p.stderr);q=read(O/'SOURCE_QUALIFICATION.json');assert p.returncode==0 and q['passed']and q['closed'];assert all(sha(R/n)==h for n,h in read(O/'SOURCE_FREEZE.json')['files'].items());result.update(passed=True,all_source_SHA_verified_after_child_exit=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start,review_restored=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66');put(O/'SOURCE_OUTER_CLOSED.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
