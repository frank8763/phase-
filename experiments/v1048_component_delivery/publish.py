"""Publish closed V1044 evidence while its relay's pure source child continues.

Briefly pause ONLY the known relay parent so it cannot race a new model against
publication's execution lock. Source computation, deadlines, and frozen code
continue unchanged. An independent bounded helper guarantees parent resumption.
"""
import json,os,signal,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1047_day_relay_20261111';P=R/'runs/v1044_curvature_speed_prediction'
def stamp(pid):
 try:
  s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();return s[19],s[0]
 except FileNotFoundError:return None,None

def main():
 receipt=json.loads((O/'START_RECEIPT.json').read_text());pid=receipt['driver_pid'];assert stamp(pid)[0]==receipt['pid_start'];a=json.loads((O/'ACTIVE.json').read_text());assert a['kind']=='source'and not(P/'PUBLICATION_CLAIM.json').exists();assert not(O/'COMPONENT_DELIVERY_CLAIM.json').exists();(O/'COMPONENT_DELIVERY_CLAIM.json').write_text(json.dumps(dict(started=time.time(),parent_pid=pid,source_child_pid=a['pid'],models=0))+'\n');child=None;started=time.time();os.kill(pid,signal.SIGSTOP)
 helper=Path(__file__).with_name('resume.py');subprocess.Popen([sys.executable,'-B',str(helper),str(pid),receipt['pid_start']],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 try:
  assert json.loads((O/'ACTIVE.json').read_text())['kind']=='source','MODEL_STARTED_BEFORE_PARENT_PAUSE'
  import fcntl
  with (R/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
  with(P/'publication.console').open('x')as log:child=subprocess.Popen([sys.executable,'-B',str(R/'experiments/v1045_curvature_timed_route/publish_closed.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);code=child.wait(timeout=120)
  assert code==0,'PUBLICATION_EXIT '+str(code)
 finally:
  if child is not None and child.poll()is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(5)
  if stamp(pid)[0]==receipt['pid_start']:os.kill(pid,signal.SIGCONT)
  (O/'COMPONENT_DELIVERY_PARENT_RESUMED.json').write_text(json.dumps(dict(at=time.time(),parent_pid=pid,parent_pause_s=time.time()-started,source_child_not_paused=True,model_integrations_added=0,frozen_source_changed=False,deadline_changed=False))+'\n')
if __name__=='__main__':main()
