import importlib.abc,json,sys,time,signal
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1029_declared_course_source';sys.path.insert(0,str(C))
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('CLIPPING_CHECK_180S')));signal.alarm(180)
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from fast_periodic import PeriodicSupport,original
saved=json.loads((R/'runs/v858_nav2_verified/v1024/dynamic_we/CAUSAL_EVIDENCE.json').read_text());a=original.PeriodicSupport();b=PeriodicSupport();old_s=new_s=0.;rows=[]
for row in saved['periodic_constraints']:
 t=time.monotonic();a.update(row['time'],row['native_tick'],row['support']);old_s+=time.monotonic()-t;t=time.monotonic();b.update(row['time'],row['native_tick'],row['support']);new_s+=time.monotonic()-t
 exact=all(np.array_equal(x.v,y.v)and np.array_equal(x.a,y.a)and np.array_equal(x.b,y.b)for x,y in zip(a.polytopes,b.polytopes));assert exact,'CLIPPING_NOT_EXACT'
 rows.append(dict(native_tick=row['native_tick'],vertices_planes_and_bounds_exact=exact))
expected=json.loads((R/'runs/v858_nav2_verified/v1024/dynamic_we/DYNAMIC_COMPLETE_PLAN.json').read_text())['source']['periodic'];assert b.snapshot()==expected
out=dict(passed=True,all_original_constraints=len(rows),all_each_update_vertices_planes_bounds_exact=True,final_saved_snapshot_exact=True,old_wall_s=old_s,new_wall_s=new_s,models=0,integrations=0,rows=rows);(O/'CLIPPING_EQUIVALENCE.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='rows'}));signal.alarm(0)
