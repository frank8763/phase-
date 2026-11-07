"""Fixed saved body inputs, no navigation planner or candidate search."""
import fcntl,json,os,sys,time,traceback
from pathlib import Path
import numpy as np
import native_entry
from vehicle import Vehicle,R
from instrumentation import dump
O=R/'runs/v858_nav2_verified/v859_steering';OLD=R/'runs/v858_nav2_verified';lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{sorted(os.sched_getaffinity(0))[3]})
def execute(name,commands):
 v=Vehicle(O/name,'WEST_EAST',10010001,False);start=time.monotonic();maxlag=0.;b=[]
 try:
  for i,(speed,yaw)in enumerate(commands):
   assert time.time()<1794052800-30;target=start+i*.01;time.sleep(max(0.,target-time.monotonic()));maxlag=max(maxlag,time.monotonic()-target);assert maxlag<=.1,'QUALIFICATION_WALL_LAG';v.step(float(speed),float(yaw),False);b.append(v.body())
  result=v.finish();result.update(replay=v.replay(),maximum_wall_lag_s=maxlag);np.savez_compressed(O/name/'BODY_RESPONSE.npz',body=np.asarray(b),target=np.asarray(commands));dump(O/name/'RESULT.json',result);return result,np.asarray(b)
 finally:
  if not hasattr(v,'finished_summary'):v.finish()
try:
 source=np.asarray(json.loads((OLD/'component01/closed_loop_actual/BODY_COMMANDS.json').read_text()));a,body=execute('fixed11',source[:,:2]);forward=float(body[250:390,3].mean());turn=float(body[750:890,4].mean());a_pass=.1<=forward<=.3 and .01<=turn<=.15 and a['final_translation_speed_m_s']<=.03 and a['replay']['passed'];assert a_pass,'FIXED11_ORIGINAL_FUNCTIONAL_GATE'
 source=np.asarray(json.loads((OLD/'entry02/static_main_01/physics/BODY_COMMANDS.json').read_text()));b,body=execute('saved_response',source[:,1:3]);sel=(source[:,0]-source[0,0]>=3)&(source[:,0]-source[0,0]<30);old_error=float(np.sqrt(np.mean((source[sel,2]-source[sel,4])**2)));measured=np.asarray(json.loads((O/'saved_response/BODY_COMMANDS.json').read_text()));new_error=float(np.sqrt(np.mean((source[sel,2]-measured[sel,4])**2)));passed=new_error<=.8*old_error and b['replay']['passed'] and b['bad_contacts']==a['bad_contacts']==0
 result=dict(passed=passed,fixed11=dict(passed=a_pass,steady_forward_m_s=forward,turn_mean_yaw_rad_s=turn,result=a),saved_response=dict(passed=passed,old_yaw_rmse=old_error,new_yaw_rmse=new_error,maximum_allowed=.8*old_error,result=b),actual_native=1100+4174,replay_native=1100+4174,private_native=0,closed=True);dump(O/'QUALIFICATION_RESULT.json',result);assert passed,'SAVED_RESPONSE_NOT_IMPROVED_20PERCENT'
except BaseException as e:
 dump(O/'QUALIFICATION_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),closed=True));raise
