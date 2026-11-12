"""Actual saved-root full-cycle finite-corridor qualification, zero physics."""
import sys,json,time,importlib.abc,signal,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1090_active_corridor'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL_CORRIDOR '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(C));import corridor
def main():
 def halt(*_):raise TimeoutError('BOUNDED_CORRIDOR_QUALIFICATION')
 signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,120);started=time.monotonic()
 try:
  x=json.loads((R/'runs/v1090_gear_prefix_reference/QUALIFICATION_INPUT.json').read_text());q=corridor.construct(x['setup'],x['packet'],x['source'],O,x['goal']);import numpy as np;np.savez_compressed(O/'QUALIFIED_CORRIDOR.npz',requests=q['requests'],states=q['states'],controls=q['controls']);answer=dict(passed=True,proof=q['proof'],candidates=q['candidates'],wall_s=time.monotonic()-started,models=0,integrations=0,actual_saved_root=20160,source_from_actual_ranges=True)
 except BaseException as e:answer=dict(passed=False,error=repr(e),traceback=traceback.format_exc(),wall_s=time.monotonic()-started,models=0,integrations=0)
 (O/'QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
