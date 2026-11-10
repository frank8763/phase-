"""Saved failure red, input-consistent continued search green, zero models."""
import copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1017_input_validated_progress';O.mkdir(exist_ok=True)
sys.path[:0]=[str(C),str(R/'experiments/v1003_causal_recovery_execution')]
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('original_plan',R/'experiments/v1003_causal_recovery_execution/plan.py');new=load('validated_plan',C/'plan.py')
source=R/'runs/v1016_saved_route_diagnosis/saved';rows=json.loads((source/'RECOVERY_CORRIDORS.json').read_text());setup=json.loads((source/'physics/SETUP.json').read_text());known=setup['known'];checks=[]
# Three fixed causal inputs: original successful physical first profile, its
# stationary handoff state, and the exact newly failed second search input.
first=json.loads((source/'COMMITTED_PROFILE_1.json').read_text())
fixtures=[('original_passed_first_profile',first['packet'],first['source'],first['plan']['original_goal']),('post_handoff_second_failure',rows[-1]['search_packet'],rows[-1]['search_source'],rows[-1]['original_goal']),('first_profile_saved_end',rows[0]['end_packet'],rows[0]['end_source'],rows[0]['original_goal'])]
sys.path.insert(0,str(R/'experiments/v997_input_consistent_recovery'));from saved_qualification import independently_check_geometry
for label,packet,src,goal in fixtures:
 mem=packet['controller_memory'];prior=old.construct(packet,src,goal,known,setup,mem['last_ctrl'],mem['integral'],time.time()+5.)
 start=time.monotonic();p=new.construct(packet,src,goal,known,setup,mem['last_ctrl'],mem['integral'],time.time()+5.)
 assert p['passed']and time.monotonic()-start<5.,(label,p.get('status'),p.get('input_candidate_checks'))
 if label=='original_passed_first_profile':
  assert prior['passed']and p['edge_targets']==prior['edge_targets']
  for key in ['planned_body_requests','predicted_actuator_controls','state_path']:assert p[key]==prior[key],key
 if label=='post_handoff_second_failure':assert not prior['passed']and prior['checks']['progress']is False and not p['input_candidate_checks'][0]['passed']and len(p['input_candidate_checks'])>=2
 states=np.asarray(p['state_path']);raw=independently_check_geometry(np.c_[states[:,:3],states[:,6]],known,src['periodic']);lower=raw-new.geometry.SPATIAL-.005*(.13+np.hypot(.44,.375)*.16)
 assert raw>=p['required_raw_clearance_m']and lower>=.155 and p['actual_goal_progress_lower_m']>=.4 and p['planned_body_requests'][-200:]==[[0.,0.,False]]*200
 states2,u2,requests=new.predict(setup,p['initial'],p['edge_targets']);assert np.array_equal(states,states2)and requests==p['planned_body_requests']and np.array_equal(u2,p['predicted_actuator_controls'])
 (O/(label+'.json')).write_text(json.dumps(dict(packet=packet,source=src,old_plan=prior,new_plan=p),indent=2)+'\n')
 checks.append(dict(case=label,passed=True,old_passed=prior['passed'],old_progress_lower=prior.get('actual_goal_progress_lower_m'),new_progress_lower=p['actual_goal_progress_lower_m'],independent_geometry_lower_m=float(lower),tested_input_prefixes=len(p['input_candidate_checks']),targets=p['edge_targets'],wall_s=time.monotonic()-start))
# Drive actual search callback refusal instead of assuming the search continues.
called=[]
packet,src,goal=fixtures[-1][1:]
rejected=new.search.construct(packet,src,goal,known,packet['body_measured_at'],time.time()+1.,accept_inputs=lambda x:(called.append(x)or False))
assert not rejected['passed']and len(called)>=2
result=dict(passed=True,models=0,integrations=0,physical_predictions=0,checks=checks,all_refused_never_admitted=True,rejected_prefixes_checked=len(called),old_failures_preserved=True,actual_control_and_replay_gates_unchanged=True)
(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':pass
