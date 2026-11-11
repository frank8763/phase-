"""Analytical producer only; no model imports or actuator ownership."""
import importlib.abc,json,os,signal,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ANALYTICAL_JOB_CANNOT_LOAD_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import pin_threads,HARD_END
from handoff import prepare
def main():
 folder=Path(sys.argv[1]);x=json.loads((folder/'INPUT.json').read_text());pin_threads()
 def stop(*_):raise InterruptedError('SOURCE_JOB_FIXED_CAP')
 signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.001,min(15.,HARD_END-time.time()-30)))
 try:result=prepare(x['setup'],x['packet'],x['source'],x['goal'],x['actions'],x['elapsed'])
 except BaseException as e:result=dict(passed=False,error=repr(e),models=0)
 temporary=folder/'RESULT.tmp';temporary.write_text(json.dumps(result,allow_nan=False));os.replace(temporary,folder/'RESULT.json')
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
