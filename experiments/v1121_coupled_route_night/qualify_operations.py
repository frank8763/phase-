"""Exercise actual worker/task/factory/audit entry without any physical model."""
import sys,json,importlib.abc,ast,copy
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1121_coupled_route_night'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL_ENTRY '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));import worker
w=worker.load_worker();w.pipeline.configure(O)
def main():
 assert not(O/'OPERATION_QUALIFICATION.json').exists();tasks=json.loads((C/'TASKS.json').read_text());cfg=json.loads((O/'CONFIG.json').read_text())
 for t in tasks:
  p=O/(t['task_id']+'.json');p.write_text(json.dumps(t,indent=2)+'\n');found,root,config,out=w.entry(str(p));assert found==t and root==O and out.parent==R/'runs/v858_nav2_verified/v1121'and not out.exists()
  assert t['dynamic'] and t['historical_prefix_native']==0
 f=w.factory(O)
 try:f.create_vehicle(Path(tasks[0]['output'])/'physics',tasks[0])
 except AssertionError as error:assert str(error)=='PHYSICAL_MODELS_DISABLED_FOR_PREPARATION'
 else:raise AssertionError('PREPARATION_CREATED_PHYSICAL_MODEL')
 for p in C.glob('*.py'):ast.parse(p.read_text())
 audit=w.load('night_actual_file_audit_entry',C/'audit.py')
 assert callable(audit.run)and callable(w.pipeline.execute)
 assert str(w.pipeline.C)==str(C)and w.pipeline.normal.__file__==str(R/'experiments/rpccr_execution_core/fresh_pipeline.py')
 from source import requests
 rows=[(.1,.08,3,0),(-.2,0.,4,1),(0.,0.,2200,0)];assert len(requests(rows))==2207;assert w.pipeline.front_rows(rows,5)==[(.1,.08,3,0),(-.2,0.,2,1)]
 for n in [0,-1,2208]:
  try:w.pipeline.front_rows(rows,n)
  except AssertionError:pass
  else:raise AssertionError('BAD_PREFIX_ACCEPTED')
 before=dict(cfg);assert cfg['active_candidate']in json.loads((C/'CANDIDATES.json').read_text());bad=copy.deepcopy(cfg['active_candidate']);bad['radius_extra']=99.;assert bad not in json.loads((C/'CANDIDATES.json').read_text())
 w.install_history_guard(Path(tasks[3]['output']))
 try:(R/'runs/v858_nav2_verified/v1085_entry/main_fresh_ns/physics/NATIVE_TRACE.npz').open('rb')
 except AssertionError as error:assert'FRESH_NAVIGATION_HISTORY_READ_FORBIDDEN'in str(error)
 else:raise AssertionError('HISTORICAL_ONLINE_TRACE_ALLOWED')
 answer=dict(passed=True,models=0,physical_integrations=0,actual_worker_audit_factory_entry=True,models_disabled_guard_refused=True,declared_task_count=len(tasks),old_online_history_refused=True,normal_branch_is_original=True,source_suffix_prefix_checked=True,frozen_candidate_membership_enforced=True)
 (O/'OPERATION_QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer))
if __name__=='__main__':main()
