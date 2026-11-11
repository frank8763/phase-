"""One immutable relay configuration. Pure analytical, never a vehicle import."""
import importlib.abc,json,signal,sys,time
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from search import construct

def audit_source(x,result,end):
 ss,uu,rr,mm=predict(x['setup'],x['packet'],result['actions']);assert np.max(abs(ss-np.asarray(result['state_path'])))<=1e-10 and np.max(abs(uu-np.asarray(result['predicted_actuator_controls'])))<=1e-10,'PROFILE_REBUILD'
 geometry=Geometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']);engine=Expander(x['setup']);minimum=math.inf
 for i in range(len(ss)):
  assert time.time()<end,'FULL_STOP_AUDIT_TIME_CAP';safe,lower=stop_witness(engine,geometry,ss[i],mm[i],i);minimum=min(minimum,lower)
  if not safe:return dict(passed=False,first_failed_native=i,minimum_stop_raw_m=minimum,all_native_required=len(ss),all_native_checked=i+1,models=0)
 return dict(passed=True,all_native_required=len(ss),all_native_checked=len(ss),minimum_stop_raw_m=minimum,models=0)

def main():
 cfg=json.loads(Path(sys.argv[1]).read_text());out=O/'sources'/cfg['id'];out.mkdir(parents=True,exist_ok=False);pin_threads();deadline=min(float(sys.argv[2]),time.time()+cfg['wall_s']);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ROOT_SOURCE_CAP')));signal.setitimer(signal.ITIMER_REAL,max(.001,deadline-time.time()))
 x=json.loads((O/'INPUT_SOURCE.json').read_text());result=None
 try:
  result=construct(x,cfg,deadline-125,lambda p:dump(out/'PARTIAL.json',p))
  if result['passed']:
   proof=audit_source(x,result,deadline-5);result['all_native_stop_audit']=proof
   if not proof['passed']:
    result={k:v for k,v in result.items()if k not in ['state_path','planned_body_requests','predicted_actuator_controls']};result.update(passed=False,status='FULL_NATIVE_STOP_AUDIT_REJECTED')
  result['input_source_sha256']=sha(O/'INPUT_SOURCE.json');dump(out/'RESULT.json',result)
 except BaseException as e:dump(out/'ERROR.json',dict(error=repr(e),models=0,integrations=0));return 1
 finally:signal.setitimer(signal.ITIMER_REAL,0)
 print(json.dumps({k:v for k,v in result.items()if k not in ['state_path','planned_body_requests','predicted_actuator_controls','actions','nearest_actions']}),flush=True);return 0
if __name__=='__main__':sys.exit(main())
