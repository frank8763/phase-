import importlib.abc,json,sys,time,math
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1038_staged_timed_source'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from stage_search import construct
row=json.loads((R/'runs/v1037_periodic_norm_source/SOURCE.json').read_text())
# Public lower-right rectangle: stage before its left end, above its top.
rectangle=np.asarray(row['setup']['known']['known_rectangles'][9]);stage=[float(rectangle[0]-rectangle[2]-.85),float(rectangle[1]+rectangle[3]+.75),0.]
started=time.time();result=construct(row['packet'],row['source'],row['setup'],stage,time.time()+90)
(O/'STAGING.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['actions','state_path','planned_body_requests','predicted_actuator_controls']}),flush=True)
