"""Bounded parked planning and clock-independent crossing publication.

Planning owns no actuators. The existing certified zero-input hold remains the
only command until a fresh, causally enclosed publication is accepted. Only
existing full stops permit refresh; a crossing is one retained moving suffix.
"""
import itertools,json,math,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
from kernel import Predictor,PARAMETERS,initial,predict,ref,REQUIRED,virtual,load
refresh_module=load('v1053_qualified_refresh',R/'experiments/v1052_measured_retained_refresh/refresh.py')
interval=load('v1053_interval_support',R/'experiments/v1035_signed_timed_input_source/time_geometry.py')
PERIOD=2*math.pi/.32;SLOT=.01;MAX_HOLD=1200;N=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
def parked(packet):
 refresh_module.validate_measured_packet(packet,packet['sent_at']);u=np.array(packet['controller_memory']['last_ctrl'])
 assert abs(packet['body'][3])<=.003 and abs(packet['body'][4])<=.03,'NOT_PARKED'
 assert abs(u[2:]).max()<=1e-10 and packet['controller_memory']['integral']==0.,'CONTROLLER_NOT_IN_HOLD'
 assert abs(np.array(packet['steering']['velocity'])).max()<=.03,'ENCODER_NOT_SETTLED'
def source_check(packet,source):
 assert source['source_native_tick']<=packet['native_tick'],'FUTURE_SOURCE'
 assert 0<=source['source_age_s']<=.051,'STALE_SENSOR_SOURCE'
 p=source['periodic'];assert p['omega']==.32 and p['amplitude']==.25 and p['source_tick']<=source['source_native_tick'],'PUBLIC_CLASS_OR_CAUSALITY_CHANGED'
def hold_permission(setup,packet,source):
 parked(packet);source_check(packet,source);actions=[dict(kind='wait',gear=0,target=0.,ticks=MAX_HOLD)];ss,uu,rr,mm=predict(setup,packet,actions,tail=False);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[:,:3]);low=float(np.minimum(a,b).min());assert low>=REQUIRED,'NO_FULL_CYCLE_BOUNDED_HOLD'
 return dict(passed=True,states=ss.tolist(),requests=rr.tolist(),minimum_raw_m=low,maximum_native=MAX_HOLD,source_tick=packet['native_tick'])
def planes(vertices):
 result=[]
 for values in vertices:
  v=np.array(values);triples=np.array(list(itertools.combinations(range(len(v)),3)));n=np.cross(v[triples[:,1]]-v[triples[:,0]],v[triples[:,2]]-v[triples[:,0]]);length=np.linalg.norm(n,axis=1);valid=length>=1e-12;n=n[valid]/length[valid,None];triples=triples[valid];b=np.einsum('ij,ij->i',v[triples[:,0]],n);d=v@n.T-b;hi=d.max(axis=0);lo=d.min(axis=0);outward=hi<=2e-9;inward=lo>=-2e-9;keep=outward|inward;n[~outward]*=-1;b[~outward]*=-1;faces=np.c_[n[keep],b[keep]+3e-9];_,ids=np.unique(np.round(faces,8),axis=0,return_index=True);assert len(ids),'DEGENERATE_SOURCE';result.append(faces[np.sort(ids)].tolist())
 return result
def contained(new_vertices,old_planes):
 if len(new_vertices)!=len(old_planes):return False
 return all(float((np.asarray(v)@np.asarray(h)[:,:3].T-np.asarray(h)[:,3]).max())<=1e-8 for v,h in zip(new_vertices,old_planes))
