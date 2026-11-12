"""Refresh a finite static corridor and certify its nominal braking prefixes."""
import numpy as np
from kernel import initial,predict,checks,ref,REQUIRED
from planner import construct
from brake_reserve import Reserve
from recovery_source import forecast_packet
from fresh import actions_from_requests

def renew(setup,packet,goal,wall_s=10.,max_expansions=20000):
 candidate=construct(setup,packet,None,goal,wall_s,max_expansions)
 if not candidate['passed']:return candidate
 rr=np.array(candidate['planned_body_requests']);actions=candidate['actions'];ss,uu,requests,mm=predict(setup,packet,actions,tail=False);reserve=Reserve(setup,use_wide_reserve=False);safe=None;proofs=[];stopped_early=False
 for i in range(0,len(rr),5):
  p=forecast_packet(packet,ss[i],mm[i],i);proof=reserve.check(p,rr[i:i+5]);proofs.append(dict(native=i,**proof))
  if proof['current_stop_minimum_raw_m']>=REQUIRED+.02 and i>=400:safe=i
  if not proof['passed']:
   stopped_early=True;break
 if stopped_early:
  if safe is None:return dict(passed=False,status='NO_NOMINAL_BRAKE_COMPATIBLE_STATIC_PREFIX',models=0,integrations=0,original_candidate_status=candidate['status'])
  rr=np.vstack([rr[:safe],np.zeros((2200,3))]);actions=actions_from_requests(rr);ss,uu,rr,mm=predict(setup,packet,actions,tail=False)
 minimum=float(ref._old.Geometry(setup['known'],None).clearances(ss[:,:3])[0].min());cc,upper=checks(ss,uu,rr,packet,setup,np.asarray(goal),minimum,REQUIRED);goal_source=bool(cc['goal_upper']);safety=dict(cc);safety.pop('goal_upper');assert all(safety.values()),'STATIC_REFRESH_FULL_PROFILE_REJECTED'
 return dict(passed=True,status='COMPLETE_STATIC_GOAL'if goal_source else'FINITE_STATIC_RECOVERY_NOT_ARRIVAL',functional_goal_source=goal_source,finite_progress_never_counts_as_arrival=not goal_source,packet=packet,source=None,actions=actions,state_path=ss.tolist(),predicted_actuator_controls=uu.tolist(),planned_body_requests=rr.tolist(),minimum_raw_m=minimum,checks=safety,original_goal_profile_checks=cc,terminal_goal_upper_m=upper,nominal_brake_preview_checks=proofs,truncated_to_certified_complete_stop=stopped_early,original_candidate_status=candidate['status'],models=0,integrations=0)
