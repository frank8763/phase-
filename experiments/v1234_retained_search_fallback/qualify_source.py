import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import copy,json,time,fcntl,traceback
from package_loader import get_goal_entry
e=get_goal_entry();q=e.q;np=e.np;C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def main(case):
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 roots=dict(slot10=('v1230/main_slot10','LIVE_GOAL'),slot09=('v1230/main_slot09','LIVE_GOAL'),oldNS=('v1220/regression_main_NORTH_SOUTH','ROUTE'))
 folder,kind=roots[case];raw=R/'runs/v858_nav2_verified'/folder
 x=read(raw/('ROUTE_RECOVERY_INPUT.json'if kind=='ROUTE'else'LIVE_GOAL_INPUT.json'))
 with np.load(raw/('ROUTE_JOINT_TABLE.npz'if kind=='ROUTE'else'LIVE_GOAL_TABLE.npz'))as z:t={k:z[k].copy()for k in z.files}
 out=O/('SOURCE_'+case);out.mkdir();org=e.bind_current(x,x['packet'],False);start=time.monotonic()
 try:
  d=e.generate(x,t,org,0,time.monotonic()+150,lambda x:q.dump(out/'PROGRESS.json',x),shadow_origin=copy.deepcopy(org))
  if d['passed']:np.savez_compressed(out/'REFERENCE.npz',**{k:d.pop(k)for k in ['states','controls','memory']})
  d.update(models=0,new_mujoco_native=0,actual_saved_causal_input=True);q.dump(out/'RESULT.json',d);print(json.dumps({k:d.get(k)for k in ['passed','wall_s','phase_expanded','terminal_attempts','analytical_cpp_native','best']},default=lambda v:v.tolist()if hasattr(v,'tolist')else v.item()))
 except BaseException as er:q.dump(out/'ERROR.json',dict(error=repr(er),traceback=traceback.format_exc(),models=0,new_mujoco_native=0,unfinished_analytical_work_unknown=True));raise
if __name__=='__main__':main(sys.argv[1])
