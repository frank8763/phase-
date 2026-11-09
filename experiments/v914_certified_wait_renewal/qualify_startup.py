"""Run actual installed bridge to pre-goal boundary with synthetic zero-model peer."""
import copy,hashlib,importlib.abc,json,socket,sys,threading,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v914_certified_wait_renewal'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','vehicle','physical','factory'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import ros_worker
engine=ros_worker.engine
out=R/'runs/v914_startup_fixture02';out.mkdir(exist_ok=False);(out/'physics').mkdir()
task=copy.deepcopy(json.loads((C/'TASKS.json').read_text())[0]);task.update(output=str(out),socket_dir=str(out.relative_to(R)),run_id='v914-zero-model-startup-fixture')
# Only test entry authority is substituted. No production authority or science changed.
engine.authorized=lambda *a:time.time()+90
original_check=engine.require_goal_allowed;boundary=[]
def stop_before_goal(*args):
 original_check(*args);boundary.append(dict(at=time.monotonic(),synthetic_packet=args[0]));raise RuntimeError('EXPECTED_ZERO_MODEL_PRE_GOAL_BOUNDARY')
engine.require_goal_allowed=stop_before_goal
peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=Path('runs/v914_startup_fixture02/physics.sock');peer.bind(str(address));peer.settimeout(.005);done=threading.Event();events=[]
def serve():
 phase='WAITING';begun=time.monotonic()
 while not done.is_set()and time.monotonic()-begun<60:
  try:
   message=json.loads(peer.recv(65536));events.append(message)
   if message['kind']=='arm':phase='RUNNING'
   if message['kind']=='stop':break
  except socket.timeout:pass
  now=time.monotonic();packet=dict(kind='observation',run_id=task['run_id'],phase=phase,native_tick=0,sim_time=0.,sent_at=now,body_measured_at=now,scan_measured_at=now,initial_snapshot=phase=='WAITING',body=[-4.,-2.,0.,0.,0.],scan=dict(native_tick=0,time=0.,xy=[-4.,-2.],yaw=0.,ranges=[3.]*32))
  try:peer.sendto(json.dumps(packet).encode(),str(Path(task['socket_dir'])/'ros.sock'))
  except FileNotFoundError:pass
thread=threading.Thread(target=serve);thread.start()
try:result=engine.run(task,{},hashlib.sha256((C/'SOURCE_FREEZE.json').read_bytes()).hexdigest())
finally:done.set();thread.join(2);peer.close();address.unlink(missing_ok=True)
checks=dict(reached_exact_pre_navigation_boundary=len(boundary)==1,expected_software_stop='EXPECTED_ZERO_MODEL_PRE_GOAL_BOUNDARY'in result.get('error',''),no_navigation_action=not result['navigation_action_sent'],two_real_master_readbacks=result.get('global_master_readiness',{}).get('passed')is True,all_real_lifecycle_nodes_active=all(v==3 for v in result.get('active_states',{}).values())and len(result.get('active_states',{}))==7,arm_exchange=sum(x['kind']=='arm'for x in events)==1,no_actuator_command=all(x['kind']!='command'for x in events),synthetic_peer_never_integrates=True)
proof=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,navigation_goals=0,synthetic_peer=True,scope='Actual installed ROS lifecycle, complete static map, preARM and ARM exchange through production bridge. Synthetic observation fixture only, not physical qualification.',events=events)
for name in ['FULL_STARTUP_QUALIFICATION.json','ROS_SOFTWARE_QUALIFICATION.json']:(O/name).write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof));assert proof['passed']
