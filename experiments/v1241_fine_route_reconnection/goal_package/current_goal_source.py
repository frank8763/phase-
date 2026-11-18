"""Keep original successes; reconnect whole action routes only after exhaustion."""
import time
from .candidate_search import q,np,PreviewGeometry
from .retained_source import generate as retained
from .reconnect import generate as reconnect

def generate(x,table,origin,offset,deadline,checkpoint=lambda _:None,*,onward_only=False,shadow_origin=None):
 baseline=retained(x,table,origin,offset,deadline,checkpoint,onward_only=onward_only,shadow_origin=shadow_origin)
 if baseline['passed']:return baseline
 assert baseline['bounded_total_expansions']==6000 and len(baseline['search_trials'])==2,'INCOMPLETE_ORIGINAL_WORK_NO_RECONNECTION'
 assert all(not t['passed']and sum(t['phase_expanded'])==3000 for t in baseline['search_trials'])
 assert offset==0 and not onward_only and time.monotonic()<deadline,'RECONNECTION_SCOPE'
 result=reconnect(x,table,origin,offset,min(deadline,time.monotonic()+120),checkpoint,shadow_origin=shadow_origin)
 result['retained_exhaustion']=baseline
 result['analytical_cpp_native']+=baseline['analytical_cpp_native']
 result['admission_python_native']+=baseline['admission_python_native']
 result['retained_original_successes_unchanged']=True
 return result
