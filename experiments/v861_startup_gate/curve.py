"""One fixed body-command curve, native physics only through frozen Vehicle."""
import fcntl,json,math,os,runpy,sys,time,traceback,signal
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v858_nav2_verified/v861_curve';END=1794052800.
runpy.run_path(str(R/'experiments/v858_nav2_verified_entry/native_entry.py'),run_name='qualified_cwd_only')
from vehicle import Vehicle
from instrumentation import dump
def reference(x,y,a,v,w,dt):
 if abs(w)<1e-12:return x+v*dt*math.cos(a),y+v*dt*math.sin(a),a
 return x+v/w*(math.sin(a+w*dt)-math.sin(a)),y-v/w*(math.cos(a+w*dt)-math.cos(a)),a+w*dt
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('CURVE_ABSOLUTE_DEADLINE')));signal.setitimer(signal.ITIMER_REAL,max(.01,END-5-time.time()));v=None;result=dict(passed=False,actual_native=None,replay_native=0,private_native=0);status='ENTRY';expected=[]
 try:
  os.chdir(R);v=Vehicle(O/'physics','WEST_EAST',10010001,False);x,y,a,_,_=v.body();start=time.monotonic();maxlag=0.;status='RUNNING'
  for i in range(1600):
   assert time.time()<END-15,'ROOT_DEADLINE';speed,yaw=(0.,0.)if i<200 or i>=1400 else(.15,0.)if i<600 else(.15,.05)if i<1000 else(.15,-.05)
   target=start+i*.01;time.sleep(max(0.,target-time.monotonic()));maxlag=max(maxlag,time.monotonic()-target);assert maxlag<=.1,'WALL_LAG';v.step(speed,yaw);x,y,a=reference(x,y,a,speed,yaw,.01);expected.append([x,y,a])
  summary=v.finish();replay=v.replay();q=np.asarray([r['qpos']for r in v.rows]);angle=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));ref=np.asarray(expected);err=np.linalg.norm(q[:,:2]-ref[:,:2],axis=1);ae=abs((angle-ref[:,2]+np.pi)%(2*np.pi)-np.pi);progress=float(q[-1,0]-q[0,0]);checks=dict(position_maximum=float(err.max())<=.15,position_rms=float(np.sqrt(np.mean(err**2)))<=.10,heading_maximum=float(ae.max())<=.15,progress=progress>=1.5,actual_stopped=summary['final_translation_speed_m_s']<=.03,full_replay=replay['passed'],bad_contacts=summary['bad_contacts']==0)
  np.savez_compressed(O/'REFERENCE.npz',pose=ref);result.update(summary,replay=replay,replay_native=replay['replay_native'],checks=checks,maximum_position_error_m=float(err.max()),rms_position_error_m=float(np.sqrt(np.mean(err**2))),maximum_heading_error_rad=float(ae.max()),along_axis_progress_m=progress,maximum_wall_lag_s=maxlag,passed=all(checks.values()));status='CURVE_COMPLETE'
 except BaseException as e:
  status='CURVE_EXCEPTION';result.update(error=repr(e),traceback=traceback.format_exc())
  if v:result.update(v.finish())
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);result.update(status=status,closed=True);dump(O/'RESULT.json',result);print(json.dumps(result),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
