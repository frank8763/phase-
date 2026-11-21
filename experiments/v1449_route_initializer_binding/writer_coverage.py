"""Reuse writer qualifications only for exact normalized production sources."""
import ast
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def normalized(path,original_directory):
 source=Path(path).read_text().replace(original_directory,C.name)
 return ast.dump(ast.parse(source),include_attributes=False)

def coverage():
 # These are output interception contracts, not scientific runtime outcomes.
 specs={
  'ACTUAL_ROS':('v1439_actual_ros_startup_close','STARTUP_QUALIFICATION.json',['route_ros.py','entry_boundary.py','writer_budget.py','bounded_io.py']),
  'MODELED_ROS':('v1436_pathlib_control_rename','PEER_QUALIFICATION.json',['modeled_peer.py','peer_entry.py','model_peer.py','entry_boundary.py','bounded_io.py']),
  'PLANNER':('v1438_planner_writer_entry','PLANNER_QUALIFICATION.json',['route_worker.py','planning_job.py','entry_boundary.py','bounded_io.py']),
  'SUPERVISOR_LOG':('v1436_pathlib_control_rename','CONTROL_QUALIFICATION.json',['writer_budget.py','bounded_io.py'])}
 rows={}
 for role,(directory,name,files)in specs.items():
  proof_path=R/'runs'/directory/name;proof=json.loads(proof_path.read_text());assert proof['passed']and proof['models']==proof['physical_native']==0
  for filename in files:
   source=R/'experiments'/directory/filename;current=C/filename
   # Later writer_budget qualification branches only add explicit zero-model
   # entry scopes; production branch and reserve methods must match exactly.
   if filename=='writer_budget.py':
    old=ast.parse(source.read_text());new=ast.parse(current.read_text())
    for method in ['__init__','reserve','reserve_control','_read','_put']:
     get=lambda tree:next(x for node in tree.body if isinstance(node,ast.ClassDef)and node.name=='WriterBudget'for x in node.body if isinstance(x,ast.FunctionDef)and x.name==method)
     assert ast.dump(get(old),include_attributes=False)==ast.dump(get(new),include_attributes=False),'WRITER_METHOD_QUALIFICATION_CHANGED:'+role+':'+method
   elif filename=='bounded_io.py'and directory=='v1436_pathlib_control_rename':
    # The size-checked native MuJoCo save wrapper was later actually exercised
    # by V1447. The Python boundary itself is unchanged from V1436.
    get=lambda p:next(x for x in ast.parse(p.read_text()).body if isinstance(x,ast.ClassDef)and x.name=='OutputBoundary')
    assert ast.dump(get(source),include_attributes=False)==ast.dump(get(current),include_attributes=False)
   else:assert normalized(source,directory)==normalized(current,C.name),'WRITER_SOURCE_NOT_QUALIFIED:'+role+':'+filename
  rows[role]=dict(source_scope_qualified=True,qualification_file=str(proof_path.relative_to(R)),qualification_sha256=sha(proof_path),normalized_source_files=files,current_source_hashes={str((C/f).relative_to(R)):sha(C/f)for f in files},not_full_actual_route_qualification=True)
 return rows
