"""Bounded first dynamic development, scene certificate before navigation."""
import signal,time,traceback
from pathlib import Path
from bounded_execution import Window,read,dump
src=Path(__file__).resolve().parent
repo=src.parents[1]
origin=read(repo/'runs/v658_dynamic_unknown/development01/WINDOW.json')
window=Window(src,'v659_dynamic_scene_repair','development02',3600,origin['absolute_deadline_unix'])
tasks=[95000011,95000040,95000053];selected=None;outcomes=[];repeat=[];status='DYNAMIC_SCENE_SCREENING'
def stop(*_):raise RuntimeError('BOUNDARY_OR_USER_STOP')
signal.signal(signal.SIGTERM,stop)
try:
 for seed in tasks:
  row=window.run(f'scene_{seed}',seed,'single_event',True)
  if row is None:status='SCENE_BUDGET_INCOMPLETE';break
  if row['feasibility']and row['feasibility']['eligible']:
   selected=seed;dump(window.path/'SELECTED_SCENE.json',{'seed':seed,'source':'first preregistered scene eligible before any navigation','preflight_name':row['name']});break
 if selected is None:status='NO_ELIGIBLE_DYNAMIC_SCENE'
 else:
  for mode in ['instant','predictive']:
   row=window.run(f'dev31_{selected}_{mode}',selected,'single_event',mode=mode)
   if row is None:status='NAVIGATION_BUDGET_INCOMPLETE';break
   result=window.result(row);safe=window.audit(row)
   outcomes.append({'seed':selected,'mode':mode,'name':row['name'],'result':result,'physical_audit_passed':safe})
   dump(window.path/'RESULTS.json',outcomes)
   if not safe:status='STOPPED_PHYSICAL_OR_RECORD_AUDIT';break
  else:
   status='PAIR_COMPLETED'
   if outcomes[-1]['result']['strict_safe_arrival']:
    row=window.run(f'dev31_{selected}_predictive_repeat',selected,'single_event',mode='predictive')
    if row is None:status='REPEAT_BUDGET_INCOMPLETE'
    else:
     record=window.repeat(row,window.root/f'dev31_{selected}_predictive/paired');repeat.append(record)
     dump(window.path/'REPEAT_AUDIT.json',repeat);status='PREDICTIVE_REPEAT_MATCHED'if record['matched']else'PREDICTIVE_REPEAT_FAILED'
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(window.path/'ERROR.json',{'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
finally:
 dump(window.path/'COMPLETION.json',{'status':status,'elapsed_s':time.monotonic()-window.started,'limit_s':window.limit,
      'selected_seed':selected,'navigation_branches':len(outcomes),'predictive_repeat_attempted':bool(repeat),
      'dynamic_stability_acceptance_passed':False,'training_updates':0,'scope':'first paired dynamic development, not independent confirmation'})
 dump(window.path/'ACTIVE.json',{'status':status,'completed':True});print('DYNAMIC_DEVELOPMENT_COMPLETE',status,flush=True)
