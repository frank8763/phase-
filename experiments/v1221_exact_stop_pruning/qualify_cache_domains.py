"""Distinct source/geometry/state inputs cannot collide in exact caches."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import copy,json,fcntl
from candidate_observer import q,np
from exact_cache import interval_cache
R=Path(__file__).resolve().parents[2];O=R/'runs/v1221_exact_stop_pruning'
def run():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 p=R/'runs/v858_nav2_verified/v1220/main_slot02';x=json.loads((p/'LIVE_OBSERVER_INPUT.json').read_text())
 timed=q.Geometry.__init__.__globals__['OriginalTimed'];env=timed.__init__.__globals__;f=env['interval_support'];vertices=x['source']['periodic']['vertices'];starts=np.array([.1,.2]);ends=starts+.03
 changed=copy.deepcopy(vertices);
 for vertex in changed[0]:vertex[0]+=.001
 cases=[(vertices,starts,ends),(changed,starts,ends),(vertices,starts+.01,ends+.01)]
 baseline=[f(*a).copy()for a in cases]
 with interval_cache(q)as stats:
  actual=[env['interval_support'](*a).copy()for a in cases]
  again=env['interval_support'](*cases[0]);assert np.array_equal(again,baseline[0])
 assert all(np.array_equal(a,b)for a,b in zip(actual,baseline)) and not np.array_equal(baseline[0],baseline[1])and stats['misses']==3 and stats['hits']==1
 assert env['interval_support']is f
 result=dict(passed=True,changed_vertices_and_time_do_not_collide=True,all_raw_arrays_exact=True,binding_restored=True,models=0,new_mujoco_native=0,analytical_propagations=0);q.dump(O/'CACHE_DOMAIN_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':run()
