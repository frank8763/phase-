"""Fresh route-aware worker, isolated physical owner and complete recorded replay."""
import sys,json,types,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];CORE=R/'experiments/rpccr_execution_core'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(CORE))
spec=importlib.util.spec_from_file_location('night_prior_qualified_worker',R/'experiments/v1097_east_west/worker.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)

def patched_source():
 s=prior.patched_source();old='import fresh_pipeline as pipeline';assert s.count(old)==1
 new="pipeline=load('night_coupled_pipeline',R/'experiments/v1121_coupled_route_night/pipeline.py')";s=s.replace(old,new)
 anchor="assert a['models_authorized']and task['task_id']in a['allowed_task_ids'];";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"assert cfg['active_candidate']in json.loads((R/'experiments/v1121_coupled_route_night/CANDIDATES.json').read_text());")
 old="except BaseException as e:r.update(passed=False,error=repr(e),traceback=traceback.format_exc())";assert s.count(old)==1
 s=s.replace(old,old+";r['functional_refusal_safely_stopped']=isinstance(e,pipeline.SourceRefusal)and(out/'FUNCTIONAL_FAILURE_STOP.json').exists()and json.loads((out/'FUNCTIONAL_FAILURE_STOP.json').read_text()).get('passed')is True")
 anchor="r['analytical_prediction_native']=live.PREDICTION_NATIVE";assert s.count(anchor)==1;s=s.replace(anchor,anchor+";r['coupled_analytical_work']=dict(pipeline.COUNTS)")
 return s

def load_worker():
 prior.prior.configure();m=types.ModuleType('night_route_worker');m.__file__=str(prior.prior.ORIGINAL);sys.path.insert(0,str(C));exec(compile(patched_source(),m.__file__,'exec'),m.__dict__);return m
if __name__=='__main__':
 m=load_worker();sys.exit(m.main())
