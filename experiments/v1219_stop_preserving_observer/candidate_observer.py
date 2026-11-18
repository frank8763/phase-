"""Fixed original candidates ranked by complete along-route stopping reserve."""
from pathlib import Path
import importlib.util,sys,time,math,json
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
from current_state_tools import original,validate_input
import stop_certificates as stops
q=original.q;np=q.np
spec=importlib.util.spec_from_file_location('phase_v1219_original_observer',R/'experiments/v1195_eight_gib_timed_refuge/candidate_observer.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
candidate_rows=base.candidate_rows

def synthesize(x,table,deadline,checkpoint=lambda _:None):
 validate_input(x);g=q.Geometry(x,table);engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);origin=dict(q.initial(x['packet']),steering_load_episode=False)
 trials=[];eligible=[];stop_work=0
 catalog=[(0.,0)]+[(t,n)for n in[200,400,600,800]for t in[0.,-.16,-.24,-.32,-.42722137342572125]]
 for turn,ticks in catalog:
  for cut in[11400,11800]:
   assert time.monotonic()<deadline,'CURRENT_OBSERVER_SYNTHESIS_BUDGET'
   rows=candidate_rows(turn,ticks,cut);ss,uu,mm=engine.simulate(origin,rows);one=dict(x,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist());proof,_=g.final(one,ss,uu,rows)
   progress=float(np.linalg.norm(np.asarray(x['packet']['body'][:2])-x['goal'])-np.linalg.norm(ss[-1,:2]-x['goal']));proof['checks']['observation_progress']=progress>=.5;proof['passed']=bool(all(proof['checks'].values()))
   target=np.array([1.68,-1.18,-.74]);distance=float(np.linalg.norm(ss[-1,:2]-target[:2]));yaw=abs(math.atan2(math.sin(ss[-1,2]-target[2]),math.cos(ss[-1,2]-target[2])))
   row=dict(turn=turn,stage_native=ticks,cut=cut,passed=proof['passed'],raw=proof['minimum_raw_m'],progress=progress,refuge_guide_distance=distance,failed=[k for k,v in proof['checks'].items()if not v]);trials.append(row)
   if proof['passed']:eligible.append((distance+.2*yaw,rows,ss,uu,mm,proof,row))
  checkpoint(dict(stage='observer_fixed_candidates',done=len(trials),eligible=len(eligible),cpp_native=engine.native))
 best=None
 for distance,rows,ss,uu,mm,proof,row in eligible:
  certificate=stops.certify_reference(x,table,rows,ss,mm,deadline,checkpoint);stop_work+=certificate['analytical_cpp_native']
  reserve=min(min(r['current_raw'],r['prospective_raw']) for r in certificate['records'])
  row.update(complete_stops_passed=certificate['passed'],minimum_stop_raw_m=reserve,stop_failed_offset=certificate.get('failed_offset'))
  if not certificate['passed']:row['passed']=False;row['failed'].append('all_along_route_stops');continue
  rank=(-reserve,distance,len(uu))
  if best is None or rank<best[0]:best=(rank,rows,ss,uu,mm,proof,row,certificate)
 answer=dict(passed=best is not None,trials=trials,analytical_cpp_native=engine.native+stop_work,candidate_cpp_native=engine.native,stop_certificate_cpp_native=stop_work,models=0,new_mujoco_native=0,scope='finite reference stop-reserve ranking, not robust invariant proof')
 if best:
  _,rows,ss,uu,mm,proof,row,certificate=best;answer.update(rows=rows,states=ss,controls=uu,memory=mm,proof=proof,selected=row,complete_stop_qualification=certificate,current_entry_native=x['packet']['native_tick'],current_clock=x['packet']['sim_time'])
 return answer
