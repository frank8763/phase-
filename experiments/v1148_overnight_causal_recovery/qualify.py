"""Actual entries, saved red/green, and exact primitive end-memory chaining."""
from primitives import *
import copy,ast
sys.path.insert(0,str(C))
import component_worker,component_audit,primitive_search,post_actual

def main():
 assert '--isolated'in sys.argv or sha(R/'REVIEW_PENDING')==GUARD_SHA
 saved=R/'runs/v1146_causal_certificate_refresh';setup=json.loads((R/'runs/v858_nav2_verified/v1144/observation_main/physics/SETUP.json').read_text());packets=[json.loads((saved/'ACTUAL_REFUSAL_PACKET.json').read_text()),json.loads((R/'runs/v1145_observer_failure_review/SAVED_STOP_PACKET.json').read_text())];expander=Expander(setup);engine=Engine(setup);cases=0;maximum=0.;python_native=0
 for packet in packets:
  origin=initial(packet);assert not origin['coupled_episode']and not origin['steering_motion_active'];state=np.asarray(origin['state']);memory=np.r_[origin['last_ctrl'],origin['integral']]
  for speed in [0.,.08,.12]:
   for steps in [1,8,100]:
    targets=np.array([-CAP,-.32,-.16,0.,.16,.32,CAP]);ss,uu,mem=expander.expand(state,memory,targets,speed,steps)
    for k,target in enumerate(targets):
     rows=[(float(target),speed,steps,0)];cs,cu=engine.simulate(origin,rows);ps,pu,pm,_,_=python_replay(setup,origin,rows);python_native+=steps;error=max(float(abs(ss[k]-cs[1:]).max()),float(abs(uu[k]-cu).max()),float(abs(ps-cs).max()),float(abs(pu-cu).max()),float(abs(pm[-1]-mem[k]).max()));maximum=max(maximum,error);assert error<=1e-8,'EXPANSION_OR_END_MEMORY_NOT_IDENTICAL';cases+=1
 # Chaining preserves integral and steering memory across distinct commands.
 origin=initial(packets[-1]);state=np.asarray(origin['state']);memory=np.r_[origin['last_ctrl'],origin['integral']];chain=[];states=[];controls=[]
 for target,speed,steps in [(-.32,.12,100),(.32,.12,100),(0.,0.,100)]:
  ss,uu,mem=expander.expand(state,memory,np.array([target]),speed,steps);state=ss[0,-1];memory=mem[0];states.extend(ss[0]);controls.extend(uu[0]);chain.append((target,speed,steps,0))
 cs,cu=engine.simulate(origin,chain);assert abs(np.asarray(states)-cs[1:]).max()<=1e-8 and abs(np.asarray(controls)-cu).max()<=1e-8
 # Genuine parent historical schedule and unchanged paired task inputs.
 journal=json.loads((component_worker.PARENT/'MODE_JOURNAL.json').read_text())
 for i in range(32515):component_worker.historical_mode(i,journal)
 tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==2 and all(not Path(t['output']).exists()for t in tasks);assert all(t['seed']==10010001 and t['phase']==.6573753567727383 for t in tasks)
 profiles=json.loads((C/'PROFILES.json').read_text());assert len(profiles)==8 and len({p['name']for p in profiles})==8 and all(p['speed']in [.08,.12]and p['edge_native']in [100,200]and p['wall_s']==3600 for p in profiles)
 bad=0
 for targets,speed,ticks in [(np.array([CAP+.01]),.12,100),(np.array([0.]),.13,100),(np.array([float('nan')]),.12,100),(np.array([0.]),.12,0)]:
  try:expander.expand(state,memory,targets,speed,ticks)
  except AssertionError:bad+=1
 assert bad==4
 q=json.loads((saved/'QUALIFICATION.json').read_text());assert q['passed']and q['old']['prospective']['passed']is False and q['refreshed']['prospective']['passed']is True
 for p in C.glob('*.py'):ast.parse(p.read_text())
 result=dict(passed=True,actual_worker_audit_and_search_imported=True,saved_red_green_preserved=True,primitive_cases=cases,primitive_state_ctrl_final_memory_max_error=maximum,chained_full_state_and_memory_match=True,invalid_requests_rejected=bad,fixed_physical_tasks=2,fixed_software_profiles=8,models=0,physical_native=0,analytical_expansion_native=expander.native,analytical_profile_native=engine.native,independent_python_native=python_native,isolated='--isolated'in sys.argv)
 dump(O/('ISOLATED_QUALIFICATION.json'if '--isolated'in sys.argv else'QUALIFICATION.json'),result);print(encode(result))

if __name__=='__main__':main()
