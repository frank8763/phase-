"""Lock one new 90-minute root; never reopen old physical windows."""
import fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1044_curvature_speed_prediction'
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 assert not(O/'ROUND_WINDOW.json').exists(),'NO_WINDOW_RESET'
 assert hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 assert all(json.loads((O/name).read_text())['passed']for name in ['ZERO_MODEL_QUALIFICATION.json','ENTRY_QUALIFICATION.json'])
 freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items()),'SOURCE_CHANGED'
 start=time.time();window=dict(started_unix=start,absolute_deadline_unix=start+5400,duration_s=5400,maximum_models=3,maximum_navigation_native=1500,maximum_own_replay_native=1500,private_mujoco_native=0,old_windows_closed=True,scope='fixed straight/left/right .08 curvature-speed prediction response; no navigation or 24',user_authorization='2026-11-11 下一步开始; bounded source qualification and necessary original-task component verification')
 with(O/'ROUND_WINDOW.json').open('x')as f:json.dump(window,f,indent=2)
 dump(O/'APPROVAL.json',dict(models_authorized=True,first_failure_stop=True,no_navigation=True));log=(O/'campaign.console').open('x');p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();dump(O/'START_RECEIPT.json',dict(pid=p.pid,**window));print(json.dumps(dict(pid=p.pid,**window)))
if __name__=='__main__':main()
