"""No model creation: compare independent implementations and transition boundaries."""
import copy,hashlib,json,math,sys
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(own));sys.path.insert(1,str(repo/'experiments/v763_observation_commitment_audit'))
from selection import initial_state,select
from independent_selection import audit_initial,audit_select
read=lambda p:json.loads(p.read_text());cs=read(repo/'runs/v759_state_feedback_execution/FEEDBACK_MAIN_SUMMARY.json')['decisions'][0]['candidates'];assert initial_state()==audit_initial()
checked=0
def compare(c,t,y,h,s):
 global checked
 before=copy.deepcopy((c,s));x=select(c,t,y,h,s);z=audit_select(c,t,y,h,s);assert x==z and (c,s)==before
 if x[0]is not None:assert c[x[0]]['admissible']
 checked+=1;return x
# Commitment cannot be broken by a more rewarding but still-safe competitor.
i,s,e=compare(cs,0,0.,.8,initial_state());other=copy.deepcopy(cs);other[0]['goal_progress_m']=100.;j,_,e=compare(other,4,0.,.8,s);assert i==j and e['reason']=='PROGRESS_COMMITMENT'
j,_,e=compare(other,12,0.,.8,s);assert j==0 and e['reason']=='PROGRESS_RESELECT'
# Hysteresis boundaries, actual heading needed, forbidden targets never fabricated.
i,s,e=compare(cs,4,0.,.45,s);assert s['mode']=='OBSERVE'
for h in [.549999,.55,.550001]:
 j,ss,e=compare(cs,8,math.pi/16,h,s);assert (ss['mode']=='PROGRESS')==(h>=.55)
j,ss,e=compare(cs,8,math.pi/16-1e-6,.9,s);assert ss['mode']=='OBSERVE'
none=copy.deepcopy(cs)
for c in none:c['admissible']=False
assert compare(none,12,.3,.2,s)[0]is None
# Exercise each fixed action as the only admissible one, including no-scan fallback.
for index in range(15):
 subset=copy.deepcopy(none);subset[index]['admissible']=True
 for h in [.44,.46,.56]:
  assert compare(subset,12,.1,h,s)[0]==index
# Changing unrelated evaluator-only fields cannot affect decision.
aug=copy.deepcopy(cs)
for c in aug:c['evaluator_hidden_actor_xy']=[999.,999.]
assert select(cs,16,.15,.43,s)==select(aug,16,.15,.43,s)
# Every saved candidate set, fixed causal-like scalar boundary input, deterministic repeated call.
old=read(repo/'runs/v759_state_feedback_execution/FEEDBACK_MAIN_SUMMARY.json')['decisions'];ss=initial_state()
for d in old:
 index,ss,e=compare(d['candidates'],d['local_public'],.01*d['local_public'],.8-.012*d['local_public'],ss)
out=repo/'runs/v762_selection_prelaunch';out.mkdir(exist_ok=False);(out/'RESULT.json').write_text(json.dumps(dict(status='INDEPENDENT_SELECTOR_TRANSITIONS_AND_CAUSAL_INPUTS_PASS',comparisons=checked,new_initializations=0,new_integrations=0,synthetic_states_not_physical_evidence=True),indent=2)+'\n');print(checked)
