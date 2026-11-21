"""Keep proven frozen writers exact; new actual ROS entry is an AST relocation."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;F=R/'experiments/v1449_route_initializer_binding'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def coverage():
 s=importlib.util.spec_from_file_location('v1456_frozen_writer_source_proofs',F/'writer_coverage.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base);rows=base.coverage()
 current={'ACTUAL_ROS':['route_ros.py','route_context.py','planning_job.py','entry_boundary.py','writer_budget.py','bounded_io.py'],'PLANNER':['route_worker.py','entry_boundary.py','writer_budget.py','bounded_io.py'],'SUPERVISOR_LOG':['writer_budget.py','bounded_io.py']}
 for role,files in current.items():
  for filename in files:assert ast.dump(ast.parse((C/filename).read_text()))==ast.dump(ast.parse((F/filename).read_text())),'RELOCATED_WRITER_CHANGED:'+role+filename
  rows[role].update(current_source_hashes={str((C/f).relative_to(R)):sha(C/f)for f in files},relocation_only_no_new_processes_executed=True)
 # MODELED_ROS still executes the identical frozen model_peer/peer_entry sources.
 rows['MODELED_ROS']['explicit_frozen_execution_directory']=str(F.relative_to(R))
 return rows
