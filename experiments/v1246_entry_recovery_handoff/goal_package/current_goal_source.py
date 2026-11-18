"""Certified short entry recovery, then unchanged22mm whole-goal planning."""
import copy,time
from .candidate_search import q,np,PreviewGeometry
from .old_source import generate as original
from .retained_source import generate as retained
from .reconnect import generate as reconnect
from .admission import preview,predictor_origin
from .connection import TURNS,endpoint

COMPONENT_EXTRA=.002
GOAL_EXTRA=.022
HANDOFF_EXTRA=.044

def entry_status(x,table,origin,shadow_origin,offset):
 geometry=PreviewGeometry(q.Geometry(x,table),offset)
 lower=min(float(min(a[0]for a in geometry.components(np.asarray(o['state'])[None,:3],np.array([0]))))for o in [origin,shadow_origin])
 return ('ORIGINAL_SAFETY_REFUSED'if lower<q.REQUIRED+COMPONENT_EXTRA else 'ENTRY_RECOVERY_REQUIRED'if lower<q.REQUIRED+GOAL_EXTRA else 'WHOLE_GOAL_READY'),lower

def whole_goal(x,table,origin,offset,deadline,checkpoint,shadow_origin):
 answer=retained(x,table,origin,offset,deadline,checkpoint,shadow_origin=shadow_origin)
 if answer['passed']:return answer
 assert answer['bounded_total_expansions']==6000 and len(answer['search_trials'])==2,'INCOMPLETE_ORIGINAL_WORK_NO_RECONNECTION'
 assert all(not t['passed']and sum(t['phase_expanded'])==3000 for t in answer['search_trials'])
 final=reconnect(x,table,origin,offset,min(deadline,time.monotonic()+120),checkpoint,shadow_origin=shadow_origin)
 final['retained_exhaustion']=answer;final['analytical_cpp_native']+=answer['analytical_cpp_native'];final['admission_python_native']+=answer['admission_python_native']
 return final

def stage_check(x,table,origin,shadow_origin,offset,candidate,deadline,prefix_native):
 record,arrays=preview(x,table,origin,shadow_origin,offset,candidate,deadline)
 if not record['passed']:return record
 geometry=PreviewGeometry(q.Geometry(x,table),offset);lower=[]
 for key in ['states','shadow']:
  a,b=geometry.components(arrays[key][:,:3],np.arange(len(arrays[key])))
  margin=np.minimum(a,b);lower.append(margin)
 threshold=np.full(len(lower[0]),q.REQUIRED+GOAL_EXTRA)
 threshold[:prefix_native+1]=q.REQUIRED+COMPONENT_EXTRA
 minimum_excess=min(float((v-threshold).min())for v in lower)
 record.update(passed=bool(minimum_excess>=-1e-10),prefix_native=prefix_native,
  stage_contract='certified_entry_recovery_then22mm_goal',short_recovery_extra_reserve_m=COMPONENT_EXTRA,
  onward_extra_reserve_m=GOAL_EXTRA,minimum_stage_margin_excess_m=minimum_excess,
  required_nominal_reserve_m=COMPONENT_EXTRA,
  nominal_execution_reserve_m=min(record['feedback_proof']['minimum_raw_m'],record['continuous_shadow_proof']['minimum_raw_m'])-q.REQUIRED)
 return record

