"""Pure analytical producer. This entry cannot import a vehicle/model runtime."""
import importlib.abc,json,signal,sys,time,os
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from resource_policy import apply
apply()
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL_ONLY '+name)
sys.meta_path.insert(0,NoModel())
from kernel import pin_threads
from handoff import prepare

def main():
 folder=Path(sys.argv[1]);x=json.loads((folder/'INPUT.json').read_text());pin_threads();started=time.monotonic()
 def stop(*_):raise InterruptedError('PURE_SOURCE_JOB15S_CAP')
 signal.signal(signal.SIGALRM,stop);from kernel import HARD_END
 signal.setitimer(signal.ITIMER_REAL,max(.001,min(15.,HARD_END-time.time()-30)))
 try:result=prepare(x['setup'],x['packet'],x['source'],x['goal'],x['actions'],x['elapsed'])
 except BaseException as e:result=dict(passed=False,error=repr(e),models=0,integrations=0)
 result['actual_job_wall_s']=time.monotonic()-started;signal.setitimer(signal.ITIMER_REAL,0);temp=folder/'RESULT.tmp';data=json.dumps(result,allow_nan=False);
 try:
  from budget import check
  check(len(data.encode())+128*1024**2)
 except BaseException as e:result=dict(passed=False,error=repr(e),models=0,integrations=0);data=json.dumps(result)
 temp.write_text(data);os.replace(temp,folder/'RESULT.json');return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
