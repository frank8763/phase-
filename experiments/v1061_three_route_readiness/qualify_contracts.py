"""A red-capable producer contract test: geometric pass is not goal pass."""
import sys,copy,importlib.abc,json,time
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from handoff import prepare,base,validate_actions
pin_threads();x=json.loads((O/'dependencies/WE_MEASURED_INPUT.json').read_text());packet=x['packet'];setup=x['setup'];source=x['source'];rows=[dict(kind='wait',gear=0,target=0.,speed=0.,ticks=200)];wrong=[packet['body'][0]+1.,packet['body'][1]]
legacy=load('v1061_frozen_old_generic_bug',R/'experiments/v1058_fresh_repeat_entry/handoff.py');old=legacy.prepare(setup,packet,source,wrong,rows,0);assert old['passed'],'EXPECTED_OLD_WRONG_GOAL_ACCEPTANCE';red=dict(old_geometric_producer_accepted_unreachable_goal=True,wrong_goal=wrong)
try:prepare(setup,packet,source,wrong,rows,0)
except AssertionError as e:assert str(e)=='COMPLETE_INPUT_ENDPOINT_OR_CONTROL_REJECTED';red['fixed_producer_rejects_same_goal']=True
else:raise AssertionError('WRONG_GOAL_STILL_ACCEPTED')
positive=prepare(setup,packet,source,packet['body'][:2],rows,0);assert positive['passed']and all(positive['complete_profile_checks'].values());negative=[]
for name,actions in [('unqualified_speed',[dict(kind='move',gear=1,target=0.,speed=.04,ticks=200)]),('gear_speed_disagreement',[dict(kind='move',gear=-1,target=0.,speed=.03,ticks=200)]),('unqualified_target',[dict(kind='move',gear=1,target=CAP+.01,ticks=200)]),('noninteger_duration',[dict(kind='wait',gear=0,target=0.,ticks=True)]),('empty',[]),('over_budget',[dict(kind='wait',gear=0,target=0.,ticks=40001)])]:
 try:validate_actions(actions)
 except AssertionError:negative.append(name)
 else:raise AssertionError('NEGATIVE_ACCEPTED '+name)
for name,actions in [('no_complete_stop',[dict(kind='move',gear=1,target=0.,speed=.03,ticks=200)]),('insufficient_stop',[dict(kind='move',gear=1,target=0.,speed=.03,ticks=200),dict(kind='wait',gear=0,target=0.,ticks=199)])]:
 try:prepare(setup,packet,source,packet['body'][:2],actions,0)
 except AssertionError:negative.append(name)
 else:raise AssertionError('NEGATIVE_ACCEPTED '+name)
result=dict(passed=True,red_capable=red,positive_parked_contract_passed=True,negative_cases=negative,models=0,integrations=0,does_not_qualify_any_route_functional_chain=True);dump(O/'CONTRACT_QUALIFICATION.json',result);print(json.dumps(result))
