"""Independent full saved physical controls/body/mode/contact/replay audit; zero models."""
import sys,math,gzip
from afternoon_tools import *
import numpy as np
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'));from bindings import Adapter
import kernel
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'));from geometry import Geometry
from source import Engine,initial

def audit(task,save=True,software_root=None):
 software_root=Path(software_root)if software_root is not None else O/'software'
 out=Path(task['output']);r=json.loads((out/'RESULT.json').read_text());s=json.loads((out/'physics/SETUP.json').read_text());d={k:v.copy()for k,v in np.load(out/'physics/NATIVE_TRACE.npz').items()};cmd=json.loads((out/'physics/BODY_COMMANDS.json').read_text());journal=json.loads((out/'MODE_JOURNAL.json').read_text());cert=json.loads((out/'STOP_CERTIFICATES.json').read_text());n=len(d['qpos']);base=20160;reference={k:v.copy()for k,v in np.load(software_root/'SOURCE.npz').items()};rows=json.loads((software_root/'ROWS.json').read_text());p=json.loads((out/'ACTUAL_SAVED_ENTRY.json').read_text());old={k:v.copy()for k,v in np.load(R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/physics/NATIVE_TRACE.npz').items()};histmax=max(float(abs(d[k][:base]-old[k][:base]).max())if d[k][:base].size else 0. for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']);quat=d['qpos'][:,3:7];yaw=np.arctan2(2*(quat[:,0]*quat[:,3]+quat[:,1]*quat[:,2]),1-2*(quat[:,2]**2+quat[:,3]**2));vel=d['qvel'];mv=vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw);lat=-vel[:,0]*np.sin(yaw)+vel[:,1]*np.cos(yaw);ctrl=d['ctrl'][:,s['actuator_ids']];owner=kernel.Predictor(s,dict(state=[0.]*8,last_ctrl=p['controller_memory']['last_ctrl'],integral=p['controller_memory']['integral'],virtual_rate=.6),kernel.PARAMETERS).adapter;owner.__class__=Adapter;owner.virtual_rate=.6;maximum=0.;memory=True;binding=True;schedule=True;envelopes=True;mode_anchor=None;previous=False
 expected=[]
 for target,speed,ticks,mode in rows['rows']:expected.extend([(target,speed,bool(mode))]*int(ticks))
 for i,j in enumerate(journal):
  k=base+i;enc=np.r_[d['qpos'][k-1,s['steering_qpos_addresses']],vel[k-1,s['steering_qvel_addresses']]];owner.encoders=lambda enc=enc:enc.copy();memory&=bool(abs(owner.last-j['last_ctrl']).max()<=1e-10 and abs(owner.integral-j['integral'])<=1e-10);owner.parked_target=j['target']if j['mode']else None;_,vr,wr,bv,bw,stale=cmd[k];binding&=bool(j['native']==k and abs(mv[k-1]-bv)<=1e-10 and abs(vel[k-1,5]-bw)<=1e-10);u=owner.compute(vr,wr,bv,bw,bool(stale));maximum=max(maximum,float(abs(u-ctrl[k]).max()))
  if j['component_index']is not None:schedule&=bool(j['component_index']==i and i<len(expected)and(j['target'],j['speed'],j['mode'])==expected[i]and vr==j['speed']and abs(wr-(0. if j['mode']or vr==0 else vr*math.tan(j['target'])/.6))<1e-12)
  else:schedule&=bool(j['phase']=='failure_stop'and vr==wr==0 and not j['mode'])
  if j['mode']and not previous:mode_anchor=np.r_[d['qpos'][k-1,:2],yaw[k-1]]
  if abs(vr)>=.005:mode_anchor=None
  if mode_anchor is not None:envelopes&=bool(np.linalg.norm(d['qpos'][k,:2]-mode_anchor[:2])<=.02 and abs(math.atan2(math.sin(yaw[k]-mode_anchor[2]),math.cos(yaw[k]-mode_anchor[2])))<=.1)
  if j['mode']:envelopes&=bool(np.array_equal(ctrl[k,2:],np.zeros(2))and abs(mv[k])<=.01)
  previous=j['mode']
 poses=np.c_[d['qpos'][:,:2],yaw];static=kernel.ref._old.Geometry(s['known'],None).clearances(poses)[0];limits=np.asarray(s['limits']);rates=np.asarray(s['slew_per_second'])*.01;new=n-base;response=np.array([np.inf]*3)
 if new==len(reference['controls']):
  angles=yaw[base:]-reference['states'][1:,2];steer=np.array([kernel.virtual(q)for q in d['qpos'][base:,s['steering_qpos_addresses']]]);response=np.array([np.linalg.norm(d['qpos'][base:,:2]-reference['states'][1:,:2],axis=1).max(),abs(np.arctan2(np.sin(angles),np.cos(angles))).max(),abs(steer-reference['states'][1:,6]).max()])
 checks={'history_exact':histmax<=1e-8,'native_lengths':n==len(cmd)==r['new_actual_native']==r['physical']['root_guard_native_count']and new==len(journal),'all_controls_reconstructed':maximum<=1e-10 and memory,'all_actual_feedback_bound':binding,'fixed_source_schedule':schedule,'mode_envelopes':envelopes,'all_body_caps':bool((abs(mv)<=.13).all()and(abs(lat)<=.03).all()and(abs(vel[:,5])<=.16).all()),'static_full_body':float(static.min())>=.15-1e-8,'actual_clearance':float(d['clearance'].min())>=.15-1e-8,'self_containment':float(d['self_margin'].min())>=-1e-10,'bad_contacts_zero':r['physical']['bad_contacts']==0,'legal_ctrl':bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),'legal_slew':bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all()),'complete2200_tail':len(cmd)>=2200 and all(c[1]==c[2]==0. for c in cmd[-2200:])and bool(np.linalg.norm(vel[-50:,:2],axis=1).max()<=.003 and abs(vel[-50:,5]).max()<=.003 and abs(vel[-50:,s['steering_qvel_addresses']]).max()<=.015),'complete_replay':r.get('replay',{}).get('passed')is True and r['own_replay_native']==n,'all_current_and_prospective_stop_certificates':bool(cert and all(c['current']['passed']and c['prospective']['passed']for c in cert)),'complete_response':bool(new==14700 and np.all(response<=[.04,.035,.015])),'component_original_goal_separate':r.get('original_goal_reached')is False,'fresh_actual_observations':r.get('actual_new_observations',0)>0}
 # On real evidence, reconstruct every current/prospective stop from recorded actual packets.
 reconstruction_count=0;reconstruction_native=0
 if save:
  origin=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());tab=np.load(R/'runs/v1135_causal_batch/domain/JOINT_TABLE.npz');g=Geometry(origin,{k:tab[k]for k in ['bounds','centers']});engine=Engine(s);reconstructed=True
  from observer_worker import front
  from source import remaining_rows
  for c in cert:
   assert remaining()>5,'INDEPENDENT_AUDIT_DEADLINE';packet=c['packet'];idx=c['offset'];native=base+idx;actual=np.r_[d['qpos'][native-1,:2],yaw[native-1]];reconstructed&=bool(np.linalg.norm(np.array(packet['body'][:2])-actual[:2])<=1e-10 and abs(math.atan2(math.sin(packet['body'][2]-actual[2]),math.cos(packet['body'][2]-actual[2])))<=1e-10 and packet['native_tick']==native)
   block=front(remaining_rows(rows['rows'],idx),c['count'])
   for key,schedule in [('current',[(0.,0.,2200,0)]),('prospective',[*block,(0.,0.,2200,0)])]:
    ss,uu=engine.simulate(initial(packet),schedule);proof,_=g.final(dict(origin,packet=packet,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,schedule);reconstructed&=bool(proof['passed']==c[key]['passed']and proof['states_sha256']==c[key]['states_sha256']and proof['controls_sha256']==c[key]['controls_sha256']);reconstruction_count+=1
  reconstruction_native=engine.native;checks['all_stop_proofs_independently_reconstructed']=reconstructed
 result={'passed':bool(r['passed']and all(checks.values())),'checks':checks,'maximum_historical_state_error':histmax,'maximum_controller_error':maximum,'maximum_response_errors':response.tolist(),'physical_native':n,'historical_reconstruction_native':base,'new_component_native':new,'models':0,'physical_integrations':0,'analytical_dynamics_integrations':reconstruction_native,'stop_certificates_reconstructed':reconstruction_count,'not_original_goal_or_dynamic_acceptance':True}
 if save:dump(out/'FINAL_INDEPENDENT_AUDIT.json',result)
 return result
if __name__=='__main__':
 result=audit(json.loads(Path(sys.argv[1]).read_text()));print(encode(result));sys.exit(0 if result['passed']else 1)
