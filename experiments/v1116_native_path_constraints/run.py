"""One bounded full-source optimizer, mandatory original Python independent audit."""
import sys,json,time,signal,hashlib,shutil,traceback,importlib.abc,math
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1116_native_path_constraints';OLD=R/'runs/v1107_reference_frame_alignment'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','factory','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));import kernel,numpy as np
from bindings import Predictor,initial
from recovery_source import forecast_packet
sys.path.insert(0,str(C));from solver import Solver,CAP,KNOTS
from bindings import Adapter
sys.path.insert(0,str(R/'experiments/v1103_connected_reference'));from reference_contract import context,admit,select_after_recheck
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def replay_rows(x,rows,origin=None):
 inp=initial(x['packet'])if origin is None else origin;p=Predictor(x['setup'],inp,kernel.PARAMETERS);p.adapter.__class__=Adapter
 ss=[p.state.copy()];uu=[];rr=[];mm=[np.r_[p.adapter.last,p.adapter.integral]];flags=[];targets=[];episodes=[]
 for target,speed,ticks,mode in rows:
  p.adapter.parked_target=target if mode else None;w=0. if mode or speed==0. else speed*math.tan(target)/.6
  for _ in range(ticks):
   s,u=p.step(speed,w,False);ss.append(s);uu.append(u);rr.append([speed,w,0.]);mm.append(np.r_[p.adapter.last,p.adapter.integral]);flags.append(mode);targets.append(target);episodes.append(p.coupled_episode)
 return np.array(ss),np.array(uu),np.array(rr),np.array(mm),np.array(flags),np.array(targets),np.array(episodes)
def distances(poses,q):
 edge=np.diff(q[:,:2],axis=0);den=(edge*edge).sum(axis=1);a=poses[:,None,:2]-q[None,:-1,:2];f=np.divide((a*edge).sum(axis=2),den,out=np.zeros(a.shape[:2]),where=den>0.);return np.linalg.norm(a-np.clip(f,0,1)[:,:,None]*edge,axis=2).min(axis=1)
