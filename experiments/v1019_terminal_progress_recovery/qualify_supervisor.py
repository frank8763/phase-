"""Production supervisor ABORT->full capture->same-goal success; metadata peer only."""
import copy,hashlib,importlib.util,json,sys,tempfile,time,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1019_terminal_progress_recovery'
sys.path[:0]=[str(C),str(R/'experiments/v1018_input_progress_night'),str(R/'experiments/v1003_causal_recovery_execution')]
s=importlib.util.spec_from_file_location('production_terminal_supervisor',C/'supervise.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
from steering_continuity import SteeringContinuity
fixture=json.loads((O/'TERMINAL_CAPTURE_PLAN.json').read_text());saved=R/'runs/v1016_saved_route_diagnosis/saved';setup=json.loads((saved/'physics/SETUP.json').read_text());events=[]
class Future:
 def __init__(self,result):self.value=result
 def done(self):return True
 def result(self):return self.value
class Handle:
 accepted=True
 def __init__(self,status):self.status=status
 def get_result_async(self):return Future(types.SimpleNamespace(status=self.status))
 def cancel_goal_async(self):raise AssertionError('ALREADY_ABORTED_ACTION_MUST_NOT_BE_CANCELLED_OR_REUSED')
with tempfile.TemporaryDirectory(prefix='supervisor-',dir=O)as td:
 out=Path(td);(out/'physics').mkdir();(out/'physics/SETUP.json').write_text(json.dumps(setup))
 packet=copy.deepcopy(fixture['packet']);source=copy.deepcopy(fixture['source']);goal=fixture['goal'];plan=fixture['plan'];statuses=[6,4];requested=[]
 def snapshot():
  now=time.monotonic();p=copy.deepcopy(packet);p['body_measured_at']=p['sent_at']=now;p['steering']['measured_at']=now;p['steering']['native_tick']=p['native_tick'];src=copy.deepcopy(source);src.update(source_age_s=.001,decision_at=now);return p,src
 def issue(g):
  requested.append([g.pose.pose.position.x,g.pose.pose.position.y]);return Future(Handle(statuses.pop(0)))
 n=types.SimpleNamespace(motion=types.SimpleNamespace(out=out,decision_snapshot=snapshot),forward=types.SimpleNamespace(replan_requested=False,replan_count=0,resume=lambda goal:None),
  action=types.SimpleNamespace(send_goal_async=issue),get_clock=lambda:types.SimpleNamespace(now=lambda:types.SimpleNamespace(to_msg=lambda:None)),guard_failure=None,
  planner_proxy=types.SimpleNamespace(known=setup['known'],rows=[]),tube_decisions=[],profile_owner=False,steering_continuity=SteeringContinuity(),command_sequence=0,commands=[],retained_proof=None,last_nominal_at=None)
 n.latest=copy.deepcopy(packet)
 def send(msg):
  events.append(msg['kind'])
  if msg['kind']=='commit_profile':
   assert n.profile_owner
   raw=Path(msg['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==msg['sha256'];record=json.loads(raw);assert record['plan']==plan
   state=plan['state_path'][-1];packet['body']=[state[0],state[1],state[2],state[3],state[5]];packet['native_tick']+=len(plan['planned_body_requests']);packet['sim_time']+=len(plan['planned_body_requests'])*.01
   packet['steering']['position']=plan['predicted_actuator_controls'][-1][:2];packet['steering']['velocity']=[0.,0.]
   n.latest=dict(packet,profile_status=dict(active=False,profile_id=1,completed_id=1,released_id=None))
  if msg['kind']=='release_profile':
   assert n.profile_owner and msg['resume_command']['v']==msg['resume_command']['w']==0.
   n.latest['profile_status'].update(released_id=1,handoff_sequence=msg['resume_command']['sequence'])
 n.send=send
 initial=types.SimpleNamespace(pose=types.SimpleNamespace(pose=types.SimpleNamespace(position=types.SimpleNamespace(x=goal[0],y=goal[1])),header=types.SimpleNamespace(stamp=None)))
 original=m.planner.construct;m.planner.construct=lambda *args:copy.deepcopy(plan)
 def require(ok,why):
  if not ok:raise AssertionError(why)
 def wait(node,predicate,until,label):assert predicate(),label
 try:response,rows=m.supervise(n,initial,time.monotonic()+10,time.time()+30,lambda *args,**kwargs:None,wait,require,lambda:None)
 finally:m.planner.construct=original
 assert response.status==4 and len(rows)==1 and rows[0]['passed']and rows[0]['trigger']['kind']=='NAV2_ABORTED_CAUSAL_RECOVERY'
 assert rows[0]['actual_goal_progress_m']<.4 and rows[0]['atomic_handoff']['stop_ownership_until_ack']and requested==[goal,goal]
 assert events.count('commit_profile')==events.count('release_profile')==1 and n.profile_owner is False
 result=dict(passed=True,models=0,integrations=0,scope='Actual production supervisor with nonphysical immediate action/native metadata peers',
  aborted_action_not_cancelled_again=True,full_capture_plan_exact=True,real_zero_handoff_helper_executed=True,original_goal_reissued=True,success_status_only_after_same_goal_action_succeeds=True,
  no_synthetic_action_success=True,progress_below_point4_allowed_only_actual_goal_capture=True,rows=rows)
 (O/'SUPERVISOR_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
