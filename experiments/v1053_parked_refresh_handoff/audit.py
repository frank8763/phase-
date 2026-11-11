"""All native safety plus epoch coverage, local forecast and causal publication."""
import sys
from kernel import *
sys.path.insert(0,str(C))
from handoff import contained,source_check
legacy=load('v1053_old_saved_audit',R/'experiments/v1051_retained_corridor_entry/audit.py')
def audit_native(task,full_profile=True):
 out=Path(task['output']);r=json.loads((out/'RESULT.json').read_text());n=r['completed_native']
 if n==0:
  result=dict(passed=False,safety_passed=False,no_native_integrations=True,models=0,reason='INITIALIZATION_OR_ENTRY_FAILED_NO_NATIVE_TRACE_EXPECTED');dump(out/'FINAL_INDEPENDENT_AUDIT.json',result);return result
 setup=json.loads((out/'physics/SETUP.json').read_text());z=dict(np.load(out/'physics/NATIVE_TRACE.npz'));commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());ctrl=z['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01;p=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);control_error=0.
 for c,u in zip(commands,ctrl):control_error=max(control_error,float(abs(u-p.adapter.compute(c[1],c[2],c[3],c[4],c[5])).max()))
 safety=dict(all_native_recorded=len(commands)==n==len(z['qpos'])==r['physical']['fully_recorded_native']==r['physical']['root_guard_native_count'],actual_clearance=float(z['clearance'].min())>=.15-1e-8,self_margin=float(z['self_margin'].min())>=-1e-10,no_bad_contacts=r['physical']['bad_contacts']==0,legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rate+1e-10).all()),controller_reconstruction=control_error<=1e-10,full_own_replay=r.get('replay',{}).get('passed')is True and r.get('own_replay_native')==n and r.get('replay',{}).get('maximum_qpos_qvel_ctrl_mocap_error',1.)<=1e-8)
 segments=json.loads((out/'EXECUTION_SEGMENTS.json').read_text())if(out/'EXECUTION_SEGMENTS.json').exists()else[];cursor=23640;maximum=np.zeros(3);adoptions=[]
 for segment in segments:
  assert segment['start_native']==cursor,'UNCOVERED_NATIVE';count=segment['executed_native'];states=np.asarray(segment['state_path']);assert count<len(states)
  q=z['qpos'][cursor:cursor+count];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));pred=states[1:count+1];err=yaw-pred[:,2];steer=np.array([virtual(row)for row in q[:,setup['steering_qpos_addresses']]])
  if count:maximum=np.maximum(maximum,[np.linalg.norm(q[:,:2]-pred[:,:2],axis=1).max(),abs(np.arctan2(np.sin(err),np.cos(err))).max(),abs(steer-pred[:,6]).max()])
  if segment['kind']=='CERTIFIED_PARKED_HOLD':
   packet=segment['planning_packet'];source=segment['planning_source'];request=np.array(commands)[cursor:cursor+count][:,[1,2,5]];assert np.array_equal(request,np.zeros((count,3))),'PLANNER_TOOK_CONTROL';assert segment['minimum_raw_m']>=REQUIRED
  else:
   plan=json.loads((R/segment['adopted_plan']).read_text());packet=plan['published_packet'];source_check(packet,plan['publication_source']);proposal=json.loads((R/segment['adopted_plan']).with_name('RESULT.json').read_text());assert contained(plan['publication_source']['periodic']['vertices'],proposal['source_planes']);assert 0<=plan['publication_age_s']<=.05
   # Reproduce the actual declared nominal anchor (the planning packet), not
   # a fictitious exact reset at publication. The certified hold and measured
   # <=1mm publication gate bridge the stationary anchor to the latest packet;
   # all subsequent physical errors remain against this saved nominal path.
   ss,uu,rr,mm=predict(setup,plan['planning_packet'],plan['actions'],tail=False);assert abs(ss-states).max()<=1e-8;assert np.array_equal(np.array(commands)[cursor:cursor+count][:,[1,2,5]],rr[:count]);g=Geometry(setup['known'],plan['planning_source']['periodic'],packet['sim_time']);low=g.complete(ss);cc,upper=checks(ss,uu,rr,plan['planning_packet'],setup,np.array(task['goal_xy']),low,REQUIRED);assert all(cc.values()),'PUBLISHED_REMAINDER_NOT_SAFE';adoptions.append(dict(start_native=cursor,whole_native=len(rr),minimum_raw_m=low,goal_upper_m=upper))
  cursor+=count
 coverage=cursor==n;local=bool(maximum[0]<=.04 and maximum[1]<=.035 and maximum[2]<=.015);result=dict(passed=bool(r['passed']and all(safety.values())and coverage and local and r.get('actual_original_goal_reached',False)and r.get('historical_replay_maximum_error',1.)<=1e-8),safety_passed=bool(all(safety.values())and coverage),safety=safety,all_new_native_covered_once=coverage,prediction=dict(position_m=float(maximum[0]),heading_rad=float(maximum[1]),steering_rad=float(maximum[2]),passed=local),full_remainder_adoptions=adoptions,maximum_controller_error=control_error,minimum_actual_clearance_m=float(z['clearance'].min()),models=0,integrations=0);dump(out/'FINAL_INDEPENDENT_AUDIT.json',result);return result
def compare(main,repeat):return legacy.compare(main,repeat)
