"""Profile fixed saved complete certificates; no vehicle model import."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','vehicle','torch','rclpy'}:raise AssertionError('ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from pathlib import Path
import json,time,fcntl,cProfile,pstats,io
from candidate_observer import q,np,stops,original
from exact_cache import interval_cache
R=Path(__file__).resolve().parents[2];O=R/'runs/v1221_exact_stop_pruning';read=lambda p:json.loads(p.read_text())
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 raw=R/'runs/v858_nav2_verified/v1220/repair_main_slot03';x=read(raw/'LIVE_OBSERVER_INPUT.json');records=read(raw/'LIVE_OBSERVER_CERTIFICATES.json')[:6];rows=read(raw/'LIVE_OBSERVER_SELECTION.json')['rows']
 with np.load(raw/'LIVE_OBSERVER_TABLE.npz')as z:table={k:z[k].copy()for k in z.files}
 g=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients'])
 def run():
  answer=[]
  for c in records:
   p=c['packet'];pr,ss=stops.prove(engine,g,x,p,dict(q.initial(p),steering_load_episode=c['steering_load_episode']),original.front(original.remaining_rows(rows,c['offset']),c['prefix']));answer.append((pr,[a.copy()for a in ss]))
  return answer
 pr=cProfile.Profile();begin=time.monotonic();pr.enable();a=run();pr.disable();baseline=time.monotonic()-begin
 with interval_cache(q)as stats:begin=time.monotonic();b=run();cached=time.monotonic()-begin
 for (pp,aa),(qq,bb)in zip(a,b):
  assert json.dumps(pp,sort_keys=True,default=lambda a:a.item())==json.dumps(qq,sort_keys=True,default=lambda a:a.item()) and all(np.array_equal(x,y)for x,y in zip(aa,bb))
 buf=io.StringIO();pstats.Stats(pr,stream=buf).sort_stats('cumtime').print_stats(18);(O/'PROFILE_COMPLETE.txt').write_text(buf.getvalue())
 result=dict(passed=True,fixed_pairs=len(records),all_proofs_and_states_exact=True,baseline_s=baseline,cached_s=cached,cache=stats,analytical_cpp_native=engine.native,models=0,new_mujoco_native=0);q.dump(O/'CACHE_COMPLETE_QUALIFICATION.json',result);print(json.dumps(result));print(buf.getvalue()[:3500])
if __name__=='__main__':main()
