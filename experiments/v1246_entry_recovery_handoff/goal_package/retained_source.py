"""Route-independent current-state full-goal source; no WE refuge coordinates."""
from pathlib import Path
import time
from .candidate_search import q,np,search,PreviewGeometry
from .admission import preview as feedback_preview
from .fallback_search import search as fallback_search

def generate(x,table,origin,offset,deadline,checkpoint=lambda _:None,*,onward_only=False,shadow_origin=None):
 assert x['setup']['case']['id']=='NORTH_SOUTH','NS_SOURCE_ROUTE_REQUIRED'
 assert shadow_origin is not None,'CONTINUOUS_SHADOW_REQUIRED'
 work=0
 def admit(candidate):
  nonlocal work
  result,_=feedback_preview(x,table,origin,shadow_origin,offset,candidate,deadline);work+=result['python_native']
  if result['passed']:
   reserve=min(result['feedback_proof']['minimum_raw_m'],result['continuous_shadow_proof']['minimum_raw_m'])-q.REQUIRED
   result['nominal_execution_reserve_m']=reserve;result['required_nominal_reserve_m']=.022
   result['passed']=bool(reserve>=.022)
   if not result['passed']:result['reason']='NOMINAL_EXECUTION_RESERVE'
  return result
 baseline=search(x,table,min(deadline,time.monotonic()+120),checkpoint,preview=dict(origin=origin,native_offset=offset,shadow_origin=shadow_origin),admit=admit,expansion_limit=3000)
 trials=[{k:baseline[k]for k in ['passed','phase_expanded','nodes','terminal_attempts','analytical_cpp_native','wall_s']}]
 result=baseline
 if not baseline['passed']:
  assert sum(baseline['phase_expanded'])==3000,'BASELINE_DID_NOT_EXHAUST_FIXED_WORK_NO_FALLBACK'
  assert time.monotonic()<deadline,'FALLBACK_DEADLINE_EXHAUSTED'
  result=fallback_search(x,table,min(deadline,time.monotonic()+120),checkpoint,preview=dict(origin=origin,native_offset=offset,shadow_origin=shadow_origin),admit=admit,expansion_limit=3000)
  trials.append({k:result[k]for k in ['passed','phase_expanded','nodes','terminal_attempts','analytical_cpp_native','wall_s']})
  result['baseline_exhaustion']=baseline
  result['analytical_cpp_native']+=baseline['analytical_cpp_native']
 result['search_trials']=trials
 result['bounded_total_expansions']=sum(sum(t['phase_expanded'])for t in trials)
 result['retained_balanced_search_first']=True
 result['maximum_total_expansions']=6000
 result.update(prefix_rows=None,method='current_state_NS_retained_balanced_seeded_fallback',admission_python_native=work)
 return result
