"""Fresh t0 task-driven source using the already qualified original search.

Only public initial pose/map/actuator metadata. No historical command/trace is
read, no simulator is imported, and all routes use the exact same function.
"""
import importlib.abc,json,os,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1061_three_route_readiness'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1023_dense_input_route'))
from input_route import construct
from certificate import audit
def main():
 cpu=2 if 2 in os.sched_getaffinity(0)else min(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpu});rows=[]
 for name in ['WEST_EAST','NORTH_SOUTH','EAST_WEST']:
  x=json.loads((O/(name+'_T0_METADATA.json')).read_text());plan=construct(x['packet'],None,x['goal'],x['setup'],time.time()+45,'pre_detection_static');proof=audit(plan,x['packet'],None,x['setup'],x['goal'])if plan['passed']else dict(passed=False);result=dict(passed=plan['passed']and proof['passed'],case=name,plan=plan,audit=proof,models=0,integrations=0);(O/(name+'_STATIC_SOURCE.json')).write_text(json.dumps(result,indent=2)+'\n');rows.append(dict(case=name,passed=result['passed'],expanded=plan.get('expanded'),status=plan['status']));print(json.dumps(rows[-1]),flush=True)
 (O/'STATIC_SOURCE_QUALIFICATION.json').write_text(json.dumps(dict(passed=all(x['passed']for x in rows),rows=rows,models=0,integrations=0,metadata_proxy_not_new_mjb=True),indent=2)+'\n')
if __name__=='__main__':main()
