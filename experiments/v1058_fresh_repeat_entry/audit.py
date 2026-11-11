"""Saved all-native audit including true-zero ownership and complete discovery."""
import gzip,sys
from kernel import *
sys.path.insert(0,str(C))
from handoff import contained,source_check
legacy=load('v1056_saved_repeat_comparator',R/'experiments/v1051_retained_corridor_entry/audit.py')
def compare(a,b):return legacy.compare(a,b)
def owner_scans(sensors):
 # Exactly two byte-equal factory binding calls precede the owner t0 scan.
 assert len(sensors)>=3 and all(scan['native_tick']==0 and scan['time']==0. for scan in sensors[:3]),'EXACT_FACTORY_T0_THREE_CALLS_REQUIRED'
 assert sensors[0]==sensors[1]==sensors[2],'FACTORY_T0_CALLS_NOT_IDENTICAL'
 owned=sensors[2:];assert all(a['native_tick']<b['native_tick']and a['time']<b['time']for a,b in zip(owned,owned[1:])),'NONCAUSAL_RECORDED_OWNER_SCANS'
 return owned
def audit_native(task):
 out=Path(task['output']);r=json.loads((out/'RESULT.json').read_text());n=r['completed_native'];assert n is not None and n>0,'NO_COMPLETE_NATIVE_TRACE'
 setup=json.loads((out/'physics/SETUP.json').read_text());z=dict(np.load(out/'physics/NATIVE_TRACE.npz'));commands=np.array(json.loads((out/'physics/BODY_COMMANDS.json').read_text()));ctrl=z['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rate=np.array(setup['slew_per_second'])*.01;p=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);control_error=0.
 for c,u in zip(commands,ctrl):control_error=max(control_error,float(abs(u-p.adapter.compute(c[1],c[2],c[3],c[4],c[5])).max()))
 safety=dict(all_native_recorded=len(commands)==n==len(z['qpos'])==r['physical']['fully_recorded_native']==r['physical']['root_guard_native_count'],actual_clearance=float(z['clearance'].min())>=.15-1e-8,self_margin=float(z['self_margin'].min())>=-1e-10,no_bad_contacts=r['physical']['bad_contacts']==0,legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rate+1e-10).all()),controller_reconstruction=control_error<=1e-10,full_own_replay=r.get('replay',{}).get('passed')is True and r.get('own_replay_native')==n and r['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,fresh_native_zero=r['fresh_native_zero']and r['historical_replay_native']==0 and r['navigation_native']==n)
 maximum=np.zeros(3);cursor=0;adoptions=[];used_sources=[]
 def tracking(states,count):
  nonlocal maximum
  if count==0:return
  q=z['qpos'][cursor:cursor+count];assert len(q)==count;pred=np.array(states)[1:count+1];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));d=yaw-pred[:,2];steer=np.array([virtual(row)for row in q[:,setup['steering_qpos_addresses']]]);maximum=np.maximum(maximum,[np.linalg.norm(q[:,:2]-pred[:,:2],axis=1).max(),abs(np.arctan2(np.sin(d),np.cos(d))).max(),abs(steer-pred[:,6]).max()])
 # Use actual execution journals even when a functional assertion interrupted
 # the stage before the parent could append its summary segment.
 for label in ['STATIC','BRAKE','APPROACH']:
  journal=out/(label+'_EXECUTION.json')
  if not journal.exists():break
  j=json.loads(journal.read_text());assert j['origin_native']==cursor;count=j['executed_native'];plan=json.loads((out/(label+'_PLAN.json')).read_text());ss=np.array(plan['state_path']);rr=np.array(plan['planned_body_requests']);engine=Predictor(setup,initial(plan['packet']),PARAMETERS);states=[engine.state.copy()];controls=[]
  for request in rr:s,u=engine.step(*request);states.append(s);controls.append(u)
  assert np.max(abs(np.array(states)-ss))<=1e-8;assert np.max(abs(np.array(controls)-plan['predicted_actuator_controls']))<=1e-8;assert np.array_equal(commands[cursor:cursor+count][:,[1,2,5]],rr[:count]);a,b=ref._old.Geometry(setup['known'],None if plan['source']is None else plan['source']['periodic']).clearances(ss[:,:3]);assert min(a.min(),b.min())>=REQUIRED;assert plan['passed'];used_sources.extend([plan['source']]if plan['source']is not None else[]);tracking(ss,count);cursor+=count
  if label=='STATIC':assert j['causal_discovery_interrupt']and cursor==r['first_causal_discovery_native']
 for segment in json.loads((out/'EXECUTION_SEGMENTS.json').read_text())if(out/'EXECUTION_SEGMENTS.json').exists()else[]:
  assert segment['start_native']==cursor,'UNCOVERED_NATIVE';count=segment['executed_native'];states=np.array(segment['state_path']);tracking(states,count)
  if segment['kind']=='CERTIFIED_PARKED_HOLD':
   used_sources.append(segment['planning_source']);assert np.array_equal(commands[cursor:cursor+count][:,[1,2,5]],np.zeros((count,3)));assert segment['minimum_raw_m']>=REQUIRED
  else:
   plan=json.loads((R/segment['adopted_plan']).read_text());packet=plan['published_packet'];source_check(packet,plan['publication_source']);proposal=json.loads((R/segment['adopted_plan']).with_name('RESULT.json').read_text());used_sources.extend([plan['planning_source'],plan['publication_source']]);assert contained(plan['publication_source']['periodic']['vertices'],proposal['source_planes']);assert 0<=plan['publication_age_s']<=.05
   ss,uu,rr,mm=predict(setup,plan['planning_packet'],plan['actions'],tail=False);assert abs(ss-states).max()<=1e-8;assert np.array_equal(commands[cursor:cursor+count][:,[1,2,5]],rr[:count]);g=Geometry(setup['known'],plan['planning_source']['periodic'],packet['sim_time']);low=g.complete(ss);cc,upper=checks(ss,uu,rr,plan['planning_packet'],setup,np.array(task['goal_xy']),low,REQUIRED);assert all(cc.values());adoptions.append(dict(start_native=cursor,native=len(rr),minimum_raw_m=low,goal_upper_m=upper))
  cursor+=count
 # Reconstruct every used domain from actual saved range packets. This
 # audit has no model and never supplies evaluator actor labels to Evidence.
 causal=load('v1056_saved_causal_reconstruction',R/'experiments/v1024_full_route_execution/causal.py');normsource=load('v1056_saved_norm_reconstruction',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');reconstructed=causal.Evidence(setup['known']);reconstructed.periodic=normsource.PeriodicSupport();targets={}
 for source in used_sources:targets.setdefault(source['source_native_tick'],[]).append(source)
 with gzip.open(out/'physics/SENSORS.json.gz','rt')as f:sensors=json.load(f)
 matched=0
 sensors=owner_scans(sensors)
 for scan in sensors:
  reconstructed.update(scan)
  for source in targets.get(scan['native_tick'],[]):
   actual=reconstructed.periodic.snapshot();assert actual==source['periodic'],'CAUSAL_DOMAIN_RECONSTRUCTION';matched+=1
 safety['all_used_domains_reconstructed_from_actual_sensor_packets']=matched==len(used_sources)
 safety['canonical_model_sha']=setup['model_sha256']==json.loads((C/'CANONICAL_MODEL_SHA.json').read_text())[task['case_id']]
 safety['actual_body_caps']=bool(abs(commands[:,3]).max()<=.13 and abs(commands[:,4]).max()<=.16)
 evidence=json.loads((out/'CAUSAL_EVIDENCE.json').read_text());assert evidence['first']==reconstructed.first,'FIRST_DISCOVERY_RECONSTRUCTION';first=evidence['first'];discovery=first['native_tick']if first else None;chain=False
 if discovery is not None and n>=discovery+328:
  zero=bool(np.array_equal(commands[discovery:discovery+328][:,[1,2,5]],np.zeros((328,3))));speed=float(np.linalg.norm(z['qvel'][discovery+327,:2]));goal=float(np.linalg.norm(z['qpos'][-1,:2]-task['goal_xy']));progress=float(np.linalg.norm(z['qpos'][-1,:2]-z['qpos'][discovery+327,:2]));chain=zero and speed<=.03 and goal<=.45 and progress>=1. and bool(adoptions);chain_record=dict(passed=chain,discovery_native=discovery,complete328_zero=zero,actual_speed_after328=speed,post_stop_net_displacement_m=progress,goal_distance_m=goal,new_causal_routes=len(adoptions));dump(out/'SUPPLEMENTAL_DISCOVERY_CHAIN_AUDIT.json',chain_record)
 # Actual actor truth is evaluated ONLY after execution: each used periodic
 # domain must contain every actual native center. It never enters planning.
 domain=True;worst=-1e9;norm=load('v1056_offline_periodic_domain',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');normals=np.c_[np.cos(np.arange(8)*np.pi/8),np.sin(np.arange(8)*np.pi/8)]
 for segment in json.loads((out/'EXECUTION_SEGMENTS.json').read_text())if(out/'EXECUTION_SEGMENTS.json').exists()else[]:
  if segment['kind']=='CERTIFIED_PARKED_HOLD':source=segment['planning_source']
  else:source=json.loads((R/segment['adopted_plan']).read_text())['planning_source']
  start=segment['start_native'];count=segment['executed_native'];t=z['time'][start:start+count];xy=z['mocap_pos'][start:start+count,0,:2];vertices=source['periodic']['vertices'];rows=[]
  for j,vertices_j in enumerate(vertices):
   v=np.array(vertices_j);bound=np.max(v[:,0,None]+v[:,1,None]*np.sin(.32*t)[None,:]+v[:,2,None]*np.cos(.32*t)[None,:],axis=0);lower=np.min(v[:,0,None]+v[:,1,None]*np.sin(.32*t)[None,:]+v[:,2,None]*np.cos(.32*t)[None,:],axis=0);rows.extend([xy@normals[j]-bound,lower-xy@normals[j]])
  if count:worst=max(worst,float(np.max(rows)))
 domain=worst<=2.1e-7;coverage=cursor==n;local=bool(np.all(maximum<=[.04,.035,.015]));safety['actual_domain_offline_coverage']=domain
 result=dict(passed=bool(r['passed']and all(safety.values())and coverage and local and chain),safety_passed=bool(all(safety.values())and coverage),safety=safety,all_native_covered_once=coverage,prediction=dict(position_m=float(maximum[0]),heading_rad=float(maximum[1]),steering_rad=float(maximum[2]),passed=local),full_remainder_adoptions=adoptions,maximum_controller_error=control_error,minimum_actual_clearance_m=float(z['clearance'].min()),maximum_actor_domain_violation_m=worst,models=0,integrations=0);dump(out/'SUPPLEMENTAL_INDEPENDENT_AUDIT.json',result);return result
