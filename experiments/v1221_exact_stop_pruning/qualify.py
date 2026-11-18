import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import json,time,fcntl,traceback
from candidate_observer import synthesize,q,np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def main(case):
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 raw=R/'runs/v858_nav2_verified'/('v1220/main_slot02'if case=='slot02'else 'v1218/main_'+case)
 x=read(raw/'LIVE_OBSERVER_INPUT.json')
 with np.load(raw/'LIVE_OBSERVER_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 out=O/('QUALIFIED_'+case);out.mkdir();begin=time.monotonic()
 try:
  answer=synthesize(x,table,time.monotonic()+600,lambda p:q.dump(out/'PROGRESS.json',p));assert answer['passed'];np.savez_compressed(out/'REFERENCE.npz',**{k:answer.pop(k)for k in ['states','controls','memory']})
  if case in ['slot01','slot03']:
   old=read(R/'runs/v1219_stop_preserving_observer'/('CANDIDATE_'+case)/'RESULT.json');assert all(answer['selected'][k]==old['selected'][k]for k in ['turn','stage_native','cut','minimum_stop_raw_m'])
   with np.load(R/'runs/v1219_stop_preserving_observer'/('CANDIDATE_'+case)/'REFERENCE.npz')as a,np.load(out/'REFERENCE.npz')as b:
    assert all(np.array_equal(a[k],b[k])for k in a.files)
   answer['old_exhaustive_arrays_exact']=True
  answer['wall_s']=time.monotonic()-begin;q.dump(out/'RESULT.json',answer);print(json.dumps({k:v for k,v in answer.items()if k not in ['trials','complete_stop_qualification','rows','proof']},default=lambda a:a.item()))
 except BaseException as e:q.dump(out/'ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,unfinished_analytical_unknown=True));raise
if __name__=='__main__':main(sys.argv[1])
