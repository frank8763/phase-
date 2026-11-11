"""Saved all-native audit including true-zero ownership and complete discovery."""
import gzip,sys
from kernel import *
sys.path.insert(0,str(C))
from handoff import contained,source_check
legacy=load('v1056_saved_repeat_comparator',R/'experiments/v1051_retained_corridor_entry/audit.py')
def compare(a,b):
 x=Path(a['output']);y=Path(b['output']);sa=json.loads((x/'physics/SETUP.json').read_text());sb=json.loads((y/'physics/SETUP.json').read_text());maximum={};same=True
 with np.load(x/'physics/NATIVE_TRACE.npz')as xx,np.load(y/'physics/NATIVE_TRACE.npz')as yy:
  for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
   same=same and xx[key].shape==yy[key].shape
   maximum[key]=float(abs(xx[key]-yy[key]).max())if same and xx[key].size else 0. if same else None
 with np.load(x/'physics/INITIAL_STATE.npz')as xx,np.load(y/'physics/INITIAL_STATE.npz')as yy:initial=np.array_equal(xx['state'],yy['state'])
 with gzip.open(x/'physics/CONTACTS.json.gz','rt')as f:cx=json.load(f)
 with gzip.open(y/'physics/CONTACTS.json.gz','rt')as f:cy=json.load(f)
 contact=cx==cy;ra=json.loads((x/'RESULT.json').read_text());rb=json.loads((y/'RESULT.json').read_text());discovery=ra['physical']['first_actor_detection']==rb['physical']['first_actor_detection'];result=dict(passed=same and all(v is not None and v<=1e-8 for v in maximum.values())and initial and contact and discovery and sa['model_sha256']==sb['model_sha256'],same_lengths=same,maximum_qpos_qvel_ctrl_mocap_error=maximum,same_initial_state=initial,same_all_actual_contacts=contact,same_actual_discovery=discovery,same_model=sa['model_sha256']==sb['model_sha256'],models=0);folder=O/'REPEAT_COMPARISONS';folder.mkdir(exist_ok=True);dump(folder/(a['task_id']+'.json'),result);return result
def owner_scans(sensors):
 # Exactly two byte-equal factory binding calls precede the owner t0 scan.
 assert len(sensors)>=3 and all(scan['native_tick']==0 and scan['time']==0. for scan in sensors[:3]),'EXACT_FACTORY_T0_THREE_CALLS_REQUIRED'
 assert sensors[0]==sensors[1]==sensors[2],'FACTORY_T0_CALLS_NOT_IDENTICAL'
 owned=sensors[2:];assert all(a['native_tick']<b['native_tick']and a['time']<b['time']for a,b in zip(owned,owned[1:])),'NONCAUSAL_RECORDED_OWNER_SCANS'
 return owned
