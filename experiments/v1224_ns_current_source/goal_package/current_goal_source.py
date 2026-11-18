"""Route-independent current-state full-goal source; no WE refuge coordinates."""
from pathlib import Path
import time
from .candidate_search import q,np,search,PreviewGeometry
from .admission import preview as feedback_preview

def generate(x,table,origin,offset,deadline,checkpoint=lambda _:None,*,onward_only=False,shadow_origin=None):
 assert x['setup']['case']['id']=='NORTH_SOUTH','NS_SOURCE_ROUTE_REQUIRED'
 assert shadow_origin is not None,'CONTINUOUS_SHADOW_REQUIRED'
 work=0
 def admit(candidate):
  nonlocal work
  result,_=feedback_preview(x,table,origin,shadow_origin,offset,candidate,deadline);work+=result['python_native'];return result
 result=search(x,table,min(deadline,time.monotonic()+120),checkpoint,preview=dict(origin=origin,native_offset=offset,shadow_origin=shadow_origin),admit=admit,expansion_limit=3000)
 result.update(prefix_rows=None,method='current_state_NS_direct_control_space',admission_python_native=work)
 return result
