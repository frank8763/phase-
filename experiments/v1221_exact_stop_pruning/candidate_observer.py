"""Exact finite max-min selector with incumbent-bound early elimination.

Only the search order/work changes. A candidate whose verified prefix minimum
is strictly below the incumbent's complete minimum cannot win. A full winner
is always certified at every original boundary, with original geometry.
"""
from pathlib import Path
import importlib.util,sys,time,math
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
from current_state_tools import original,validate_input
import stop_certificates as stops
q=original.q;np=q.np
spec=importlib.util.spec_from_file_location('v1221_immutable_catalog',R/'experiments/v1195_eight_gib_timed_refuge/candidate_observer.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
candidate_rows=base.candidate_rows

def certify(x,table,rows,states,memory,deadline,incumbent=None,checkpoint=lambda _:None):
 engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);g=q.Geometry(x,table);flags=stops.flags_before(rows);offset=0;boundaries=[]
 while offset<len(states)-1:
  suffix=original.remaining_rows(rows,offset);first=suffix[0];n=int(first[2])if first[3]or first[1]==0. else min(8,int(first[2]));boundaries.append((offset,n));offset+=n
 # Every current stop contains its own initial state: its raw minimum is
 # bounded above by that state's geometric clearance. Used only to eliminate
 # a candidate, never to certify one. Small outward rounding protects ties.
 indices=np.array([k for k,n in boundaries]);a,b=g.components(states[indices,:3],indices);raw=np.minimum(a,b);j=int(np.argmin(raw));upper=float(raw[j])+1e-10
 if incumbent is not None and upper<incumbent:
  return dict(passed=False,pruned=True,records=[],upper_bound_m=upper,incumbent_m=incumbent,state_bound_witness=dict(offset=int(indices[j]),raw_m=float(raw[j])),analytical_cpp_native=engine.native)
 records={};minimum=float('inf')
 ordered=sorted(zip(raw,boundaries),key=lambda item:(item[0],item[1][0]))
 for _,(offset,n) in ordered:
  assert time.monotonic()<deadline,'EXACT_STOP_SEARCH_DEADLINE'
  block=original.front(original.remaining_rows(rows,offset),n);p=stops.forecast(x,states[offset],memory[offset],offset);origin=dict(state=states[offset],last_ctrl=memory[offset,:4],integral=float(memory[offset,4]),**flags[offset]);p.update({k:v for k,v in flags[offset].items()if k!='steering_load_episode'})
  proofs,_=stops.prove(engine,g,x,p,origin,block)
  rec=dict(offset=offset,prefix=n,current_passed=proofs[0]['passed'],prospective_passed=proofs[1]['passed'],current_raw=proofs[0]['minimum_raw_m'],prospective_raw=proofs[1]['minimum_raw_m'],failed=[k for proof in proofs for k,v in proof['checks'].items()if not v]);records[offset]=rec
  minimum=min(minimum,rec['current_raw'],rec['prospective_raw'])
  if not all(p['passed']for p in proofs):return dict(passed=False,pruned=False,records=[records[k]for k in sorted(records)],failed_offset=offset,analytical_cpp_native=engine.native)
  # Strict comparison: equal minima must retain the old tie-breaking rules.
  if incumbent is not None and minimum<incumbent:
   return dict(passed=False,pruned=True,records=[rec],upper_bound_m=minimum,incumbent_m=incumbent,witness=rec,analytical_cpp_native=engine.native)
  if len(records)%100==0:checkpoint(dict(stage='exact_stop_certificates',done=len(records),total=len(boundaries),cpp_native=engine.native))
 return dict(passed=True,pruned=False,records=[records[k]for k in sorted(records)],analytical_cpp_native=engine.native)

