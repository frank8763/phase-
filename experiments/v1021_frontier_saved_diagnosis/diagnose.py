"""Saved frontier counterfactuals only: no model imports, controls or safety acceptance."""
import copy,hashlib,importlib.abc,importlib.util,json,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1021_frontier_saved_diagnosis';O.mkdir(exist_ok=True)
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL_DIAGNOSIS '+name)
sys.meta_path.insert(0,NoModel())
p=R/'experiments/v1019_terminal_progress_recovery/reference.py';spec=importlib.util.spec_from_file_location('actual_frozen_search',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original=p.read_text();results=[]
for route in ['we','ns']:
 out=R/'runs/v858_nav2_verified/v1020'/('main_'+route);record=json.loads((out/'RECOVERY_CORRIDORS.json').read_text())[-1];packet=record['search_packet'];src=record['search_source'];goal=record['original_goal'];known=json.loads((out/'physics/SETUP.json').read_text())['known']
 for mode in ['original','static_only_COUNTERFACTUAL','include_depth_in_key','fine_grid_2x','horizon24_COUNTERFACTUAL','no_minimum_progress_COUNTERFACTUAL']:
  code=original
  if mode=='include_depth_in_key':code=code.replace('round(p[3]/(ref.MAX_DELTA/2)))','round(p[3]/(ref.MAX_DELTA/2)),depth)')
  if mode=='fine_grid_2x':code=code.replace('p[0]/.05','p[0]/.025').replace('p[1]/.05','p[1]/.025').replace(')*72/',' )*144/').replace(')%72',')%144')
  if mode=='horizon24_COUNTERFACTUAL':code=code.replace('if depth>=12:','if depth>=24:')
  if mode=='no_minimum_progress_COUNTERFACTUAL':code=code.replace('progress>=.4 or','progress>=.01 or')
  # Instrument only an in-memory copy. No frozen source is written.
  code=code.replace('allowed=(values>=ref.REQUIRED).all(axis=1)',"allowed=(values>=ref.REQUIRED).all(axis=1)\n        probes.append(dict(depth=depth,static_rejected=int((a.reshape(len(ref.TARGETS),ref.EDGE_N)<ref.REQUIRED).any(axis=1).sum()),dynamic_rejected=int((b.reshape(len(ref.TARGETS),ref.EDGE_N)<ref.REQUIRED).any(axis=1).sum()),allowed=int(allowed.sum()),nominal_progress=progress))")
  namespace=dict(__file__=str(p),__name__='saved_diagnostic_'+mode,probes=[]);exec(compile(code,str(p),'exec'),namespace)
  geom=namespace['ref']._old.Geometry
  if mode=='static_only_COUNTERFACTUAL':
   class StaticOnly(geom):
    def __init__(self,known,prior):super().__init__(known,None)
   namespace['ref']._old.Geometry=StaticOnly
  try:
   started=time.monotonic();answer=namespace['construct'](packet,src,goal,known,packet['body_measured_at'],time.time()+2.)
  finally:namespace['ref']._old.Geometry=geom
  probes=namespace['probes'];summary=dict(route=route,mode=mode,passed_geometric_search=answer['passed'],status=answer['status'],expanded=answer.get('expanded'),generated=answer.get('generated'),rejected_edges=answer.get('rejected_edges'),
   max_depth=max((x['depth']for x in probes),default=0),maximum_progress_lower_at_expansion=max((x['nominal_progress']for x in probes),default=None),
   static_rejected_edges=sum(x['static_rejected']for x in probes),dynamic_rejected_edges=sum(x['dynamic_rejected']for x in probes),
   returned_progress_lower=answer.get('actual_goal_progress_lower_m'),wall_s=time.monotonic()-started,
   actual_input_prediction_checked=False,not_a_physical_or_safe_control_pass=True)
  if mode=='original':assert not answer['passed']and answer['status']==record['proposal']['source_proposal']['status']and answer['expanded']==record['proposal']['source_proposal']['expanded']
  results.append(summary);print(json.dumps(summary),flush=True)
result=dict(models=0,integrations=0,new_controls=0,old_source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),original_failure_reproduced=True,results=results,
 limitation='Counterfactual search results are geometric diagnostics only. Static-only removes dynamic safety, horizon24 exceeds registered controller horizon and tiny-progress lowers function requirement; none is an execution certificate. No alternative was run on a vehicle.')
(O/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
