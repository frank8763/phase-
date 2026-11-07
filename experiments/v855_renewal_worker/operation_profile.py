"""Transparent inclusive operation timers; no policy, prediction or state changes."""
import atexit,functools,json,time
from collections import defaultdict
from pathlib import Path

def timed(name,function,stats):
 @functools.wraps(function)
 def call(*args,**kwargs):
  start=time.perf_counter()
  try:return function(*args,**kwargs)
  finally:
   elapsed=time.perf_counter()-start
   stats[name]['calls']+=1;stats[name]['inclusive_wall_s']+=elapsed;stats[name]['samples_wall_s'].append(elapsed)
 return call

def install(outer):
 import geometry_predictor,reserved_recovery,reference_recovery,numpy as np
 stats=defaultdict(lambda:dict(calls=0,inclusive_wall_s=0.,samples_wall_s=[]))
 for module,name,label in[(geometry_predictor.RobotPredictor,'predict','native_predict'),(geometry_predictor.RobotPredictor,'select','nominal_select'),(reserved_recovery.ReservedRecovery,'admit_nominal','complete_admission'),(reference_recovery,'predict_follow','reference_feedback_predict'),(np,'savez_compressed','compressed_npz_write')]:setattr(module,name,timed(label,getattr(module,name),stats))
 def finish():
  values={}
  for name,record in stats.items():
   samples=record['samples_wall_s']
   values[name]={**record,'p50_wall_s':float(np.percentile(samples,50)),'p95_wall_s':float(np.percentile(samples,95)),'p99_wall_s':float(np.percentile(samples,99)),'maximum_wall_s':max(samples)}
  (Path(outer)/'paired'/'OPERATION_PROFILE.json').write_text(json.dumps(dict(operations=values,overlapping_inclusive_timers_do_not_add=True,models_added=0,integrations_added=0,hidden_truth_read=False),indent=2)+'\n')
 atexit.register(finish)
 return finish