def _synthesize(x,table,deadline,checkpoint=lambda _:None):
 validate_input(x);g=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);origin=dict(q.initial(x['packet']),steering_load_episode=False)
 trials=[];eligible=[];work=0;best=None
 initial_ss,initial_u,_=engine.simulate(origin,[(0.,0.,2200,0)]);target=initial_ss[-1,:3].tolist();common,_=g.final(dict(x,goal=target[:2],safe_terminal_pose=target),initial_ss,initial_u,[(0.,0.,2200,0)]);assert common['passed'],'NO_CURRENT_COMPLETE_STOP_AT_SELECTION_ENTRY'
 common_bound=common['minimum_raw_m']
 catalog=[(0.,0)]+[(t,n)for n in[200,400,600,800]for t in[0.,-.16,-.24,-.32,-.42722137342572125]]
 for turn,ticks in catalog:
  for cut in[11400,11800]:
   assert time.monotonic()<deadline,'CURRENT_OBSERVER_SYNTHESIS_BUDGET'
   rows=candidate_rows(turn,ticks,cut);ss,uu,mm=engine.simulate(origin,rows);proof,_=g.final(dict(x,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,rows)
   progress=float(np.linalg.norm(np.asarray(x['packet']['body'][:2])-x['goal'])-np.linalg.norm(ss[-1,:2]-x['goal']));proof['checks']['observation_progress']=progress>=.5;proof['passed']=bool(all(proof['checks'].values()))
   target=np.array([1.68,-1.18,-.74]);distance=float(np.linalg.norm(ss[-1,:2]-target[:2]));yaw=abs(math.atan2(math.sin(ss[-1,2]-target[2]),math.cos(ss[-1,2]-target[2])))
   row=dict(turn=turn,stage_native=ticks,cut=cut,passed=proof['passed'],raw=proof['minimum_raw_m'],progress=progress,refuge_guide_distance=distance,failed=[k for k,v in proof['checks'].items()if not v]);trials.append(row)
   if proof['passed']:eligible.append((distance+.2*yaw,rows,ss,uu,mm,proof,row,len(trials)-1))
  checkpoint(dict(stage='observer_fixed_candidates',done=len(trials),eligible=len(eligible),cpp_native=engine.native))
 # Heuristic work order only; every eliminated candidate has a real certificate
 # witness bounding its final objective, not an assumed bound from this score.
 eligible.sort(key=lambda a:(a[0],len(a[3]),a[7]))
 for distance,rows,ss,uu,mm,proof,row,index in eligible:
  # Every reference starts at the same measured origin and must include this
  # exact current stop. Bound the full lexicographic objective, including ties.
  optimistic=(-common_bound,distance,len(uu),index)
  if best is not None and optimistic>=best[0]:
   row.update(complete_stops_passed=False,pruned=True,common_origin_bound_m=common_bound,optimistic_rank=optimistic,incumbent_rank=best[0]);checkpoint(dict(stage='exact_common_stop_tie_elimination',candidate=index,common_bound=common_bound));continue
  spec=importlib.util.spec_from_file_location('v1221_endpoint_bound',Path(__file__).with_name('endpoint_bound.py'));bounds=importlib.util.module_from_spec(spec);spec.loader.exec_module(bounds)
  bound=bounds.upper_bound(q,original,stops,x,table,rows,ss,mm,deadline,None if best is None else -best[0][0]);work+=bound['analytical_cpp_native']
  if bound['refusal_witness']is not None:
   witness=bound['refusal_witness'];k=witness['offset'];n=witness['prefix'];flags=stops.flags_before(rows);p=stops.forecast(x,ss[k],mm[k],k);p.update({key:v for key,v in flags[k].items()if key!='steering_load_episode'});origin=dict(state=ss[k],last_ctrl=mm[k,:4],integral=float(mm[k,4]),**flags[k]);e=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);pp,_=stops.prove(e,g,x,p,origin,original.front(original.remaining_rows(rows,k),n));work+=e.native;assert not all(p['passed']for p in pp),'ENDPOINT_FAILURE_NOT_REPRODUCED'
   rec=dict(offset=k,prefix=n,current_passed=pp[0]['passed'],prospective_passed=pp[1]['passed'],current_raw=pp[0]['minimum_raw_m'],prospective_raw=pp[1]['minimum_raw_m'],failed=[key for pr in pp for key,v in pr['checks'].items()if not v])
   row.update(passed=False,complete_stops_passed=False,pruned=False,stop_failed_offset=k,stop_failure_witness=rec,minimum_stop_raw_m=min(pr['minimum_raw_m']for pr in pp));row['failed'].append('all_along_route_stops');checkpoint(dict(stage='exact_infeasibility_witness',candidate=index,failed_offset=k,checks=rec['failed']));continue
  if best is not None and bound['upper_bound_m'] < -best[0][0]:
   row.update(complete_stops_passed=False,pruned=True,endpoint_bound_witness=bound['witness'],incumbent_m=-best[0][0],upper_bound_m=bound['upper_bound_m']);checkpoint(dict(stage='exact_endpoint_elimination',candidate=index,upper_bound=bound['upper_bound_m'],incumbent=-best[0][0]));continue
  certificate=certify(x,table,rows,ss,mm,deadline,None if best is None else -best[0][0],checkpoint);work+=certificate['analytical_cpp_native']
  if certificate.get('state_bound_witness'):
   row.update(complete_stops_passed=False,pruned=True,state_bound_witness=certificate['state_bound_witness'],incumbent_m=certificate['incumbent_m'],upper_bound_m=certificate['upper_bound_m']);continue
  reserve=min(min(r['current_raw'],r['prospective_raw'])for r in certificate['records'])
  row['limiting_stop_witness']=min(certificate['records'],key=lambda r:min(r['current_raw'],r['prospective_raw']))
  row.update(complete_stops_passed=certificate['passed'],minimum_stop_raw_m=reserve,stop_failed_offset=certificate.get('failed_offset'),pruned=certificate['pruned'])
  if certificate['pruned']:
   row.update(pruning_witness=certificate['witness'],incumbent_m=certificate['incumbent_m'],upper_bound_m=certificate['upper_bound_m']);continue
  if not certificate['passed']:
   row['stop_failure_witness']=next(r for r in certificate['records']if not r['current_passed']or not r['prospective_passed']);row['passed']=False;row['failed'].append('all_along_route_stops');checkpoint(dict(stage='exact_full_stop_failure',candidate=index,failed_offset=certificate.get('failed_offset'),checks=row['stop_failure_witness']['failed']));continue
  rank=(-reserve,distance,len(uu),index)
  if best is None or rank<best[0]:best=(rank,rows,ss,uu,mm,proof,row,certificate)
  checkpoint(dict(stage='exact_candidate_complete',candidate=index,complete_stops_passed=certificate['passed'],minimum=reserve,best=None if best is None else -best[0][0]))
 answer=dict(passed=best is not None,trials=trials,analytical_cpp_native=engine.native+work,candidate_cpp_native=engine.native,stop_certificate_cpp_native=work,models=0,new_mujoco_native=0,scope='exact original max-min objective; only sound bound work pruning',scientific_selection_unchanged=True,common_origin_stop_proof=common)
 if best:
  _,rows,ss,uu,mm,proof,row,certificate=best;answer.update(rows=rows,states=ss,controls=uu,memory=mm,proof=proof,selected=row,complete_stop_qualification=certificate,current_entry_native=x['packet']['native_tick'],current_clock=x['packet']['sim_time'])
 return answer


def synthesize(x,table,deadline,checkpoint=lambda _:None):
 # Identical pure interval extrema, scoped to this finite selection only.
 spec=importlib.util.spec_from_file_location('v1221_exact_interval_cache',Path(__file__).with_name('exact_cache.py'));memo=importlib.util.module_from_spec(spec);spec.loader.exec_module(memo)
 with memo.interval_cache(q)as stats:
  answer=_synthesize(x,table,deadline,checkpoint)
 answer['exact_interval_cache']=stats
 return answer
