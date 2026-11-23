"""Original search/evaluation/sampler code, distinct PhaseG2 generator+feasibility."""
import ast,copy,hashlib,math,sys,time,types
from round_common import *

def bind_factory(np,source,payload,accounting):
 original=load('v1762_exact_original_binding',R/'experiments/v1749_sccr_public_interface/binding.py');core,helpers,proof=original.bind(np,source)
 shape=load('v1762_new_phase_g2_shape',C/'shape_and_gate.py')
 def generator(segment,signed_offset,shoulder):return np.asarray(shape.control_polygon(segment.tolist(),float(signed_offset),float(shoulder)),dtype=np.float32)
 ns=vars(core).copy();ns['_build_control_points']=generator
 evaluate=types.FunctionType(core._evaluate_candidate.__code__,ns,core._evaluate_candidate.__name__,core._evaluate_candidate.__defaults__,core._evaluate_candidate.__closure__)
 def wrapped(*args,**kwargs):
  assert accounting['evaluations']<648,'ORIGINAL_FINITE_SEARCH_COUNT_EXCEEDED';accounting['evaluations']+=1
  candidate=evaluate(*args,**kwargs)
  if candidate is None:accounting['null_candidates']+=1;return None
  gate=shape.full_path_gate(candidate.active_path.tolist(),float(payload['observation']['body'][2]))
  original_feasible=bool(candidate.feasible);accounting['original_geometric_feasible']+=int(original_feasible);accounting['phase_feasible']+=int(original_feasible and gate['passed'])
  accounting['candidate_rows'].append(dict(index=accounting['evaluations'],original_geometric_feasible=original_feasible,phase_gate=gate,offset=candidate.offset,approach_distance=candidate.approach_distance,rejoin_distance=candidate.rejoin_distance,shoulder=candidate.shoulder,objective=candidate.objective,score=candidate.score))
  updated=copy.copy(candidate);updated.feasible=bool(original_feasible and gate['passed']);assert updated.objective==candidate.objective and updated.score==candidate.score
  return updated
 ns_search=vars(core).copy();ns_search['_evaluate_candidate']=wrapped
 search=types.FunctionType(core.search_continuous_corridor.__code__,ns_search,core.search_continuous_corridor.__name__,core.search_continuous_corridor.__defaults__,core.search_continuous_corridor.__closure__)
 assert search.__code__ is core.search_continuous_corridor.__code__ and evaluate.__code__ is core._evaluate_candidate.__code__
 assert ns['_sample_bspline'] is core._sample_bspline
 accounting['original_search_evaluation_sampler_bodies_unchanged']=True
 return types.SimpleNamespace(search_continuous_corridor=search),helpers,proof

def run(payload,source):
 assert read(O/'CURRENT_QUERY_ADMISSION.json')['maximum_adapted_search_calls']==1
 sys.path.insert(0,str(R/'experiments/v1749_sccr_public_interface'))
 template=load('v1762_original_query_template',R/'experiments/v1749_sccr_public_interface/query.py')
 accounting=dict(evaluations=0,null_candidates=0,original_geometric_feasible=0,phase_feasible=0,candidate_rows=[])
 ns=vars(template).copy();ns['O']=O;ns['bind']=lambda np,s:bind_factory(np,s,payload,accounting)
 execute=types.FunctionType(template.run.__code__,ns,template.run.__name__,template.run.__defaults__,template.run.__closure__)
 started=time.monotonic();answer=execute(payload,source);elapsed=time.monotonic()-started
 answer['template_scope']=answer.pop('scope');answer.update(scope='SCCR_PHASE_G2_ADAPTED_GEOMETRIC_QUERY',method_identity='SCCR-PhaseG2-v1762',full_historical_SCCR=False,original_method_rerun=False,new_curve_generator=True,original_search_bounds_and_scoring_unchanged=True,full_path_vehicle_filter_added=True,adapted_query_wall_s=elapsed)
 assert accounting['evaluations']==answer.get('candidate_count')==648,'SEARCH_FINITE_DENOMINATOR_CHANGED'
 if answer['candidate_found']:
  shape=load('v1762_selected_gate',C/'shape_and_gate.py');answer['selected_phase_gate']=shape.full_path_gate(answer['selected_path'],float(payload['observation']['body'][2]));assert answer['selected_phase_gate']['passed']
 return answer,accounting
