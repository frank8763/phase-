"""Original bounded writers; only the admission context capability differs."""
import ast
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;F=R/'experiments/v1456_route_closure_binding'
def coverage():
 s=importlib.util.spec_from_file_location('v1458_frozen_writer_contracts',F/'writer_coverage.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows=m.coverage()
 for filename in ['route_ros.py','planning_job.py','route_worker.py','entry_boundary.py','writer_budget.py','bounded_io.py']:
  assert ast.dump(ast.parse((C/filename).read_text()))==ast.dump(ast.parse((F/filename).read_text())),'LIVE_EVENT_WRITER_LOGIC_CHANGED:'+filename
 old=ast.parse((F/'route_context.py').read_text());new=ast.parse((C/'route_context.py').read_text())
 old.body=[node for node in old.body if not(isinstance(node,ast.FunctionDef)and node.name=='authorize')];new.body=[node for node in new.body if not(isinstance(node,ast.FunctionDef)and node.name=='authorize')]
 assert ast.dump(old)==ast.dump(new),'LIVE_EVENT_CONTEXT_CHANGED_BEYOND_EXPLICIT_SCOPE'
 for row in rows.values():row.update(live_first_event_scope_relocation_only=True,not_complete_runtime_qualification=True)
 return rows