def prepare(setup,packet,source,goal,actions,elapsed):
 started=time.monotonic();hold_permission(setup,packet,source);generic=any('speed'in a for a in actions)
 if generic:
  prefix=[dict(kind='wait',gear=0,target=0.,ticks=200)];suffix=refresh_module.remainder(actions,elapsed)
 else:
  result=refresh_module.refresh(setup,packet,source,goal,actions,elapsed);assert result['passed'],'NO_REQUALIFIED_REMAINDER'
  route=result['actions'];wait=result['departure_wait_ticks'];prefix=route[:-3]if wait else route[:-2];suffix=route[-2:]
 # A fresh stopped packet needs a settling hold before using the stationary
 # wait equivalence. At intermediate stops this is absorbed in the next safe
 # prefix; at the entry it is executed once without recursively re-planning.
 if not prefix:prefix=[dict(kind='wait',gear=0,target=0.,ticks=200)]
 ss,uu,rr,mm=predict(setup,packet,prefix,tail=False);a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[:,:3]);minimum=float(np.minimum(a,b).min());assert minimum>=REQUIRED+1e-7,'PREFIX_NOT_PHASE_INDEPENDENT'
 p=Predictor(setup,dict(state=ss[-1],last_ctrl=mm[-1,:4],integral=mm[-1,4],virtual_rate=.6),PARAMETERS);waiting=[p.state.copy()];wc=[]
 for _ in range(math.ceil(PERIOD/.01)+1):q,u=p.step(0.,0.,False);waiting.append(q);wc.append(u)
 waiting=np.array(waiting);assert np.max(abs(waiting-ss[-1]))<1e-7,'WAIT_NOT_STATIONARY'
 p=Predictor(setup,dict(state=ss[-1],last_ctrl=mm[-1,:4],integral=mm[-1,4],virtual_rate=.6),PARAMETERS);cross=[p.state.copy()];cu=[];cr=[]
 for a in suffix:
  v=float(a.get('speed',.08 if a['gear']>0 else-.03))if a['kind']=='move'else 0.;w=v*math.tan(a['target'])/.6
  for _ in range(a['ticks']):q,u=p.step(v,w,False);cross.append(q);cu.append(u);cr.append([v,w,False])
 cross=np.array(cross);full=ref._old.Geometry(setup['known'],source['periodic']);a,b=full.clearances(cross[-1:,:3]);assert min(a[0],b[0])>=REQUIRED+1e-7,'TERMINAL_HOLD'
 # Launch slot j and native k occupy [(j+k)*dt,(j+k+1)*dt]. Evaluate exact
 # coefficient extrema ONCE for all sums j+k, including .05 clock + .005
 # native interval; periodic trig handles wrap without sampled phase lookup.
 # The final shortened launch slot is conservatively covered by a full cell.
 slots=math.ceil(PERIOD/SLOT);times=np.arange(slots+len(cross))*SLOT
 support=interval.interval_support(source['periodic']['vertices'],times-.055,times+SLOT+.055);theta=cross[:,2];front=np.c_[np.cos(theta),np.sin(theta)];left=np.c_[-np.sin(theta),np.cos(theta)];body=cross[:,:2]@N.T-.44*abs(front@N.T)-.375*abs(left@N.T);static=ref._old.Geometry(setup['known'],None).clearances(cross[:,:3])[0];bounds=[]
 for j in range(slots):bounds.append(float(np.minimum(static,(body-support[j:j+len(cross)]-.1).max(axis=1)).min()))
 assert max(bounds)>=REQUIRED+1e-7,'NO_ABSOLUTE_LAUNCH_INTERVAL'
 # Fixed representative waits verify exact original Python composition. The
 # full wait tube is also checked above, without resetting any memory.
 equivalence=0.
 for w in [0,1,499,1000,math.ceil(PERIOD/.01)]:
  p=Predictor(setup,dict(state=ss[-1],last_ctrl=mm[-1,:4],integral=mm[-1,4],virtual_rate=.6),PARAMETERS)
  for _ in range(w):p.step(0.,0.,False)
  trajectory=[p.state.copy()]
  for v,y,stale in cr:q,u=p.step(v,y,stale);trajectory.append(q)
  equivalence=max(equivalence,float(abs(np.array(trajectory)-cross).max()))
 assert equivalence<1e-8,'WAIT_COMPOSITION_NOT_EQUIVALENT'
 return dict(passed=True,packet=packet,source_planes=planes(source['periodic']['vertices']),source=source,goal=goal,prefix=prefix,suffix=suffix,prefix_states=ss.tolist(),prefix_controls=uu.tolist(),prefix_requests=rr.tolist(),wait_states=waiting.tolist(),wait_controls=np.array(wc).tolist(),cross_states=cross.tolist(),cross_controls=np.array(cu).tolist(),cross_requests=cr,launch_bounds=bounds,minimum_prefix_raw_m=minimum,wait_composition_max_error=equivalence,wall_s=time.monotonic()-started,models=0)
