"""Whole-path admission against the actual complete source fixture and mutants."""
import copy,importlib.abc,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1022_full_route_planner';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel())
from certificate import audit,binding
p=json.loads((R/'runs/v858_nav2_verified/v1020/PREFLIGHTS/ns/PREFLIGHT.json').read_text());setup=json.loads((R/'runs/v858_nav2_verified/v1020/PREFLIGHTS/ns/SETUP.json').read_text())
packet=dict(body=p['body'],native_tick=0,sim_time=0.,body_measured_at=0.,dynamic_discovered=False,steering=dict(position=p['steering'][:2],velocity=p['steering'][2:],native_tick=0,measured_at=0.),controller_memory=dict(last_ctrl=[0.]*4,integral=0.))
plan=json.loads((O/'ns_initial.input_route.json').read_text());goal=plan['original_goal'];plan['snapshot_binding_sha256']=binding(packet,None,setup,goal,plan['certificate_scope'])
# Add the newly introduced binding to this unfrozen preparation fixture.
(O/'ns_initial.input_route.json').write_text(json.dumps(plan,indent=2)+'\n')
positive=audit(plan,packet,None,setup,goal);assert positive['passed'],positive
rows=[]
def reject(name,mutate,packet_change=None,setup_change=None):
 q=copy.deepcopy(plan);p=copy.deepcopy(packet);s=copy.deepcopy(setup);mutate(q)
 if packet_change:packet_change(p)
 if setup_change:setup_change(s)
 result=audit(q,p,None,s,goal);rows.append(dict(name=name,passed=not result['passed'],rejection=result.get('error')or[k for k,v in result['checks'].items()if not v]))
 assert not result['passed'],name
reject('safe_prefix_instead_of_complete_route',lambda q:q.update(state_path=q['state_path'][:2001],path=q['path'][:2001],planned_body_requests=q['planned_body_requests'][:2000],predicted_actuator_controls=q['predicted_actuator_controls'][:2000]))
reject('all_200_stop_inputs_removed',lambda q:q.update(state_path=q['state_path'][:-200],path=q['path'][:-200],planned_body_requests=q['planned_body_requests'][:-200],predicted_actuator_controls=q['predicted_actuator_controls'][:-200]))
reject('middle_state_collision',lambda q:q['state_path'][1000].__setitem__(0,5.))
reject('middle_request_changed',lambda q:q['planned_body_requests'][1000].__setitem__(1,.03))
reject('illegal_middle_control',lambda q:q['predicted_actuator_controls'][1000].__setitem__(0,1.))
reject('goal_changed_to_current_point',lambda q:q.update(original_goal=p['body'][:2]))
reject('goal_upper_fabricated',lambda q:q.update(terminal_goal_distance_upper_m=.1))
reject('clearance_fabricated',lambda q:q.update(minimum_raw_full_cycle_clearance_m=1.))
reject('margin_reduced',lambda q:q.update(required_raw_clearance_m=.155))
reject('physical_authority_claimed',lambda q:q.update(physical_ready=True,actuation_authority=True))
reject('static_certificate_after_discovery',lambda q:None,lambda p:p.update(dynamic_discovered=True))
reject('different_causal_setup',lambda q:None,setup_change=lambda s:s['known']['known_circles'].append([0.,0.,1.]))
reject('truncated_edges_relabelled_complete',lambda q:q.update(edge_targets=q['edge_targets'][:5]))
reject('nonfinite_mid_profile',lambda q:q['state_path'][1000].__setitem__(1,float('nan')))
result=dict(passed=positive['passed']and all(x['passed']for x in rows),positive=positive,negative_cases=rows,models=0,integrations=0,physical_ready=False)
(O/'CERTIFICATE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],negative_cases=len(rows),positive=positive),ensure_ascii=False))