def main():
 assert not(O/'PLAN.json').exists();qualification=json.loads((O/'ENTRY_QUALIFICATION.json').read_text());assert qualification['passed'];binding=json.loads((O/'SOURCE_FREEZE.json').read_text());assert all(sha(R/n)==h for n,h in binding.items())
 for p in C.iterdir():
  if p.suffix in {'.py','.cpp','.md'}:shutil.copyfile(p,O/p.name)
 guard=sha(R/'REVIEW_PENDING');begun=time.monotonic();solver=None;retained=None;replacement=None;counts=dict(python_full_source=0,python_rolling_stops=0)
 def halt(*_):raise TimeoutError('BOUNDED240S_JOINT_SOURCE')
 signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,240)
 save('PLAN.json',dict(scope='same EW21520 coupled-model full source with original explicit constraints',optimizer_wall_s=120,max_calls_including_jacobian=1700,max_iterations=40,steering_knots_per_gear=12,duration_scale_bounds=[.75,1.35],parked_native=600,complete_stop_native=2200,inner_s=240,outer_s=250,automatic_physical_launch=False))
 answer=dict(passed=False)
 try:
  x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());pg=json.loads((OLD/'PATH_GEARS.json').read_text());seed=json.loads((R/'runs/v1115_coupled_complete_source/OPTIMIZATION.json').read_text())['z'];solver=Solver(x,np.array(pg['path']),pg['gear'],initial_guess=seed)
  with np.load(R/'runs/v1103_connected_reference/RETAINED_STOP.npz')as z:retained=dict(context=context(x),requests=z['requests'].copy(),controls=z['controls'].copy(),independent_stop_passed=True)
  best,iterations=solver.solve();save('OPTIMIZATION.json',dict(cost=best['cost'],endpoint_errors_m=best['endpoint_errors'],constraints=best['constraints'],optimizer_exit=solver.optimizer_exit,calls=solver.calls,iterations=iterations,z=best['z'].tolist(),success_not_implied_by_cost=True))
  cpp_s,cpp_u,rows,events=solver.simulate(best['z'],reserved_final=True);save('CONTROL_SCHEDULE.json',dict(rows=rows,sections=events));answer['optimizer_constraint_review']=solver.constraint_terms(cpp_s,events)[1]
  ss,uu,rr,memory,modes,targets,episodes=replay_rows(x,rows);counts['python_full_source']=len(rr)
  np.savez_compressed(O/'CONTROLLER_SOURCE.npz',states=ss,controls=uu,requests=rr,memory=memory,command_modes=modes,steering_targets=targets,coupled_episodes=episodes)
  error=max(float(abs(ss-cpp_s).max()),float(abs(uu-cpp_u).max()));answer['cpp_python_maximum_error']=error;assert error<=1e-8,'FULL_SOURCE_DYNAMICS_MISMATCH'
  a,b=kernel.ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[:,:3]);low=float(np.minimum(a,b).min());cc,upper=kernel.checks(ss,uu,rr,x['packet'],x['setup'],np.array(x['goal']),low,kernel.REQUIRED)
  cross=0.;section_rows=[];settled=True;all_endpoints=True
  for section,((q,arc,d),(begin,moving,end))in enumerate(zip(solver.sections,events)):
   # Include the preceding steering-only block in its outgoing gear section.
   start=begin-600 if section else begin;maximum=float(distances(ss[start:end+1],q).max());cross=max(cross,maximum);endpoint=float(np.linalg.norm(ss[end,:2]-q[-1,:2]));all_endpoints&=endpoint<=.02
   if section:
    expected=targets[begin-1];stable=bool(abs(ss[begin-9:begin+1,6]-expected).max()<=.005 and abs(ss[begin-9:begin+1,7]).max()<=.015 and abs(ss[begin-9:begin+1,3:6]).max()<=.003);settled&=stable
   section_rows.append(dict(gear=d,start_native=start,moving_end_native=moving,end_native=end,stopped_endpoint_error_m=endpoint,maximum_cross_track_m=maximum))
  envelope_rows=[];envelopes_passed=True
  for i,(begin,moving,end)in enumerate(events):
   if not i:continue
   anchor_index=begin-600;anchor=ss[anchor_index,:3];st,dy=kernel.ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(anchor[None,:]);raw=float(min(st[0],dy[0]));lower=raw-.02-math.hypot(.44,.375)*.1
   phase=ss[anchor_index:begin+1];pos=float(np.linalg.norm(phase[:,:2]-anchor[:2],axis=1).max());angle=float(abs(np.arctan2(np.sin(phase[:,2]-anchor[2]),np.cos(phase[:,2]-anchor[2]))).max());speed=float(abs(phase[:,3]).max());okay=bool(lower>=kernel.REQUIRED and pos<=.02 and angle<=.1 and speed+.002<=.01);envelopes_passed&=okay;envelope_rows.append(dict(start_native=anchor_index,whole_mode_raw_lower_m=lower,translation_m=pos,angle_rad=angle,speed_m_s=speed,passed=okay))
  cc.update(path_cross_track=cross<=.04,gear_endpoints_within_02=bool(all_endpoints),parked_alignment_settled=bool(settled),coupled_mode_envelopes=bool(envelopes_passed),complete2200stop=np.array_equal(rr[-2200:],np.zeros((2200,3))),terminal_full_cycle_hold=min(a[-1],b[-1])>=kernel.REQUIRED)
  review=dict(passed=bool(all(cc.values())),checks={k:bool(v)for k,v in cc.items()},minimum_full_cycle_raw_m=low,goal_upper_m=upper,maximum_predicted_cross_track_m=cross,sections=section_rows,coupled_envelopes=envelope_rows,analytical_native=len(rr));answer['complete_review']=review
  if review['passed']:
   stops=[]
   for i in range(0,len(rr)-2200,125):
    packet=forecast_packet(x['packet'],ss[i],memory[i],i);origin=initial(packet);origin['state']=ss[i].copy();origin['last_ctrl']=memory[i,:4].copy();origin['integral']=float(memory[i,4]);origin['coupled_episode']=bool(episodes[i-1])if i else False
    stop_s,stop_u,stop_r,_,_,_,_=replay_rows(dict(x,packet=packet),[(0.,0.,2200,0)],origin);counts['python_rolling_stops']+=2200
    st,dy=kernel.ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(stop_s[:,:3]);sl=float(np.minimum(st,dy).min());sc,_=kernel.checks(stop_s,stop_u,stop_r,packet,x['setup'],stop_s[-1,:2],sl,kernel.REQUIRED);sc.pop('goal_upper');passed=bool(all(sc.values()));stops.append(dict(offset_native=i,passed=passed,full_stop_controls_passed=passed,stop_raw_m=sl))
    if not passed:break
   review.update(rolling_stops=stops,passed=bool(stops and all(s['passed']for s in stops)))
   if review['passed']:
    manifest=admit(x,review,ss,uu,rr);manifest.update(command_modes_sha256=hashlib.sha256(modes.tobytes()).hexdigest(),steering_targets_sha256=hashlib.sha256(targets.tobytes()).hexdigest(),coupled_episode_sha256=hashlib.sha256(episodes.tobytes()).hexdigest(),coupled_model_coefficient_sha256=sha(R/'experiments/v1114_coupled_steering_mode/COUPLING.json'));save('COMPLETE_REFERENCE_CONTRACT.json',manifest);replacement=dict(context=context(x),manifest=manifest,whole_goal_admitted=True);answer['passed']=True
 except BaseException as e:answer.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:signal.setitimer(signal.ITIMER_REAL,0)
 if retained is not None:
  selected=select_after_recheck(context(x),retained,replacement);answer['handoff_selection']=dict(mode=selected['mode'],retained_stop_preserved=True,actual_execution=False)
 if solver is not None:answer['cpp_accounting']=dict(completed_calls=solver.calls,completed_native=solver.native,partial_call_work_unknown=solver.in_call)
 answer['python_accounting']=counts;answer['entry_analytical_work']=qualification['analytical_work'];answer['frozen_source_unchanged']=all(sha(R/n)==h for n,h in binding.items());answer['guard_original']=sha(R/'REVIEW_PENDING')==guard;answer['passed']=bool(answer['passed']and answer['frozen_source_unchanged']and answer['guard_original'])
 answer.update(closed=True,wall_s=time.monotonic()-begun,models=0,physical_integrations=0,official_planning_calls=0,new_measurements=0,automatic_physical_launch=False,whole_route_acceptance=False);save('COMPLETION.json',answer)
 pointer=R/'CURRENT_EXPERIMENT.json';current=json.loads(pointer.read_text())
 if current.get('active_run')=='runs/v1116_native_path_constraints':
  current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_software_experiment=dict(version='v1116',completion='runs/v1116_native_path_constraints/COMPLETION.json',passed=answer['passed'],closed=True,physical_integrations=0,whole_route_acceptance=False));tmp=pointer.with_suffix('.v1115.tmp');tmp.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n');tmp.replace(pointer)
 print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
