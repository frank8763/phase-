"""Independent exact-selector witness review, zero physical integrations."""
from pathlib import Path
import importlib.util,sys,math,time,copy
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v1186_live_observer_regeneration'))
from current_state_tools import original
import stop_certificates as stops
q=original.q;np=q.np
spec=importlib.util.spec_from_file_location('v1221_auditor_original_catalog',R/'experiments/v1195_eight_gib_timed_refuge/candidate_observer.py');cat=importlib.util.module_from_spec(spec);spec.loader.exec_module(cat)
def verify(x,table,chosen,deadline):
 engine=q.accelerator.Engine(x['setup'],q.model.parameters()['coefficients']);geometry=q.Geometry(x,table);org=dict(q.initial(x['packet']),steering_load_episode=False);sel=chosen['selected'];win=sel['minimum_stop_raw_m'];winner=None;checks=[]
 catalog=[(0.,0)]+[(t,n)for n in[200,400,600,800]for t in[0.,-.16,-.24,-.32,-.42722137342572125]]
 initial,control,_=engine.simulate(org,[(0.,0.,2200,0)]);target=initial[-1,:3].tolist();common,_=geometry.final(dict(x,goal=target[:2],safe_terminal_pose=target),initial,control,[(0.,0.,2200,0)]);assert common['passed']and common['states_sha256']==chosen['common_origin_stop_proof']['states_sha256'] and common['minimum_raw_m']==chosen['common_origin_stop_proof']['minimum_raw_m']
 common_bound=common['minimum_raw_m']
 selected_index=next(i for i,t in enumerate(chosen['trials'])if (t['turn'],t['stage_native'],t['cut'])==(sel['turn'],sel['stage_native'],sel['cut']))
 winner_rows=cat.candidate_rows(sel['turn'],sel['stage_native'],sel['cut']);winner_ss,winner_uu,_=engine.simulate(org,winner_rows);winner_distance=float(np.linalg.norm(winner_ss[-1,:2]-[1.68,-1.18]));winner_yaw=abs(math.atan2(math.sin(winner_ss[-1,2]+.74),math.cos(winner_ss[-1,2]+.74)));final_rank=(-win,winner_distance+.2*winner_yaw,len(winner_uu),selected_index)
 expected=[(t,n,c)for t,n in catalog for c in[11400,11800]];assert len(chosen['trials'])==len(expected)==42
 for idx,(trial,(turn,ticks,cut))in enumerate(zip(chosen['trials'],expected)):
  assert time.monotonic()<deadline and (trial['turn'],trial['stage_native'],trial['cut'])==(turn,ticks,cut)
  rows=cat.candidate_rows(turn,ticks,cut);ss,uu,mm=engine.simulate(org,rows);proof,_=geometry.final(dict(x,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,rows)
  progress=float(np.linalg.norm(np.asarray(x['packet']['body'][:2])-x['goal'])-np.linalg.norm(ss[-1,:2]-x['goal']));eligible=proof['passed']and progress>=.5
  if not eligible:
   assert not trial['passed'];checks.append(dict(index=idx,reason='original_feasibility_refused'));continue
  flags=stops.flags_before(rows)
  if trial.get('common_origin_bound_m')is not None:
   distance=float(np.linalg.norm(ss[-1,:2]-[1.68,-1.18]));yaw=abs(math.atan2(math.sin(ss[-1,2]+.74),math.cos(ss[-1,2]+.74)))
   optimistic=(-common_bound,distance+.2*yaw,len(uu),idx);incumbent=tuple(trial['incumbent_rank'])
   assert common_bound==trial['common_origin_bound_m']and tuple(trial['optimistic_rank'])==optimistic and optimistic>=incumbent and optimistic>=final_rank and -incumbent[0]<=win,'UNSOUND_COMMON_ORIGIN_BOUND'
   checks.append(dict(index=idx,reason='shared_complete_initial_stop_lexicographic_bound',upper_bound=common_bound));continue
  witness=trial.get('pruning_witness')or trial.get('stop_failure_witness')or trial.get('limiting_stop_witness')
  if trial.get('state_bound_witness'):
   w=trial['state_bound_witness'];k=w['offset'];assert 0<=k<len(ss)-1
   cursor=0;boundaries=set()
   while cursor<len(ss)-1:
    boundaries.add(cursor);suffix=original.remaining_rows(rows,cursor);first=suffix[0];cursor+=int(first[2])if first[3]or first[1]==0. else min(8,int(first[2]))
   assert k in boundaries and trial['incumbent_m']<=win
   p=stops.forecast(x,ss[k],mm[k],k);g=copy.copy(geometry);g.original=copy.copy(geometry.original);g.original.start=p['sim_time'];a,b=g.components(ss[k:k+1,:3],[0]);raw=float(min(a[0],b[0]))
   assert abs(raw-w['raw_m'])<=1e-10 and raw+1e-10<win,'UNSOUND_STATE_BOUND'
   checks.append(dict(index=idx,reason='initial_stop_state_upper_bound',upper_bound=raw+1e-10));continue
  if trial.get('endpoint_bound_witness'):
   w=trial['endpoint_bound_witness'];k=w['offset'];suffix=original.remaining_rows(rows,k);first=suffix[0];n=int(first[2])if first[3]or first[1]==0. else min(8,int(first[2]));assert w['prefix']==n
   block=original.front(suffix,n);origin=dict(state=ss[k],last_ctrl=mm[k,:4],integral=float(mm[k,4]),**flags[k]);schedule=[(0.,0.,2200,0)]if w['kind']=='current'else [*block,(0.,0.,2200,0)]
   pred,_,_=engine.simulate(origin,schedule);assert type(w['relative_native'])is int and 0<=w['relative_native']<len(pred)
   p=stops.forecast(x,ss[k],mm[k],k);local=copy.copy(geometry);local.original=copy.copy(geometry.original);local.original.start=p['sim_time'];a,b=local.components(pred[w['relative_native']:w['relative_native']+1,:3],[w['relative_native']]);raw=float(min(a[0],b[0]))
   assert abs(raw-w['raw_m'])<=1e-10 and raw+1e-9<trial['incumbent_m']<=win,'UNSOUND_ENDPOINT_UPPER_BOUND'
   checks.append(dict(index=idx,reason='complete_stop_endpoint_upper_bound',upper_bound=raw+1e-9));continue
  assert witness is not None,'MISSING_EXACT_SELECTION_WITNESS'
  k=witness['offset'];suffix=original.remaining_rows(rows,k);first=suffix[0];n=int(first[2])if first[3]or first[1]==0. else min(8,int(first[2]));assert n==witness['prefix']
  p=stops.forecast(x,ss[k],mm[k],k);p.update({name:v for name,v in flags[k].items()if name!='steering_load_episode'});origin=dict(state=ss[k],last_ctrl=mm[k,:4],integral=float(mm[k,4]),**flags[k]);proofs,_=stops.prove(engine,geometry,x,p,origin,original.front(suffix,n))
  for name,pr in zip(['current','prospective'],proofs):assert pr['passed']==witness[name+'_passed'] and abs(pr['minimum_raw_m']-witness[name+'_raw'])<=1e-8
  raw=min(pr['minimum_raw_m']for pr in proofs)
  if trial.get('pruned'):
   assert all(p['passed']for p in proofs)and raw<trial['incumbent_m']<=win,'UNSOUND_INCUMBENT_PRUNING'
  elif not trial['complete_stops_passed']:assert not all(p['passed']for p in proofs)
  else:
   assert raw<=win and abs(raw-trial['minimum_stop_raw_m'])<=1e-8
   distance=float(np.linalg.norm(ss[-1,:2]-[1.68,-1.18]));yaw=abs(math.atan2(math.sin(ss[-1,2]+.74),math.cos(ss[-1,2]+.74)))
   rank=(-raw,distance+.2*yaw,len(uu),idx)
   if winner is None or rank<winner[0]:winner=(rank,trial)
  checks.append(dict(index=idx,reason='complete_stop_witness',upper_bound=raw))
 assert winner is not None and all(winner[1][k]==sel[k]for k in ['turn','stage_native','cut','minimum_stop_raw_m'])
 return dict(passed=True,exact_original_maxmin_selection=True,candidate_witnesses=checks,analytical_cpp_native=engine.native,models=0,new_mujoco_native=0)
