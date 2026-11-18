"""Fixed real saved NS inputs, no physical model or artificial observations."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import json,time,fcntl,traceback,copy
from package_loader import get_goal_entry
entry=get_goal_entry();q=entry.q;np=entry.np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def main(case):
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 raw=R/'runs/v858_nav2_verified'/('v1222/main_slot09'if case=='slot09'else 'v1220/regression_main_NORTH_SOUTH');x=read(raw/'ROUTE_RECOVERY_INPUT.json')
 with np.load(raw/'ROUTE_JOINT_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 out=O/('SOURCE_'+case);out.mkdir();begin=time.monotonic();origin=entry.bind_current(x,x['packet'],False)
 try:
  answer=entry.generate(x,table,origin,0,time.monotonic()+150,lambda p:q.dump(out/'PROGRESS.json',p),shadow_origin=copy.deepcopy(origin))
  if answer['passed']:np.savez_compressed(out/'REFERENCE.npz',**{k:answer.pop(k)for k in ['states','controls','memory']})
  answer.update(wall_s=time.monotonic()-begin,models=0,new_mujoco_native=0,real_saved_causal_input=True);q.dump(out/'RESULT.json',answer)
  print(json.dumps({k:answer[k]for k in ['passed','wall_s','analytical_cpp_native','admission_python_native','best']},default=lambda a:a.item()))
 except BaseException as e:q.dump(out/'ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,analytical_inflight_unknown=True));raise
if __name__=='__main__':main(sys.argv[1])
