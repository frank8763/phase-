"""Prepare fixed old NS static response at .12 instead of .08; zero physical models."""
import sys,copy
from afternoon_tools import *
sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'));import logic
import numpy as np

def main():
 assert not(O/'ROUND_WINDOW.json').exists();fixture=json.loads((R/'experiments/v1114_coupled_steering_mode/STATIC_T0_SOURCE_FIXTURE.json').read_text());dump(C/'STATIC_T0_SOURCE_FIXTURE.json',fixture);tasks=json.loads((R/'experiments/v1114_coupled_steering_mode/TASKS.json').read_text());old=logic.schedule
 def schedule(sign):return [(name,200 if name=='restart'else n,.12 if name=='restart'else v,target,parked)for name,n,v,target,parked in old(sign)]
 logic.schedule=schedule;rows=[]
 for task in tasks:
  task.update(output=str(R/'runs/v858_nav2_verified/v1139'/task['task_id']),run_id='v1139-'+task['task_id']);plan,phases=logic.predict_profile(fixture['setup'],fixture['packet'],task['sign']);ss=plan['states'];static=logic.kernel.ref._old.Geometry(fixture['setup']['known'],None).clearances(ss[:,:3])[0];assert static.min()>=logic.kernel.REQUIRED+.001,'PREDICTED_STATIC_RESPONSE_CLEARANCE';assert (abs(ss[:,3:6])<=np.array([.13,.03,.16])).all();assert len(plan['controls'])==8000 and np.all(plan['requests'][-2200:,:2]==0.)
  np.savez_compressed(C/('PLAN_'+task['task_id']+'.npz'),**plan);dump(C/('PHASES_'+task['task_id']+'.json'),phases);dump(C/('TASK_'+task['task_id']+'.json'),task);rows.append({'task':task['task_id'],'predicted_native':8000,'minimum_static_raw_m':float(static.min()),'forward_request':.12})
 dump(C/'TASKS.json',tasks);dump(O/'PREPARATION.json',{'passed':True,'static_plans':rows,'analytical_python_native':16000,'models':0,'physical_integrations':0});print(encode(rows))
if __name__=='__main__':main()
