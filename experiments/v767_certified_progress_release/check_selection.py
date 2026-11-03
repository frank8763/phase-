import copy,json,math,sys
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));sys.path.insert(1,str(repo/'experiments/v768_certified_progress_release_audit'))
from selection import initial_state,select
from independent_selection import audit_initial,audit_select
read=lambda p:json.loads(p.read_text());old=read(repo/'runs/v764_observation_progress_cycle/FEEDBACK_MAIN_SUMMARY.json')['decisions'];arr=np.load(repo/'runs/v764_observation_progress_cycle/FEEDBACK_MAIN_ACTUAL.npz');base=np.load(repo/'runs/v764_observation_progress_cycle/ORIGINAL_256_NATIVE_REPLAY.npz')['qpos'][-1]
def yaw(q):return float(np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2)))
s=initial_state();checks=0
for d in old[:16]:
 k=d['local_public'];q=base if k==0 else arr['qpos'][k*8-1];x=select(d['candidates'],k,yaw(q),d['unknown_hold_m'],s);z=audit_select(d['candidates'],k,yaw(q),d['unknown_hold_m'],s);assert x==z and x[0]==d['selected_index']and x[1]==d['selector_after']and x[2]==d['selection_evidence'];s=x[1];checks+=1
# At the first observed alternative, the physical sweep and original safe action truly existed.
d=old[16];assert d['local_public']==64;q=arr['qpos'][64*8-1];x=select(d['candidates'],64,yaw(q),d['unknown_hold_m'],s);assert x==audit_select(d['candidates'],64,yaw(q),d['unknown_hold_m'],s)and x[1]['mode']=='PROGRESS'and x[0]is not None
assert d['candidates'][x[0]]['admissible']and d['candidates'][x[0]]['goal_progress_m']>=.05
# Original safety false cannot be made admissible by selector or observation state.
cs=d['candidates'];none=copy.deepcopy(cs)
for c in none:c['admissible']=False
for index in range(15):
 variants=[none,copy.deepcopy(none)];variants[1][index]['admissible']=True
 for c in variants:
  for heading in [-3.14,0.,3.14]:
   for hold in [.1,.45,.55,.8]:
    before=copy.deepcopy((c,s));u=select(c,64,heading,hold,s);v=audit_select(c,64,heading,hold,s);assert u==v and (c,s)==before
    if u[0]is not None:assert c[u[0]]['admissible']
    checks+=1
# Immediate post-release retains commitment even if the scalar trigger remains low.
u=select(cs,68,yaw(q),.1,x[1]);assert u[1]['mode']=='PROGRESS'
root=repo/'runs/v767_selection_prelaunch';root.mkdir(exist_ok=False);(root/'RESULT.json').write_text(json.dumps(dict(status='INDEPENDENT_PROGRESS_RELEASE_AND_EXACT64_PREFIX_VERIFIED',comparisons=checks,first_registered_release_public=64,all_states_saved_or_synthetic=True,new_initializations=0,new_integrations=0),indent=2)+'\n');print(checks)