def generate(x,table,origin,offset,deadline,checkpoint=lambda _:None,*,onward_only=False,shadow_origin=None):
 assert shadow_origin is not None
 status,lower=entry_status(x,table,origin,shadow_origin,offset)
 if status=='WHOLE_GOAL_READY':
  if offset==0 and not onward_only:
   return original(x,table,origin,offset,deadline,checkpoint,shadow_origin=shadow_origin)
  return whole_goal(x,table,origin,offset,deadline,checkpoint,shadow_origin)
 assert status=='ENTRY_RECOVERY_REQUIRED'and offset==0 and not onward_only,'ENTRY_RECOVERY_SCOPE_OR_ORIGINAL_SAFETY'
 geometry=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients'])
 trials=[];work=0;attempts=0
 # Fixed28 one-turn forward-plus-complete-stop proposals, never reverse.
 for count in [50,100,200,400]:
  for turn in TURNS:
   assert time.monotonic()<deadline,'ENTRY_RECOVERY_TOTAL_DEADLINE'
   prefix=[(float(turn),.12,count,0),(0.,0.,2200,0)]
   ss,uu,mm=engine.simulate(origin,prefix)
   sh,su,sm=engine.simulate(shadow_origin,prefix)
   local=copy.deepcopy(x);local['goal']=ss[-1,:2].tolist()
   proof=q.proof(geometry,local,ss,uu,q.requests_of(prefix),mm)
   shadowproof=q.proof(geometry,local,sh,uu,q.requests_of(prefix),mm)
   terminal_lower=min(float(geometry.cycle(a[-1:,:3])[0])for a in [ss,sh])
   trial=dict(turn=turn,moving_native=count,prefix_native=count+2200,proof=proof,shadow_proof=shadowproof,terminal_cycle=terminal_lower,passed=False);trials.append(trial)
   if not(proof['passed']and shadowproof['passed'])or min(proof['minimum_raw_m'],shadowproof['minimum_raw_m'])<q.REQUIRED+COMPONENT_EXTRA or terminal_lower<q.REQUIRED+HANDOFF_EXTRA:continue
   # First certify the closed-loop prefix, including its complete stop. The
   # extra preview stop is conservative qualification work, not a fake scan.
   pre=dict(rows=prefix,states=ss,controls=uu,memory=mm,proof=proof)
   admission,arrays=preview(local,table,origin,shadow_origin,0,pre,deadline);work+=admission['python_native'];trial['prefix_admission']=admission
   if not admission['passed']or min(admission['feedback_proof']['minimum_raw_m'],admission['continuous_shadow_proof']['minimum_raw_m'])<q.REQUIRED+COMPONENT_EXTRA:continue
   n=count+2200
   cycles=min(float(geometry.cycle(a[n:n+1,:3])[0])for a in [arrays['states'],arrays['shadow']])
   if cycles<q.REQUIRED+HANDOFF_EXTRA:continue
   attempts+=1
   if attempts>3:break
   onward_origin=endpoint(origin,ss,mm,True);onward_shadow=endpoint(shadow_origin,sh,sm,True)
   proposal=whole_goal(x,table,onward_origin,n,deadline,checkpoint,onward_shadow)
   work+=proposal['admission_python_native'];engine_work=proposal['analytical_cpp_native']
   trial['onward_passed']=proposal['passed'];trial['onward_cpp_native']=engine_work
   if not proposal['passed']:continue
   rows=prefix+proposal['rows'];full,control,memory=engine.simulate(origin,rows)
   proof=q.proof(geometry,x,full,control,q.requests_of(rows),memory)
   if not proof['passed']:continue
   candidate=dict(rows=rows,states=full,controls=control,memory=memory,proof=proof)
   record=stage_check(x,table,origin,shadow_origin,0,candidate,deadline,n);work+=record['python_native'];trial['full_admission']=record
   if not record['passed']:continue
   trial['passed']=True
   return dict(candidate,passed=True,prefix_rows=prefix,prefix_native=n,admission=record,
    method='current_state_NS_retained_balanced_seeded_fallback',entry_recovery_contract=record['stage_contract'],
    entry_status=status,entry_lower_m=lower,recovery_trials=trials,
    planned_onward={k:v for k,v in proposal.items()if k not in ['states','controls','memory']},
    planned_handoff_extra_reserve_m=HANDOFF_EXTRA,
    analytical_cpp_native=engine.native+sum(t.get('onward_cpp_native',0)for t in trials),admission_python_native=work,
    models=0,physical_native=0,physical_eligible=False)
  if attempts>=3:break
 return dict(passed=False,prefix_rows=None,entry_status=status,entry_lower_m=lower,recovery_trials=trials,
  analytical_cpp_native=engine.native+sum(t.get('onward_cpp_native',0)for t in trials),admission_python_native=work,
  models=0,physical_native=0,physical_eligible=False)
