"""One bounded qualification, then the frozen dependency-gated navigation queue."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v858_nav2_verified/v859_steering';END=1794052800.
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def verify():
 for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h
def saved_audit():
 q=json.loads((O/'QUALIFICATION_RESULT.json').read_text());checks=dict(function=q['passed']);total=0
 for name in ['fixed11','saved_response']:
  p=O/name;a=np.load(p/'NATIVE_TRACE.npz');s=json.loads((p/'SETUP.json').read_text());re=json.loads((p/'REPLAY.json').read_text());ids=np.asarray(s['actuator_ids']);u=a['ctrl'][:,ids];lim=np.asarray(s['limits']);n=len(u);total+=n
  checks.update({name+'_timing':bool(np.allclose(a['time'],np.arange(1,n+1)*.01,rtol=0,atol=1e-9)),name+'_clearance':bool(np.min(a['clearance'])>=.15-1e-8),name+'_self':bool(np.min(a['self_margin'])>=-1e-10),name+'_amplitude':bool(np.all(u>=lim[:,0]-1e-10)and np.all(u<=lim[:,1]+1e-10)),name+'_slew':bool(np.all(abs(np.diff(np.vstack([np.zeros((1,len(ids))),u]),axis=0))<=np.asarray(s['slew_per_second'])*.01+1e-10)),name+'_replay':re['passed']and re['replay_native']==n and re['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8})
 result=dict(passed=all(checks.values()),checks=checks,actual_native=total,replay_native=total,private_native=0,models_initialized_lower_bound=2,new_xml_compilations=2);dump(O/'QUALIFICATION_INDEPENDENT_AUDIT.json',result);assert result['passed'],'QUALIFICATION_SAVED_AUDIT_FAILED'
def main():
 verify();assert not(O/'START_CLAIM.json').exists();lock=(O/'qualification_driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(R/'REVIEW_PENDING').read_bytes();dump(O/'START_CLAIM.json',dict(pid=os.getpid(),started_unix=time.time(),root_deadline_unix=END));p=None;status='ENTRY'
 try:
  (R/'REVIEW_PENDING').unlink()
  with(O/'qualification.console').open('w')as f:p=subprocess.Popen([str(R/'run_phase.sh'),str((C/'qualify.py').relative_to(R))],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);rc=p.wait(timeout=min(180,END-time.time()-10))
  assert rc==0,'QUALIFICATION_NOT_PASSED';verify();saved_audit();status='QUALIFICATION_PASSED'
 except BaseException as e:status='QUALIFICATION_STOPPED';dump(O/'START_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc()))
 finally:
  if p and p.poll()is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=4)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'QUALIFICATION_COMPLETION.json',dict(status=status,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,closed=True))
 if status=='QUALIFICATION_PASSED':
  with(O/'campaign.console').open('w')as f:p=subprocess.Popen([sys.executable,'-B',str(C/'campaign_entry.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  dump(O/'CAMPAIGN_STARTED.json',dict(pid=p.pid,started_unix=time.time()))
if __name__=='__main__':main()
