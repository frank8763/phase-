"""Applied-only command journal and explicit complete-stop transaction."""
import numpy as np
from logic import SteeringModeRefusal,Predictor,initial,kernel
def applied_step(vehicle,request,parked,target,phase,index,journal,rejected):
 vehicle.adapter.parked_target=float(target)if parked else None
 row=dict(phase=phase,nominal_index=index,parked=bool(parked),target=float(target),before_native=vehicle.count,last_ctrl=vehicle.adapter.last.tolist(),integral=float(vehicle.adapter.integral))
 before=vehicle.count
 try:vehicle.step(float(request[0]),float(request[1]),False)
 except BaseException as error:
  if vehicle.count==before:rejected.append(dict(**row,error=repr(error),applied=False,actual_body=list(vehicle.body())))
  else:journal.append(row)
  raise
 journal.append(row)
def complete_stop_source(setup,packet):
 p=Predictor(setup,initial(packet),kernel.PARAMETERS);ss=[p.state.copy()];uu=[]
 for _ in range(2200):s,u=p.step(0.,0.,False);ss.append(s);uu.append(u)
 ss=np.array(ss);uu=np.array(uu);a,_=kernel.ref._old.Geometry(setup['known'],None).clearances(ss[:,:3]);limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01
 checks=dict(full2200=len(uu)==2200,raw=float(a.min())>=kernel.REQUIRED,body_caps=bool((abs(ss[:,3:6])<=np.array([.13,.03,.16])).all()),ctrl=bool((uu>=limits[:,0]-1e-10).all()and(uu<=limits[:,1]+1e-10).all()),slew=bool((abs(np.diff(np.vstack([packet['controller_memory']['last_ctrl'],uu]),axis=0))<=rates+1e-10).all()),terminal_rest=bool(abs(ss[-50:,3:6]).max()<=.003 and abs(ss[-50:,7]).max()<=.015))
 return dict(passed=all(checks.values()),checks=checks,minimum_raw_m=float(a.min()),analytical_native=2200),ss,uu
def execute_complete_stop(step,permit):
 for _ in range(2200):
  assert permit(),'COMPLETE_STOP_DEADLINE'
  step(0.,0.,False,0.,'failure_hold_stop',None)
