"""Independent saved full-tail, selection and actual join audit; no integration."""
import argparse,gzip,json,sys
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo/'runs/v771_audit_dependencies/site'))
from independent_domain import IndependentDomain
from exact_footprint import pose_values
from motion_tracker import install_time_gate
from self_geometry import containment_margin
from renewal_state import encode
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();root=Path(a.paired);cell=root/'geometry_memory';read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(x)for x in p.read_text().splitlines()]
protocol=read(root/'STATIC_PROTOCOL.json');b=np.asarray(protocol['footprint_bounds']);states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')};execution=lines(cell/'v648_execution.jsonl');ctr=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');ids=ctr['ids'];limits=np.asarray(ctr['limits']);rate=np.asarray(ctr['rate']);records=[];native=[]
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:native=[json.loads(x)for x in f]
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(x)for x in f]
state_checks=[states[packet['step']]['mode']=='NO_ACTORS_DECLARED' and states[packet['step']]['unknown_actor_count']==0 and states[packet['step']]['center']is None for packet in packets]
checks={'declared_no_dynamic_domain':all(state_checks),'full_native_replay':read(root/'NATIVE_REPLAY_AUDIT.json')['maximum_full_native_state_ctrl_error']<=1e-8}
certs={}
for f in (cell/'recovery_contracts').glob('*.gz'):
 with gzip.open(f,'rt')as stream:c=json.load(stream)
 certs[c['created_step']]=c
for f in sorted((cell/'retained_reentry').glob('step????.json')):
 x=read(f);step=x['step'];state=states[step];assert {k:v for k,v in state.items()if k!='step'}==x['forecast_state'] and state['step']==step and step%4==0 and state['center']is None and not x['hidden_world_geometry_used']
 field=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));field.pose_values=MethodType(pose_values,field);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
 eligible=[];local=[]
 for i,c in enumerate(x['records']):
  z=np.load(cell/'retained_reentry'/(c['label']+'.npz'));target=np.asarray(c['target']);mean=[0,1,2][i//5];diff=[-6,-3,0,3,6][i%5];assert np.array_equal(target,[0,0,mean+diff,mean-diff])
  assert np.max(abs(z['initial_qpos']-x['real_entry_qpos']))<=1e-8 and np.max(abs(z['initial_qvel']-x['real_entry_qvel']))<=1e-8 and abs(float(z['initial_time'])-x['time'])<=1e-10
  command=z['initial_ctrl'].copy();schedule=[command.copy()for _ in range(8)]
  for tick in range(0,320,8):
   desired=target.copy()
   if tick>=160:desired[2:]=0
   command=np.clip(np.clip(desired,limits[:,0],limits[:,1]),command-rate,command+rate);schedule.extend([command.copy()for _ in range(8)])
  assert np.array_equal(z['controls'],schedule)
  q=z['qpos'];v=z['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));traj=np.c_[q[:,:2],yaw];assert np.array_equal(traj,z['poses'])
  minimum=float(field.trajectory_values(traj,.01).min());margin=float(containment_margin(z['self_bounds'],b).min());speed=float(np.linalg.norm(v[-1,:2]));angular=float(np.linalg.norm(v[-1,3:6]));progress=float(np.linalg.norm(z['initial_qpos'][:2]-protocol['goal_xy'])-np.linalg.norm(q[-1,:2]-protocol['goal_xy']))
  assert max(abs(minimum-c['minimum_causal_clearance_m']),abs(margin-c['self_margin_m']),abs(speed-c['terminal_speed_m_s']),abs(angular-c['terminal_angular_speed_rad_s']),abs(progress-c['goal_progress_m']))<=1e-8
  reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else None
  assert reason==c['reason']
  if reason is None and mean>=1 and progress>=.05:eligible.append((progress,i))
  local.append(dict(index=i,minimum=minimum,progress=progress,reason=reason))
 selected=max(eligible,key=lambda t:(t[0],-t[1]))[1]if eligible else None;assert selected==x['selected_index'] and len(local)==15 and x['private_integrations']==4920
 old=certs[x['old_created_step']];cursor=x['old_native_cursor'];oq=old['initial_qpos']if cursor==0 else old['qpos'][cursor-1];ov=old['initial_qvel']if cursor==0 else old['qvel'][cursor-1];prev=protocol['start_qpos']if step==0 else execution[step-1]['qpos_full'];assert max(np.max(abs(np.asarray(oq)-x['real_entry_qpos'])),np.max(abs(np.asarray(ov)-x['real_entry_qvel'])),np.max(abs(np.asarray(prev)-x['real_entry_qpos'])))<=1e-8 and abs(old['start_time']+cursor*.01-x['time'])<=1e-8
 if selected is not None:
  z=np.load(cell/'retained_reentry'/(x['records'][selected]['label']+'.npz'));commit=read(cell/'retained_reentry'/f'step{step:04d}_committed.json');new=certs[step];assert commit['real_state_writes']==0 and commit['actual_prefix_native']==8 and commit['new_remaining_native']==320
  for j in range(8):
   nr=native[step*8+j];assert max(np.max(abs(np.asarray(nr['qpos_full'])-z['qpos'][j])),np.max(abs(np.asarray(nr['qvel_full'])-z['qvel'][j])),np.max(abs(np.asarray(nr['actual_ctrl'])[ids]-z['controls'][j])))<=1e-8
  assert np.array_equal(new['qpos'],z['qpos'][8:])and np.array_equal(new['qvel'],z['qvel'][8:])and np.array_equal(new['controls'],z['controls'][8:])
 records.append(dict(step=step,selected_index=selected,candidates=local,old_join_checked=True,new_prefix_and_cache_checked=selected is not None))
r=read(cell/'result.json');checks.update(all_decisions_checked=len(records)==r['retained_reentry_attempts'],all_commits_checked=sum(x['selected_index']is not None for x in records)==r['retained_reentry_successes'],exact_private_account=4920*len(records)==r['retained_reentry_private_native'])
out=dict(status='GLOBAL_REENTRY_SAVED_EVIDENCE_VERIFIED'if all(checks.values())else'FAIL',checks=checks,records=records,zero_integrations=True);(root/'REENTRY_INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status'],attempts=len(records),commits=r['retained_reentry_successes'])));assert all(checks.values())
