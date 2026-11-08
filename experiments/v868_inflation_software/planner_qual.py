"""Replay saved odometry/ranges to genuine Nav2. No plant/model or actuator calls."""
import gzip,hashlib,json,math,os,signal,socket,subprocess,sys,time,traceback
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v868_inflation_software'/sys.argv[1]
class NoModels:
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0]in {'mujoco','torch','vehicle','factory'}:raise RuntimeError('NO_VEHICLE_IMPORT')
sys.meta_path.insert(0,NoModels())
def main():
 assert not O.exists();O.mkdir(parents=True);source=R/'runs/v858_nav2_verified/v867/static_main_1';a=np.load(source/'physics/NATIVE_TRACE.npz');scans=json.loads(gzip.decompress((source/'physics/SENSORS.json.gz').read_bytes()));setup=json.loads((source/'physics/SETUP.json').read_text());task=json.loads((source/'TASK.json').read_text());task.update(run_id='v868-stationary-we-'+sys.argv[1],scope='RECORDED_STATE_SENSOR_PLAYBACK_NO_VEHICLE',output=str(O),socket_dir=str(O.relative_to(R)),wall_limit_s=55)
 task['nav2_params']=str(C/'nav2_params.yaml')if sys.argv[1]=='candidate01'else str(C/'baseline_params.yaml')
 now=time.time();auth=dict(software_playback_only=True,models_authorized=False,source_freeze_sha256=hashlib.sha256((C/'SOURCE_FREEZE.json').read_bytes()).hexdigest(),run_id=task['run_id'],started_unix=now,deadline_unix=min(now+70,json.loads((R/"runs/v868_inflation_software/SOFTWARE_WINDOW.json").read_text())["deadline_unix"]));(O/'TASK.json').write_text(json.dumps(task,indent=2)+'\n');(O/'AUTHORIZATION.json').write_text(json.dumps(auth,indent=2)+'\n')
 sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=O/'physics.sock';os.chdir(R);sock.bind(str(address.relative_to(R)));sock.setblocking(False);armed=None;stopped=False;commands=0;max_tick=0;p=None
 sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'));from ros_environment import command,environment
 try:
  with(O/'ros.console').open('w')as log:
   p=subprocess.Popen(command(['/usr/bin/python3.12',str(C/'planner_bridge.py'),str(O/'TASK.json'),str(O/'AUTHORIZATION.json')]),cwd=R,env=environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   while p.poll()is None and time.time()<auth['deadline_unix']-5:
    mono=time.monotonic()
    for _ in range(128):
     try:q=json.loads(sock.recv(65536))
     except BlockingIOError:break
     assert q['run_id']==task['run_id']
     if q['kind']=='arm'and armed is None:armed=mono
     elif q['kind']=='command':commands+=1
     elif q['kind']=='stop':stopped=True
    if stopped:
     time.sleep(.01);continue
    tick=0 # stationary actual saved t0 observation; all generated commands discarded
    max_tick=max(max_tick,tick)
    if tick:
     pos=a['qpos'][tick-1];vel=a['qvel'][tick-1];yaw=math.atan2(2*(pos[3]*pos[6]+pos[4]*pos[5]),1-2*(pos[5]**2+pos[6]**2));body=[*pos[:2],yaw,vel[0]*math.cos(yaw)+vel[1]*math.sin(yaw),vel[5]]
    else:body=[*setup['case']['start_xy'],setup['case']['yaw'],0.,0.]
    s=scans[min(tick//5,len(scans)-1)];packet=dict(kind='observation',run_id=task['run_id'],phase='WAITING'if armed is None else'RUNNING',native_tick=tick,sim_time=tick*.01,sent_at=mono,body_measured_at=mono,scan_measured_at=mono,initial_snapshot=armed is None,body=body,scan={k:s[k]for k in ['native_tick','time','ranges']},source='frozen recorded physical odometry and range playback; no new model')
    try:sock.sendto(json.dumps(packet).encode(),str(O.relative_to(R)/'ros.sock'))
    except (FileNotFoundError,ConnectionRefusedError,BlockingIOError):pass
    time.sleep(.005)
   if p.poll()is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
 finally:
  if p and p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
  sock.close();address.unlink(missing_ok=True)
  result=dict(closed=True,software_playback=True,model_initializations=0,model_integrations=0,actuator_execution=0,ros_returncode=None if p is None else p.returncode,recorded_ticks_served=max_tick,software_commands_not_executed=commands,stop_received=stopped,actual_closed_loop_navigation=False);(O/'PLAYBACK_COMPLETION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
