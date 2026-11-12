"""Replay original sources and each new corridor proposal independently, no models."""
import sys,json,importlib.util,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];CORE=R/'experiments/rpccr_execution_core'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(CORE));sys.path.insert(0,str(C))
import corridor
def patched_module():
 sp=importlib.util.spec_from_file_location('active_original_scene_audit',R/'experiments/v1089_route_scene_contract/audit.py');prior=importlib.util.module_from_spec(sp);sp.loader.exec_module(prior);prior.configure();s=prior.patched_source();old="rebuilt=finite_plan(setup,p['packet'],p['source'],p['planned_body_requests'],p['scope'])";assert s.count(old)==1;s=s.replace(old,"rebuilt=rebuild_corridor_or_original(setup,p,out,task)")
 m=types.ModuleType('active_corridor_full_audit');m.__file__=str(prior.ORIGINAL)
 def rebuild(setup,p,out,task):
  if p['scope']!='FULL_CYCLE_FINITE_ACTIVE_CORRIDOR':return m.finite_plan(setup,p['packet'],p['source'],p['planned_body_requests'],p['scope'])
  import numpy as np
  if p['first_in_stage']:
   stages=json.loads((Path(out)/'ACTIVE_CORRIDOR_STAGES.json').read_text());stage=next(x for x in stages if x['stage']==p['stage']);assert p['source']==stage['source']
   # State remains identical while the analytical constructor consumes wall time.
   for key in ['body','native_tick','sim_time','dynamic_discovered','controller_memory','speed_episode']:assert p['packet'][key]==stage['packet'][key]
   for key in ['position','velocity','native_tick']:assert p['packet']['steering'][key]==stage['packet']['steering'][key]
   try:m.live.produce(setup,stage['packet'],stage['source'],Path(task['run_root']),stage['goal']);rejection=None
   except AssertionError as e:rejection=str(e)
   assert rejection==stage['original_goal_proposal_rejection'],'RECOVERY_TRIGGER_NOT_REPRODUCED'
   q=corridor.construct(setup,stage['packet'],stage['source'],Path(task['run_root']),stage['goal']);assert q['proof']==stage['selected_proof']and q['candidates']==stage['candidates']and np.array_equal(q['requests'],stage['requests'])
  proof,ss,uu=corridor.proof(setup,p['packet'],p['source'],np.array(p['planned_body_requests']));assert proof==p['proof']and proof['passed'];return dict(passed=True,state_path=ss,predicted_actuator_controls=uu)
 m.rebuild_corridor_or_original=rebuild;exec(compile(s,str(prior.ORIGINAL),'exec'),m.__dict__);return m
if __name__=='__main__':
 task=json.loads(Path(sys.argv[1]).read_text());m=patched_module();answer=m.audit(task);print(json.dumps(answer),flush=True);sys.exit(0 if answer['passed']else 1)
