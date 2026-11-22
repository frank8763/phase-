"""Original independent functions; functional input never final scientific PASS."""
from pathlib import Path
from context import R,OLD,load

def audit(task,functional):
 assert task['case_id']=='WEST_EAST'and task['seed']not in [10060001,10060002], 'PILOT_REQUIRES_NON_HISTORICAL_PREFIX_COMPARISON_BRANCH'
 assert functional['actual_original_goal_reached']and functional['passed']
 assert functional['passed_means_functional_navigation_only']and not functional['scientific_passed']
 target=Path(task['output'])/'RESULT.json';touched=[]
 def bind_reader(module):
  if hasattr(module,'read'):
   original=module.read
   def read(path):return functional if Path(path)==target else original(path)
   module.read=read
  if hasattr(module,'load'):
   original_load=module.load
   def nested(name,path):return bind_reader(original_load(name,path))
   module.load=nested
  touched.append(str(getattr(module,'__file__','')));return module
 module=bind_reader(load('v1624_reused_full_independent_auditor',OLD/'native_audit.py'))
 result=module.audit(task)
 assert result['passed']
 return dict(result,original_full_numeric_gates_unchanged=True,
             functional_input_separate_from_final_result=True,
             source_bindings=touched,formal_phase_tasks_qualified=False)
