"""Independent saved-native evidence checks; no vehicle/model import."""
import sys,importlib.abc,gzip,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
paths()
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());from resource_policy import apply
apply()
from science import *
def audit(task):
 out=Path(task['output']);ph=out/'physics';rp=out/'RESULT.json';rp=rp if rp.exists()else ph/'paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text());assert result['passed'];setup=json.loads((ph/'SETUP.json').read_text());z=np.load(ph/'NATIVE_TRACE.npz');cmd=np.asarray(json.loads((ph/'BODY_COMMANDS.json').read_text()));n=len(cmd);hist=18074 if task['kind']=='remaining'else 0;inp=json.loads((out/'ACTUAL_INPUT.json').read_text());pp=np.load(out/'PLAN.npz');rr=requests(task);pred=plan(setup,inp['packet'],inp['source'],rr,task);ss=pred['states'];ctrl=z['ctrl'][:,setup['actuator_ids']];engine=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);ce=0.
 from governor import Adapter as Guarded
 from kernel import load
 from types import SimpleNamespace
 Original=load('v1082_original_signed_audit',R/'experiments/v1035_signed_timed_input_source/signed_control.py').Adapter;engine.adapter.__class__=Original;projection_count=0;max_empirical_speed_upper=0.
 for i,(c,u) in enumerate(zip(cmd,ctrl)):
  if i==hist:engine.adapter.__class__=Guarded
  if i>=hist:
   enc=np.r_[z['qpos'][i-1,setup['steering_qpos_addresses']],z['qvel'][i-1,setup['steering_qvel_addresses']]];engine.adapter.encoders=lambda enc=enc:enc
  rebuilt=engine.adapter.compute(c[1],c[2],c[3],c[4],c[5]);ce=max(ce,float(abs(rebuilt-u).max()))
  if i>=hist and abs(c[1]-.125)<=1e-12:
   gp=engine.adapter.last_speed_projection;projection_count+=gp['limited'];max_empirical_speed_upper=max(max_empirical_speed_upper,gp['offset']+gp['gain']*gp['common']+gp['reserve'])
 q=z['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));forward=z['qvel'][:,0]*np.cos(yaw)+z['qvel'][:,1]*np.sin(yaw);ang=yaw[hist:]-ss[1:,2];maximum=np.array([np.linalg.norm(q[hist:,:2]-ss[1:,:2],axis=1).max(),abs(np.arctan2(np.sin(ang),np.cos(ang))).max(),abs(np.array([virtual(x)for x in q[hist:,setup['steering_qpos_addresses']]])-ss[1:,6]).max()]);limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01
 with gzip.open(ph/'CONTACTS.json.gz','rt')as f:contacts=json.load(f)
 checks=dict(all_native=n==hist+len(rr)==len(q)==result['physical']['root_guard_native_count']==result['physical']['fully_recorded_native'],all_counts=result['new_actual_native']==len(rr)and result['historical_replay_native']==hist,canonical_model=setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8',clearance=float(z['clearance'].min())>=.15-1e-8,full_self=float(z['self_margin'].min())>=-1e-10,contacts_complete=len(contacts)==n+1,no_bad_contact=not any(c[2]in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact']for cs in contacts for c in cs),legal_ctrl=(ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all(),legal_rate=(abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all(),body_caps=abs(forward).max()<=.13 and abs(z['qvel'][:,5]).max()<=.16,control_owner=ce<=1e-10,original_complete_plan=pred['passed']and abs(pp['states']-ss).max()<=1e-8 and abs(pp['controls']-pred['controls']).max()<=1e-8,exact_requests=np.array_equal(cmd[hist:,[1,2,5]],rr)and np.array_equal(pp['requests'],rr),tracking=np.all(maximum<=[.04,.035,.015]),full2200=np.array_equal(cmd[-2200:,[1,2,5]],np.zeros((2200,3))),last328_stopped=np.linalg.norm(z['qvel'][-328:,:2],axis=1).max()<=.03 and abs(z['qvel'][-328:,5]).max()<=.03,clock=abs(z['time']-np.arange(1,n+1)*.01).max()<=1e-7,own_replay=result['own_replay_native']==n and result['replay']['passed']and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and result['replay']['contact_mismatched_ticks']==0)
 checks['speed_projection_upper']=max_empirical_speed_upper<=.129+1e-10;detail={}
 if hist:
  old=np.load(ARCH/'physics/NATIVE_TRACE.npz');he=max(float(abs(z[k][:hist]-old[k]).max())if z[k].size else 0. for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']);hp=json.loads((out/'HISTORICAL_REPLAY_PROOF.json').read_text());discovery=result['physical']['first_actor_detection']['native_tick'];goal=float(np.linalg.norm(q[-1,:2]-task['goal_xy']));distance=float(np.linalg.norm(q[-1,:2]-q[hist-1,:2]));checks.update(exact_history=he<=1e-8 and hp['passed']and hp['range_error']<=1e-6 and hp['contact_mismatched_ticks']==0,normal_discovery=cmd[discovery-1,1]>.005,actual328_brake=np.array_equal(cmd[discovery:discovery+328][:,[1,2,5]],np.zeros((328,3)))and np.linalg.norm(z['qvel'][discovery+327,:2])<=.03,original_causal_source=inp['source']['source_native_tick']==15290 and inp['packet']['native_tick']==18074,actual_goal=goal<=.45,actual_continuation=distance>=1.)
  center=z['mocap_pos'][hist:,0,:2];normals=np.c_[np.cos(np.arange(8)*math.pi/8),np.sin(np.arange(8)*math.pi/8)];tt=z['time'][hist:];basis=np.c_[np.ones(len(tt)),np.sin(.32*tt),np.cos(.32*tt)];violation=-float('inf')
  for i,vertices in enumerate(inp['source']['periodic']['vertices']):
   bounds=basis@np.asarray(vertices).T;actual=center@normals[i];violation=max(violation,float((actual-bounds.max(axis=1)).max()),float((bounds.min(axis=1)-actual).max()))
  checks['offline_actor_domain']=violation<=2e-6;detail=dict(goal_distance_m=goal,continuation_m=distance,historical_error=he,offline_domain_max_violation=violation,first_discovery_native=discovery)
 else:
  front=q[404,setup['steering_qpos_addresses']];progress=float(np.linalg.norm(q[404,:2]-q[279,:2]));checks.update(return_while_moving=abs(front).max()<=.02 and forward[404]>=.10 and progress>=.10,response_motion=np.linalg.norm(q[-1,:2]-np.asarray(inp['packet']['body'][:2]))>=.30);detail=dict(front_at405=front.tolist(),forward_at405=float(forward[404]),moving_return_m=progress)
 checks={k:bool(v)for k,v in checks.items()};a=dict(passed=all(checks.values()),checks=checks,detail=detail,maximum_tracking=maximum.tolist(),control_error=ce,minimum_actual_clearance_m=float(z['clearance'].min()),models=0,integrations=0,new_main_samples=0,actual_projection_count=projection_count,maximum_empirical_next_speed_upper=max_empirical_speed_upper);dump(out/'FINAL_INDEPENDENT_AUDIT.json',a);return a
if __name__=='__main__':
 a=audit(json.loads(Path(sys.argv[1]).read_text()));print(json.dumps(a),flush=True);sys.exit(0 if a['passed']else 1)
