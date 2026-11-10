"""Explicit exact V968 planner binding; fatal interface exceptions stop immediately."""
import importlib.util,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
SCIENCE_FILE=R/'experiments/v968_rpp_closed_loop_night/dynamic_proxy.py'
spec=importlib.util.spec_from_file_location('v974_exact_planner',SCIENCE_FILE);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class DynamicPlannerProxy(base.DynamicPlannerProxy):
 SCIENCE_FILE=SCIENCE_FILE
 def __init__(self,node,latest,out,deadline,forecast,configured_footprint):
  def checked_forecast():
   values=forecast()
   if not isinstance(values,tuple)or len(values)!=3:raise ValueError('PLANNER_ATOMIC_SNAPSHOT_REQUIRES_THREE_FIELDS')
   polygon,source,packet=values
   if not isinstance(source,dict)or not isinstance(packet,dict):raise TypeError('PLANNER_SNAPSHOT_SCHEMA')
   if source['source_native_tick']>packet['native_tick']:raise ValueError('PLANNER_FUTURE_SOURCE')
   return polygon,source,packet
  super().__init__(node,latest,out,deadline,checked_forecast,configured_footprint)
 async def execute(self,handle):
  result=await super().execute(handle)
  row=self.rows[-1];row['planner_implementation_source']=str(SCIENCE_FILE.relative_to(R))
  error=row.get('error','')
  if error.startswith(('ValueError(','TypeError(','AttributeError(','KeyError(','ModuleNotFoundError(','ImportError(')):
   fault=dict(error=error,row=row,at=time.monotonic(),reason='FATAL_PLANNER_INTERFACE_ERROR_NO_RETRY')
   (self.out/'PLANNER_INTERFACE_FAULT.json').write_text(json.dumps(fault,indent=2)+'\n')
   self.node.guard_failure=error
   self.node.send(dict(kind='stop',issued_at=time.monotonic(),reason=fault['reason']))
  (self.out/'ROUTER_REQUESTS.json').write_text(json.dumps(self.rows,indent=2)+'\n')
  return result
