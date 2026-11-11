"""One root lock immediately before the first bounded model launch."""
import fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1024_full_route_execution'
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 assert not(O/'ROUND_WINDOW.json').exists(),'NO_ROOT_RESET'
 guard=(R/'REVIEW_PENDING').read_bytes();assert hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 checks=[O/'OWNER_QUALIFICATION.json',O/'ENTRY_QUALIFICATION.json',O/'IMPORT_QUALIFICATION.json',O/'QUEUE_QUALIFICATION.json',O/'FINAL_SOURCE_QUALIFICATION.json',R/'runs/v1023_dense_input_route/FAST_QUALIFICATION.json',R/'runs/v1023_dense_input_route/MARGIN_QUALIFICATION.json',R/'runs/v1023_dense_input_route/CERTIFICATE_QUALIFICATION.json']
 assert all(json.loads(p.read_text())['passed']for p in checks),'MISSING_PRE_MODEL_QUALIFICATION'
 freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==sha for p,sha in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
 start=time.time();window=dict(started_unix=start,absolute_deadline_unix=start+5400,duration_s=5400,single_root=True,old_windows_closed=True,user_authorization='2026-11-11 改好了就开始; new finite development, no old window reused')
 with(O/'ROUND_WINDOW.json').open('x')as f:json.dump(window,f,indent=2)
 dump(O/'APPROVAL.json',dict(models_authorized=True,scope='one complete static then conditional original dynamic and exact repeat',first_failure_stop=True))
 log=(O/'campaign.console').open('x');p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();dump(O/'START_RECEIPT.json',dict(pid=p.pid,**window));print(json.dumps(dict(pid=p.pid,**window)))
if __name__=='__main__':main()
