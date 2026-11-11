"""A new independent 90m cap for one fixed historical-state component."""
import fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1039_causal_approach'
def main():
 assert not(O/'ROUND_WINDOW.json').exists(),'NO_WINDOW_RESET';assert hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for name in ['SOURCE_QUALIFICATION.json','ENTRY_QUALIFICATION.json']:assert json.loads((O/name).read_text())['passed']
 frozen=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in frozen['files'].items()),'SOURCE_CHANGED'
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 start=time.time();window=dict(started_unix=start,absolute_deadline_unix=start+5400,duration_s=5400,maximum_vehicles=1,historical_replay_native=16740,maximum_new_component_native=6900,maximum_own_replay_native=23640,navigation_native=0,private_mujoco_native=0,old_windows_closed=True,user_authorization='2026-11-11 检查，然后继续推进; one fixed bounded causal observation component only')
 with(O/'ROUND_WINDOW.json').open('x')as f:json.dump(window,f,indent=2)
 (O/'APPROVAL.json').write_text(json.dumps(dict(models_authorized=True,first_failure_stop=True,one_component_only=True))+'\n');log=(O/'campaign.console').open('x');p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();(O/'START_RECEIPT.json').write_text(json.dumps(dict(pid=p.pid,**window),indent=2)+'\n');print(json.dumps(dict(pid=p.pid,**window)))
if __name__=='__main__':main()
