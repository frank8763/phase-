"""Finite causal state/time/control-memory search; goal REGION, complete stop.

Every edge uses the unchanged qualified actuator dynamics. Discrete search is
not complete; selected full sources still require Python replay and ALL8 stops.
"""
from primitives import *
import heapq,math,signal,traceback
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'))
from geometry import Geometry
sys.path.insert(0,str(R/'experiments/v1146_causal_certificate_refresh'))
from fast_cycle import certify as cycle_certify
from recovery_source import forecast_packet

def main():
 job=json.loads(Path(sys.argv[1]).read_text());assert job in json.loads((C/'PROFILES.json').read_text());qualification='--qualification'in sys.argv
 if qualification:
  assert not json.loads((O/'APPROVAL.json').read_text())['models_authorized']and not(O/'DRIVER_STARTED.json').exists()
  job=dict(job,max_expansions=10,wall_s=120,output=str(O/'SOFTWARE_ENTRY_QUALIFICATION'))
 out=Path(job['output']);out.mkdir(exist_ok=False);begun=time.monotonic();end=min(time.monotonic()+job['wall_s'],time.monotonic()+remaining()-120)
 def halt(*_):raise TimeoutError('PRIMITIVE_SOURCE_ROOT_OR_WORKER_DEADLINE')
 signal.signal(signal.SIGALRM,halt);signal.signal(signal.SIGTERM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.monotonic()))
 error=None;expander=None;engine=None;python_native=0;calls=0;expanded=0;best_distance=None;proof=None;backups=[];selected=None;reason='BOUNDED_FRONTIER';result=None
 try:
  assert source_ok()and used()<int(1.8*1024**3)
  if qualification:
   saved=R/'runs/v1145_observer_failure_review';x=dict(setup=json.loads((R/'runs/v858_nav2_verified/v1144/observation_main/physics/SETUP.json').read_text()),packet=json.loads((saved/'SAVED_STOP_PACKET.json').read_text()),source=json.loads((saved/'SAVED_OBSERVATION_SOURCE.json').read_text()),goal=[4.,-2.],safe_terminal_pose=[4.,-1.85,0.]);table=np.load(saved/'SAVED_JOINT_TABLE.npz')
  else:x=json.loads((O/'actual_source/FRESH_INPUT.json').read_text());table=np.load(O/'actual_source/JOINT_TABLE.npz')
  g=Geometry(x,{k:table[k]for k in ['bounds','centers']});origin=initial(x['packet']);assert not origin['coupled_episode']and not origin['steering_motion_active'];expander=Expander(x['setup']);engine=Engine(x['setup']);goal=np.asarray(x['goal']);start_clock=x['packet']['sim_time'];targets=np.array([-CAP,-.32,-.16,0.,.16,.32,CAP]);speed=float(job['speed']);steps=job['edge_native'];weight=job['heuristic_weight']
  state=np.asarray(origin['state']);memory=np.r_[origin['last_ctrl'],origin['integral']];nodes=[dict(state=state,memory=memory,tick=0,parent=-1,row=None,cost=0.)];heap=[(weight*float(np.linalg.norm(state[:2]-goal)),0.,0)];seen={};best_distance=float(np.linalg.norm(state[:2]-goal));goal_attempts=0
  def rows_to(index):
   rows=[]
   while nodes[index]['parent']!=-1:rows.append(nodes[index]['row']);index=nodes[index]['parent']
   return list(reversed(rows))+[(0.,0.,2200,0)]
  while heap and expanded<job['max_expansions']and len(nodes)<80000:
   if time.monotonic()>end-90 or remaining()<180:reason='FINITE_TIME_RESERVE';break
   _,cost,index=heapq.heappop(heap);node=nodes[index];s=node['state'];m=node['memory'];tick=node['tick'];key=state_key(s,m,tick,start_clock)
   if cost>seen.get(key,float('inf'))+1e-9:continue
   expanded+=1;distance=float(np.linalg.norm(s[:2]-goal));best_distance=min(best_distance,distance)
   if distance<=.60 and goal_attempts<300:
    goal_attempts+=1;rows=rows_to(index);ss,uu=engine.simulate(origin,rows);terminal=ss[-1,:3];local=dict(x,safe_terminal_pose=terminal.tolist());candidate,_=g.final(local,ss,uu,rows)
    # The original goal predicate remains upper-distance<=.45; a free terminal
    # pose is not permission to move the registered goal or weaken the margin.
    if candidate['passed']and candidate['goal_upper_m']<=.45:
     ps,pu,mem,episodes,active=python_replay(x['setup'],origin,rows);python_native+=len(pu);difference=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));assert difference<=1e-8,'FULL_PRIMITIVE_PYTHON_REPLAY_MISMATCH';proof=candidate;selected=dict(rows=rows,terminal_pose=terminal.tolist(),input=local,maximum_python_cpp_error=difference)
     nodes8=list(range(0,len(pu)-2200+1,8))+[len(pu)-2200]
     for i in sorted(set(nodes8)):
      assert time.monotonic()<end-5 and remaining()>30,'ALL8_AUDIT_DEADLINE'
      inp=dict(state=ps[i],last_ctrl=mem[i,:4],integral=float(mem[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bs,bu=engine.simulate(inp,[(0.,0.,2200,0)]);packet=forecast_packet(x['packet'],ps[i],mem[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bx=dict(local,packet=packet,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist());bp=cycle_certify(bx,bs,bu,[(0.,0.,2200,0)])
      if not bp['passed']:bp,_=g.final(bx,bs,bu,[(0.,0.,2200,0)])
      backups.append(dict(native=i,passed=bp['passed'],minimum_raw_m=bp['minimum_raw_m'],terminal_cycle_m=bp['terminal_full_cycle_raw_m'],failed_checks=[k for k,v in bp['checks'].items()if not v],states_sha256=bp['states_sha256'],controls_sha256=bp['controls_sha256']))
     dump(out/'SELECTED.json',selected);dump(out/'SOURCE_PROOF.json',proof);dump(out/'ALL8_BACKUPS.json',backups);np.savez_compressed(out/'SOURCE.npz',states=ps,controls=pu,memory=mem,episodes=episodes,active=active);reason='COMPLETE_SOURCE_AND_ALL8'if all(b['passed']for b in backups)else'BRAKE_ONLY_BACKUPS_REFUSED';break
   if tick+steps+2200>14000:continue
   batches=[(targets,speed,steps)]
   if max(abs(s[3:6]))<=.003 and abs(s[7])<=.015:batches.append((np.array([0.]),0.,job['wait_native']))
   for angles,velocity,duration in batches:
    states,controls,memories=expander.expand(s,m,angles,velocity,duration);calls+=1
    for j,angle in enumerate(angles):
     path=states[j];allstates=np.vstack([s,path]);ticks=np.arange(tick,tick+duration+1);a,b=g.components(allstates[:,:3],ticks)
     if float(np.minimum(a,b).min())<REQUIRED+.001:continue
     if abs(path[:,3]).max()>.13 or abs(path[:,4]).max()>.03 or abs(path[:,5]).max()>.16:continue
     next_state=path[-1].copy();next_mem=memories[j].copy();ntick=tick+duration;nk=state_key(next_state,next_mem,ntick,start_clock);edge=float(np.linalg.norm(np.diff(allstates[:,:2],axis=0),axis=1).sum())+.0002*duration+.02*abs(float(angle)-s[6]);ncost=cost+edge
     if ncost>=seen.get(nk,float('inf'))-1e-9:continue
     seen[nk]=ncost;ni=len(nodes);nodes.append(dict(state=next_state,memory=next_mem,tick=ntick,parent=index,row=(float(angle),velocity,duration,0),cost=ncost));h=float(np.linalg.norm(next_state[:2]-goal));heapq.heappush(heap,(ncost+weight*h,ncost,ni))
   if expanded%100==0:dump(out/'PROGRESS.json',dict(expanded=expanded,nodes=len(nodes),frontier=len(heap),best_goal_center_distance_m=best_distance,analytical_native=expander.native+engine.native,goal_attempts=goal_attempts))
  passed=bool(proof and proof['passed']and backups and all(b['passed']for b in backups))
  result=dict(closed=True,passed=passed,full_source_passed=bool(proof and proof['passed']),stop_reason=reason,expanded=expanded,stored_nodes=len(nodes),frontier=len(heap),best_goal_center_distance_m=best_distance,goal_attempts=goal_attempts,backup_count=len(backups),failed_backups=sum(not b['passed']for b in backups),original_goal=x['goal'],terminal_region_not_fixed_arbitrary_pose=True,approximate_merging_not_completeness=True,physical_goal_passed=False)
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc());dump(out/'ERROR.json',error)
 finally:
  signal.setitimer(signal.ITIMER_REAL,0)
  result=result or dict(closed=True,passed=False,stop_reason='OPERATION_MODEL_SOURCE_OR_EVIDENCE_ERROR',best_goal_center_distance_m=best_distance,expanded=expanded)
  result.update(error=error,entry_qualification_only=qualification,counts=dict(analytical_expansion_native=expander.native if expander else 0,expansion_inflight_unknown=bool(expander and expander.partial_unknown),analytical_full_profile_native=engine.native if engine else 0,profile_inflight_unknown=bool(engine and getattr(engine,'in_call',False)),independent_python_native=python_native),models=0,physical_native=0,training_updates=0,wall_s=time.monotonic()-begun,source_unchanged=source_ok());dump(out/'RESULT.json',result);print(encode(result))
 return 0 if error is None else 1

if __name__=='__main__':sys.exit(main())
