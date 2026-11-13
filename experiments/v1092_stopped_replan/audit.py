"""Replay original sources and each new corridor proposal independently, no models."""
import sys,json,importlib.util,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];CORE=R/'experiments/rpccr_execution_core'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(CORE));sys.path.insert(0,str(C))
import corridor
def patched_module():
 sp=importlib.util.spec_from_file_location('active_original_scene_audit',R/'experiments/v1089_route_scene_contract/audit.py');prior=importlib.util.module_from_spec(sp);sp.loader.exec_module(prior);prior.configure();s=prior.patched_source();old="rebuilt=finite_plan(setup,p['packet'],p['source'],p['planned_body_requests'],p['scope'])";assert s.count(old)==1;s=s.replace(old,"rebuilt=rebuild_corridor_or_original(setup,p,out,task)")
 # Keep all native/causal/control gates, replace the obsolete final-LIVE
 # section with complete coverage by independently rebuilt finite sources.
 old="entry=json.loads((out/'LIVE_ENTRY.json').read_text());root=entry['packet']['native_tick']"
 assert s.count(old)==1;s=s.replace(old,"entry=json.loads((out/'INITIAL_METADATA.json').read_text());root=n")
 old="maximum=np.zeros(3);cursor=0;used=[]"
 assert s.count(old)==1;s=s.replace(old,old+";minimum=math.inf")
 old="count=row['executed_native'];assert np.array_equal"
 assert s.count(old)==1;s=s.replace(old,"minimum=min(minimum,p.get('proof',{}).get('minimum_full_cycle_raw_m',math.inf));"+old)
 begin=s.index(" assert cursor==root;actual_packet(entry['packet'])")
 end=s.index(" causal=load('fresh_audit_causal_ranges'",begin)
 s=s[:begin]+" assert cursor==n;actual_packet(entry['packet']);cross=float(maximum[0])\n"+s[end:]
 m=types.ModuleType('active_corridor_full_audit');m.__file__=str(prior.ORIGINAL)
 def rebuild(setup,p,out,task):
  if p['scope']=='CERTIFIED_REJECTION_STOP':
   import numpy as np
   import importlib.util
   spec=importlib.util.spec_from_file_location('certified_exit_stop_audit',R/'experiments/v1091_certified_exit/stop.py');stop=importlib.util.module_from_spec(spec);spec.loader.exec_module(stop)
   rejected=json.loads((R/p['rejected_future']).read_text());assert rejected['packet']==p['packet']and rejected['source']==p['source']
   failed,_,_=corridor.proof(setup,p['packet'],p['source'],np.array(rejected['requests']));assert failed==rejected['proof']and not failed['passed']
   proof,ss,uu,rr=stop.plan(setup,p['packet'],p['source']);assert proof==p['proof']and np.array_equal(rr,p['planned_body_requests'])
   return dict(passed=True,state_path=ss,predicted_actuator_controls=uu)
  if p['scope']!='FULL_CYCLE_FINITE_ACTIVE_CORRIDOR':return m.finite_plan(setup,p['packet'],p['source'],p['planned_body_requests'],p['scope'])
  import numpy as np
  if p['first_in_stage']:
   stages=json.loads((Path(out)/'ACTIVE_CORRIDOR_STAGES.json').read_text());stage=next(x for x in stages if x['stage']==p['stage']);assert p['source']==stage['source']
   # State remains identical while the analytical constructor consumes wall time.
   for key in ['body','native_tick','sim_time','dynamic_discovered','controller_memory','speed_episode']:assert p['packet'][key]==stage['packet'][key]
   for key in ['position','velocity','native_tick']:assert p['packet']['steering'][key]==stage['packet']['steering'][key]
   q=corridor.construct(setup,stage['packet'],stage['source'],Path(task['run_root']),stage['goal']);assert stage['policy']=='FINITE_GLOBAL_TO_ACTUAL_GOAL';assert q['proof']==stage['selected_proof']and q['candidates']==stage['candidates']and np.array_equal(q['requests'],stage['requests'])
  proof,ss,uu=corridor.proof(setup,p['packet'],p['source'],np.array(p['planned_body_requests']));assert proof==p['proof']and proof['passed'];return dict(passed=True,state_path=ss,predicted_actuator_controls=uu)
 m.rebuild_corridor_or_original=rebuild;exec(compile(s,str(prior.ORIGINAL),'exec'),m.__dict__);return m
if __name__=='__main__':
 task=json.loads(Path(sys.argv[1]).read_text());m=patched_module();answer=m.audit(task);print(json.dumps(answer),flush=True);sys.exit(0 if answer['passed']else 1)