def publish(proposal,packet,source,now):
 parked(packet);refresh_module.validate_measured_packet(packet,now);source_check(packet,source);base=proposal['packet'];assert 0<=packet['native_tick']-base['native_tick']<=MAX_HOLD,'PROPOSAL_EXPIRED'
 assert contained(source['periodic']['vertices'],proposal['source_planes']),'SOURCE_DOMAIN_EXPANDED'
 b=np.array(base['body']);q=np.array(packet['body']);d=q[2]-b[2];assert np.linalg.norm(q[:2]-b[:2])<=.001 and abs(math.atan2(math.sin(d),math.cos(d)))<=.001,'HOLD_POSE_DRIFT'
 assert abs(virtual(packet['steering']['position'])-virtual(base['steering']['position']))<=.001,'HOLD_STEERING_DRIFT'
 assert np.max(abs(np.array(packet['controller_memory']['last_ctrl'])-base['controller_memory']['last_ctrl']))<=1e-10,'HOLD_MEMORY_CHANGED'
 n=len(proposal['prefix_requests']);bounds=np.array(proposal['launch_bounds']);choices=[]
 for wait in range(1,math.ceil(PERIOD/.01)+1):
  phase=(packet['sim_time']+(n+wait)*.01)%PERIOD;slot=min(int(phase/SLOT),len(bounds)-1)
  if bounds[slot]>=REQUIRED+1e-7:choices.append((float(bounds[slot]),-wait,wait))
 assert choices,'NO_CURRENT_LAUNCH_INTERVAL';low,_,wait=max(choices);states=np.vstack([proposal['prefix_states'],np.array(proposal['wait_states'])[1:wait+1],np.array(proposal['cross_states'])[1:]]);controls=np.vstack([proposal['prefix_controls'],np.array(proposal['wait_controls'])[:wait],proposal['cross_controls']]);requests=np.vstack([proposal['prefix_requests'],np.zeros((wait,3)),proposal['cross_requests']]);actions=proposal['prefix']+[dict(kind='wait',gear=0,target=0.,ticks=wait)]+proposal['suffix'];checkpoint=len(requests);tick=0;had_move=False
 for action in proposal['prefix']:
  tick+=action['ticks'];had_move=had_move or action['kind']=='move'
  if action['kind']=='wait'and action['ticks']>=200 and had_move:checkpoint=tick;break
 return dict(passed=True,actions=actions,state_path=states.tolist(),predicted_actuator_controls=controls.tolist(),planned_body_requests=requests.tolist(),next_checkpoint_native=checkpoint,phase_wait_ticks=wait,minimum_raw_m=min(low,proposal['minimum_prefix_raw_m']),published_packet=packet,publication_age_s=now-packet['body_measured_at'],source_native_tick=source['source_native_tick'],terminal_goal_upper_m=float(np.linalg.norm(states[-1,:2]-proposal['goal']))+.08,retained_suffix_audit=dict(passed=True,contract='PARKED_REFRESH_RETAINED_MOVING_SUFFIX',moving_fallback_not_brake_only=True),proposal_wall_s=proposal['wall_s'])
sys.path.insert(0,str(C))
