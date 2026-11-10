"""Saved input replay and terminal state cases, zero models and no ROS server."""
import copy,importlib.abc,importlib.util,json,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1019_terminal_progress_recovery';O.mkdir(exist_ok=True)
sys.path[:0]=[str(C),str(R/'experiments/v1018_input_progress_night'),str(R/'experiments/v1003_causal_recovery_execution')]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','rclpy','physical','vehicle'}:raise AssertionError('NO_MODEL_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModel())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
plan=load('terminal_plan',C/'plan.py');prior=load('progress_only_plan',R/'experiments/v1017_input_validated_progress/plan.py');supervisor=load('terminal_supervisor',C/'supervise.py');owner=load('terminal_owner',C/'profile_owner.py')
source=R/'runs/v1016_saved_route_diagnosis/saved';rows=json.loads((source/'RECOVERY_CORRIDORS.json').read_text());setup=json.loads((source/'physics/SETUP.json').read_text());known=setup['known'];cases=[]
for label,row in [('original_profile',json.loads((source/'COMMITTED_PROFILE_1.json').read_text())),('last_failed_input',dict(packet=rows[-1]['search_packet'],source=rows[-1]['search_source'],plan=dict(original_goal=rows[-1]['original_goal'])))]:
 p,s,g=row['packet'],row['source'],row['plan']['original_goal'];memory=p['controller_memory']
 a=prior.construct(p,s,g,known,setup,memory['last_ctrl'],memory['integral'],time.time()+5.);b=plan.construct(p,s,g,known,setup,memory['last_ctrl'],memory['integral'],time.time()+5.)
 assert a['passed']and b['passed']and all(a[k]==b[k]for k in ['edge_targets','state_path','planned_body_requests','predicted_actuator_controls'])
 assert not b['goal_capture'];cases.append(dict(case=label,passed=True,progress_branch_exact=True))
p=copy.deepcopy(rows[0]['end_packet']);s=copy.deepcopy(rows[0]['end_source']);memory=p['controller_memory'];body=np.asarray(p['body']);goal=(body[:2]+.46*np.array([np.cos(body[2]),np.sin(body[2])])).tolist()
a=prior.construct(p,s,goal,known,setup,memory['last_ctrl'],memory['integral'],time.time()+5.);b=plan.construct(p,s,goal,known,setup,memory['last_ctrl'],memory['integral'],time.time()+5.)
assert not a['passed']and b['passed']and b['goal_capture']and b['actual_goal_progress_lower_m']<.4 and b['terminal_goal_distance_upper_m']<=.45
assert owner.valid_capture(b,np.asarray(b['state_path']))
from saved_qualification import independently_check_geometry
states=np.asarray(b['state_path']);raw=independently_check_geometry(np.c_[states[:,:3],states[:,6]],known,s['periodic']);assert raw>=b['required_raw_clearance_m']
for label,change in [('bad_upper',lambda x:x.update(terminal_goal_distance_upper_m=.5)),('wrong_goal',lambda x:x.update(original_goal=[100.,100.])),('missing_capture',lambda x:x.update(goal_capture=False))]:
 bad=copy.deepcopy(b);change(bad);assert not owner.valid_capture(bad,states);cases.append(dict(case=label,rejected=True))
(O/'TERMINAL_CAPTURE_PLAN.json').write_text(json.dumps(dict(packet=p,source=s,goal=goal,plan=b),indent=2)+'\n')
cases.append(dict(case='near_goal_capture',passed=True,goal_distance_before_m=.46,goal_upper_m=b['terminal_goal_distance_upper_m'],progress_lower_m=b['actual_goal_progress_lower_m'],unchanged_progress_threshold_for_nonterminal=.4,independent_raw_clearance_m=raw))
assert supervisor.terminal_event(6,p,s)['goal_unchanged']
for label,status,ps,ss in [('success_not_abort',4,p,s),('external_cancel',5,p,s),('no_causal_forecast',6,p,dict(s,periodic=None)),('future_observation',6,p,dict(s,source_native_tick=p['native_tick']+1))]:
 try:supervisor.terminal_event(status,ps,ss)
 except AssertionError:cases.append(dict(case=label,rejected=True))
 else:raise AssertionError('INVALID_TERMINAL_ACCEPTED '+label)
result=dict(passed=True,models=0,integrations=0,cases=cases,goal_unit_fixture_not_new_physical_task=True,original_failed_180s_tasks_not_upgraded=True)
(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