def audit_native(task,audit_dir=None):
 out=Path(task['output']);report_out=out if audit_dir is None else Path(audit_dir);report_out.mkdir(parents=True,exist_ok=True);r=json.loads((out/'RESULT.json').read_text());n=r['completed_native'];assert n is not None and n>0,'NO_COMPLETE_NATIVE_TRACE'
 setup=json.loads((out/'physics/SETUP.json').read_text());z=dict(np.load(out/'physics/NATIVE_TRACE.npz'));commands=np.array(json.loads((out/'physics/BODY_COMMANDS.json').read_text()));ctrl=z['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rate=np.array(setup['slew_per_second'])*.01;p=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);control_error=0.;memories=[np.zeros(5)]
 for c,u in zip(commands,ctrl):
  control_error=max(control_error,float(abs(u-p.adapter.compute(c[1],c[2],c[3],c[4],c[5])).max()));memories.append(np.r_[p.adapter.last,p.adapter.integral])
 safety=dict(all_native_recorded=len(commands)==n==len(z['qpos'])==r['physical']['fully_recorded_native']==r['physical']['root_guard_native_count'],actual_clearance=float(z['clearance'].min())>=.15-1e-8,self_margin=float(z['self_margin'].min())>=-1e-10,no_bad_contacts=r['physical']['bad_contacts']==0,legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rate+1e-10).all()),controller_reconstruction=control_error<=1e-10,full_own_replay=r.get('replay',{}).get('passed')is True and r.get('own_replay_native')==n and r['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,fresh_native_zero=r['fresh_native_zero']and r['historical_replay_native']==0 and r['navigation_native']==n)
 def actual_packet(packet):
  tick=packet['native_tick'];assert 0<=tick<=n and abs(packet['sim_time']-tick*.01)<=1e-7,'PACKET_CLOCK'
  if tick:
   q=z['qpos'][tick-1];v=z['qvel'][tick-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));body=np.array([q[0],q[1],yaw,v[0]*math.cos(yaw)+v[1]*math.sin(yaw),v[5]]);assert abs(body-packet['body']).max()<=1e-8,'PLANNING_BODY_NOT_ACTUAL';assert abs(q[setup['steering_qpos_addresses']]-packet['steering']['position']).max()<=1e-8;assert abs(v[setup['steering_qvel_addresses']]-packet['steering']['velocity']).max()<=1e-8
  else:assert abs(np.array(packet['body'])-json.loads((O/(task['case_id']+'_T0_METADATA.json')).read_text())['packet']['body']).max()<=1e-8
  assert abs(memories[tick]-np.r_[packet['controller_memory']['last_ctrl'],packet['controller_memory']['integral']]).max()<=1e-10,'PLANNING_MEMORY_NOT_ACTUAL'
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
  j=json.loads(journal.read_text());assert j['origin_native']==cursor;count=j['executed_native'];plan=json.loads((out/(label+'_PLAN.json')).read_text());actual_packet(plan['packet']);ss=np.array(plan['state_path']);rr=np.array(plan['planned_body_requests']);engine=Predictor(setup,initial(plan['packet']),PARAMETERS);states=[engine.state.copy()];controls=[]
  for request in rr:s,u=engine.step(*request);states.append(s);controls.append(u)
  assert np.max(abs(np.array(states)-ss))<=1e-8;assert np.max(abs(np.array(controls)-plan['predicted_actuator_controls']))<=1e-8;assert np.array_equal(commands[cursor:cursor+count][:,[1,2,5]],rr[:count]);a,b=ref._old.Geometry(setup['known'],None if plan['source']is None else plan['source']['periodic']).clearances(ss[:,:3]);assert min(a.min(),b.min())>=REQUIRED;assert plan['passed'];used_sources.extend([plan['source']]if plan['source']is not None else[]);tracking(ss,count);cursor+=count
  if label=='STATIC':
   if j['causal_discovery_interrupt']:assert cursor==r['first_causal_discovery_native']
   else:assert cursor==len(rr)
 for segment in json.loads((out/'EXECUTION_SEGMENTS.json').read_text())if(out/'EXECUTION_SEGMENTS.json').exists()else[]:
  assert segment['start_native']==cursor,'UNCOVERED_NATIVE';count=segment['executed_native'];states=np.array(segment['state_path']);tracking(states,count)
  if segment['kind']=='CERTIFIED_PARKED_HOLD':
   actual_packet(segment['planning_packet']);hs,hu,hr,hm=predict(setup,segment['planning_packet'],[dict(kind='wait',gear=0,target=0.,ticks=1200)],tail=False);assert abs(hs-states).max()<=1e-8;sa,sb=ref._old.Geometry(setup['known'],segment['planning_source']['periodic']).clearances(hs[:,:3]);assert min(sa.min(),sb.min())>=REQUIRED;used_sources.append(segment['planning_source']);assert np.array_equal(commands[cursor:cursor+count][:,[1,2,5]],np.zeros((count,3)));assert segment['minimum_raw_m']>=REQUIRED
  else:
   plan=json.loads((R/segment['adopted_plan']).read_text());packet=plan['published_packet'];source_check(packet,plan['publication_source']);proposal=json.loads((R/segment['adopted_plan']).with_name('RESULT.json').read_text());used_sources.extend([plan['planning_source'],plan['publication_source']]);assert contained(plan['publication_source']['periodic']['vertices'],proposal['source_planes']);assert 0<=plan['publication_age_s']<=.05
   actual_packet(plan['planning_packet']);actual_packet(packet);hold=plan.get('pre_adoption_hold_native',0);joined=([dict(kind='wait',gear=0,target=0.,ticks=hold)]if hold else[])+plan['actions'];ss,uu,rr,mm=predict(setup,plan['planning_packet'],joined,tail=False);memory_at_publication=mm[hold];ss,uu,rr=ss[hold:],uu[hold:],rr[hold:];assert abs(ss-states).max()<=1e-8 and abs(uu-plan['predicted_actuator_controls']).max()<=1e-8 and abs(rr-plan['planned_body_requests']).max()<=1e-12;
   if hold:assert hold==800 and packet['native_tick']==plan['planning_packet']['native_tick']+800 and abs(packet['sim_time']-plan['planning_packet']['sim_time']-8.)<=1e-7,'ADOPTED_CLOCK_MISMATCH'
   assert np.array_equal(commands[cursor:cursor+count][:,[1,2,5]],rr[:count]);g=Geometry(setup['known'],plan['planning_source']['periodic'],packet['sim_time']);low=g.complete(ss);cc,upper=checks(ss,uu,rr,dict(controller_memory=dict(last_ctrl=memory_at_publication[:4].tolist(),integral=float(memory_at_publication[4]))),setup,np.array(task['goal_xy']),low,REQUIRED);assert all(cc.values());adoptions.append(dict(start_native=cursor,native=len(rr),minimum_raw_m=low,goal_upper_m=upper))
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
 safety['canonical_model_sha']=setup['model_sha256']==json.loads((O/'PREFLIGHTS.json').read_text())[task['preflight_task_id']]['setup']['model_sha256']
 safety['actual_body_caps']=bool(abs(commands[:,3]).max()<=.13 and abs(commands[:,4]).max()<=.16)
 evidence=json.loads((out/'CAUSAL_EVIDENCE.json').read_text());assert evidence['first']==reconstructed.first,'FIRST_DISCOVERY_RECONSTRUCTION';first=evidence['first'];discovery=first['native_tick']if first else None;chain=False
 if discovery is not None and n>=discovery+328:
  zero=bool(np.array_equal(commands[discovery:discovery+328][:,[1,2,5]],np.zeros((328,3))));speed=float(np.linalg.norm(z['qvel'][discovery+327,:2]));goal=float(np.linalg.norm(z['qpos'][-1,:2]-task['goal_xy']));progress=float(np.linalg.norm(z['qpos'][-1,:2]-z['qpos'][discovery+327,:2]));physical_first=r['physical'].get('first_actor_detection');actual_discovery=physical_first is not None and physical_first['native_tick']==discovery;normal=bool(np.any(abs(commands[:discovery,1])>.005));stopped=bool(np.linalg.norm(z['qvel'][-1,:2])<=.03 and abs(z['qvel'][-1,5])<=.03);chain=zero and speed<=.03 and goal<=.45 and progress>=1. and bool(adoptions)and actual_discovery and normal and stopped;chain_record=dict(passed=chain,discovery_native=discovery,complete328_zero=zero,actual_speed_after328=speed,post_stop_net_displacement_m=progress,goal_distance_m=goal,new_causal_routes=len(adoptions));dump(report_out/'DISCOVERY_CHAIN_AUDIT.json',chain_record)
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
 result=dict(passed=bool(r['passed']and all(safety.values())and coverage and local and chain),safety_passed=bool(all(safety.values())and coverage),safety=safety,all_native_covered_once=coverage,prediction=dict(position_m=float(maximum[0]),heading_rad=float(maximum[1]),steering_rad=float(maximum[2]),passed=local),full_remainder_adoptions=adoptions,maximum_controller_error=control_error,minimum_actual_clearance_m=float(z['clearance'].min()),maximum_actor_domain_violation_m=worst,models=0,integrations=0);dump(report_out/'FINAL_INDEPENDENT_AUDIT.json',result);return result
