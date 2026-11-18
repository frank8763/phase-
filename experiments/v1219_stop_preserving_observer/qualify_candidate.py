import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('NO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import time,json,fcntl
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
from candidate_observer import synthesize,q,np
read=lambda p:json.loads(p.read_text())
def main(case):
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 raw=R/({'slot03':'runs/v858_nav2_verified/v1218/main_slot03','slot01':'runs/v858_nav2_verified/v1218/main_slot01','slot02':'runs/v858_nav2_verified/v1218/main_slot02','original_WE':'runs/v858_nav2_verified/v1217/main_WEST_EAST'}[case]);x=read(raw/'LIVE_OBSERVER_INPUT.json')
 with np.load(raw/'LIVE_OBSERVER_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 out=O/('CANDIDATE_'+case);out.mkdir();start=time.monotonic()
 try:
  answer=synthesize(x,table,time.monotonic()+300,lambda p:q.dump(out/'PROGRESS.json',p))
  if answer['passed']:np.savez_compressed(out/'REFERENCE.npz',**{k:answer.pop(k)for k in ['states','controls','memory']})
  answer['wall_s']=time.monotonic()-start;q.dump(out/'RESULT.json',answer);print(json.dumps({k:v for k,v in answer.items()if k not in ['trials','complete_stop_qualification','rows','proof']}))
 except BaseException as e:
  import traceback;q.dump(out/'ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0,analytical_incomplete_unknown=True));raise
if __name__=='__main__':main(sys.argv[1])
