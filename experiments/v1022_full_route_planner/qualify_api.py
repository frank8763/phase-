"""Actual public planner API, complete output and rejected changed metadata."""
import copy,importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1022_full_route_planner';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from planner import construct
p=json.loads((R/'runs/v858_nav2_verified/v1020/PREFLIGHTS/ns/PREFLIGHT.json').read_text());setup=json.loads((R/'runs/v858_nav2_verified/v1020/PREFLIGHTS/ns/SETUP.json').read_text())
packet=dict(body=p['body'],native_tick=0,sim_time=0.,body_measured_at=0.,dynamic_discovered=False,steering=dict(position=p['steering'][:2],velocity=p['steering'][2:],native_tick=0,measured_at=0.),controller_memory=dict(last_ctrl=[0.]*4,integral=0.))
old=json.loads((O/'ns_initial.input_route.json').read_text());goal=old['original_goal'];t=time.monotonic();result=construct(packet,None,goal,setup['known'],setup,[0.]*4,0.,time.time()+30.)
assert result['passed'] and result['edge_targets']==old['edge_targets'] and result['state_path']==old['state_path'] and result['planned_body_requests']==old['planned_body_requests']
rows=[]
for name in ['changed_memory','discovered_without_forecast','nonfinite_state','incoherent_encoders','expired_deadline']:
 q=copy.deepcopy(packet);last=[0.]*4;end=time.time()+2.
 if name=='changed_memory':last[0]=.1
 if name=='discovered_without_forecast':q['dynamic_discovered']=True
 if name=='nonfinite_state':q['body'][0]=float('nan')
 if name=='incoherent_encoders':q['steering']['native_tick']=1
 if name=='expired_deadline':end=time.time()-1
 try:construct(q,None,goal,setup['known'],setup,last,0.,end)
 except AssertionError as e:rows.append(dict(name=name,passed=True,reason=str(e)))
 else:raise AssertionError('MUTANT_ACCEPTED '+name)
from whole_input import public_setup
poisoned=dict(setup,actor=object(),case=object(),seed=object())
assert public_setup(poisoned)==public_setup(setup)
from certificate import binding
assert binding(packet,None,poisoned,goal,'pre_detection_static')==binding(packet,None,setup,goal,'pre_detection_static')
report=dict(unused_truth_metadata_not_accessed=True,passed=True,actual_public_api=True,same_complete_result_and_input_schedule=True,full_reconstruction_passed=result['full_input_admission']['passed'],negative_cases=rows,
 models=0,integrations=0,physical_ready=False,wall_s=time.monotonic()-t)
(O/'API_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
