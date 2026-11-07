"""Independent persisted component geometry, original calibration, physical/repeat audit."""
import importlib.abc,importlib.util,gzip
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('ZERO_MODEL_AUDIT')
import sys
sys.meta_path.insert(0,NoModels())
from helpers import *
from independent_norm import static_field,radial_lower
from exact_footprint import pose_values
from self_geometry import containment_margin
from dynamic_scene import Motion
from motion_tracker import Tracker
from motion_evaluator import check_forecast
from union_belief import future_cells
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
from unseen_prior import set_public_origin
result=read(root/'RESULT.json');assert read(root/'COMPLETION.json')['status']=='EARLY_JOINT_COMPONENT_EVALUATED'
entries=read(own/'FIXED_INPUTS.json');protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);base=static_field(protocol);bounds=np.asarray(protocol['footprint_bounds']);noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();trackers={};states={e['step']:e['state']for e in entries};packets=0
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:
 for packet in map(json.loads,f):
  if packet['step']>295:break
  assert packet_equal(packet,sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,noise));_,state=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);packets+=1
  if packet['step']in states:assert state==states[packet['step']];trackers[packet['step']]=copy.deepcopy(tracker)
assert packets==296
physical=list(map(json.loads,gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')));old=[x for x in physical if x['context']=='OLD_REPLAY'];assert len(old)==2360
contacts={}
with gzip.open(cell/'contacts.jsonl.gz','rt')as f:
 for c in map(json.loads,f):
  if c['physics_step']>2360:break
  contacts.setdefault(c['physics_step'],[]).append(c)
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:
 for i,line in enumerate(f):
  if i>=2360:break
  x=json.loads(line);a=old[i];assert max(np.max(abs(np.asarray(a[k])-x[v]))for k,v in [('qpos','qpos_full'),('qvel','qvel_full'),('ctrl','actual_ctrl'),('mocap','mocap_pos')])<=1e-8
  assert a['contacts']==contacts.get(i+1,[])
for a in physical:
 box=np.asarray(a['actual_bounds']);geometry=SimpleNamespace(**{**base.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(a['time']),.1]])});clearance=float(pose_values(geometry,poses(a['qpos']))[0]);margin=float(containment_margin(box,bounds));assert clearance>=.15 and abs(clearance-a['clearance_m'])<=1e-10 and margin>=0 and abs(margin-a['self_margin_m'])<=1e-10
 assert all(c['contact_type']not in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in a['contacts'])
spec=importlib.util.spec_from_file_location('original_broad',repo/'experiments/v812_soft_global_reference/motion_tracker.py');broad=importlib.util.module_from_spec(spec);spec.loader.exec_module(broad)
def values(poses0,state):
 f=SimpleNamespace(**base.__dict__);broad.install_time_gate(f,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);clock=np.arange(1,len(poses0)+1)*.01
 return np.maximum(f.causal_values_at_times(poses0,clock),np.minimum(pose_values(base,poses0),radial_lower(base,poses0,state,clock)))
contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate']);ids=contract['ids'];private=0;rows=[];coverage_count=0
from reference_certificate_audit import check_successor,expected_follow
for entry,row in zip(entries,result['records']):
 step=entry['step'];assert row['step']==step;folder=root/f'step{step:04d}';event=json.loads((folder/'early_joint_decisions.jsonl').read_text())
 from early_joint_independent import check
 check(folder,event,entry['nominal']['candidates'],protocol,deep=True,source_cell=cell)
 for a in event['probes']:
  private+=8+328*len(a['detail']['candidates'])
  for c in a['detail']['candidates']:
   z=np.load(folder/c['full_forecast_file']);v=values(z['poses'],entry['state']);assert len(v)==336
   margin=min(a['detail']['prefix_self_domain_margin_m'],float(containment_margin(z['self_bounds'][:321],bounds).min()));speed=float(np.linalg.norm(z['qvel'][319,:2]));extra_margin=float(containment_margin(z['self_bounds'],bounds).min());extra_speed=float(np.linalg.norm(z['qvel'][-1,:2]));gain=float(np.linalg.norm(np.asarray(event['real_qpos'])[:2]-protocol['goal_xy'])-np.linalg.norm(z['qpos'][319,:2]-protocol['goal_xy']))
   assert max(abs(margin-c['self_domain_margin_m']),abs(speed-c['terminal_speed_m_s']),abs(gain-c['joint_goal_gain_m']))<=1e-8
   reason='TIME_CLEARANCE'if v[:328].min()<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'SUCCESSOR_CLEARANCE'if v.min()<.155 else'SUCCESSOR_SELF'if extra_margin<.002 else'SUCCESSOR_TERMINAL_SPEED'if extra_speed>.025 else'INSUFFICIENT_REVERSE'if c['kind']=='REVERSE_BRAKE'and c['signed_displacement_m']>-.02 else'INSUFFICIENT_FORWARD'if c['kind']in('FORWARD_BRAKE','REFERENCE_FOLLOW_BRAKE')and c['signed_displacement_m']<.02 else'PROACTIVE_NO_GOAL_PROGRESS'if gain<.02 else None
   assert reason==c['reason'],(step,a['rank'],c['kind'],reason,c['reason'])
   assert np.array_equal(z['controls'][:8],np.repeat([a['first_command']],8,axis=0))and np.all(z['controls']>=limits[:,0]-1e-12)and np.all(z['controls']<=limits[:,1]+1e-12)and np.all(abs(np.diff(z['controls'][::8],axis=0))<=rate+1e-12)

 if not row['component_executed']:
  assert event['selected_rank']is None;rows.append(dict(step=step,qualified=False));continue
 selected=read(folder/'SELECTED.json');cache=selected['cache'];assert event['selected_rank']==selected['proposal']['rank']
 check_successor(cache,protocol,limits,rate)
 z=np.load(folder/'CERTIFICATE.npz');p=poses(z['qpos']);v=values(p,entry['state']);assert len(p)==336 and np.max(abs(v-z['causal_values']))<=1e-8 and v.min()>=.155
 assert containment_margin(z['self_bounds'],bounds).min()>=.002 and np.linalg.norm(z['qvel'][-1,:2])<=.025
 expected_controls=np.vstack((np.repeat([selected['proposal']['command']],8,axis=0),cache['controls'],cache['one_cycle_continuation']['extra_controls']))
 assert np.array_equal(z['controls'],expected_controls)and np.all(abs(z['controls'][0]-z['initial_ctrl'][ids])<=rate+1e-12)
 goal_gain=float(np.linalg.norm(z['initial_qpos'][:2]-protocol['goal_xy'])-np.linalg.norm(z['qpos'][-1,:2]-protocol['goal_xy']));assert abs(goal_gain-row['complete_goal_progress_m'])<=1e-10 and goal_gain>=.02 and row['qualified']==(goal_gain>=.02)
 aa=np.load(folder/'ACTUAL.npz');bb=np.load(folder/'REPEAT.npz');assert np.max(abs(aa['integration']-bb['integration']))<=1e-8
 actual=[x for x in physical if x['context']==f'S{step}_ACTUAL'];repeat=[x for x in physical if x['context']==f'S{step}_REPEAT'];assert len(actual)==len(repeat)==336
 for tick,(a,b)in enumerate(zip(actual,repeat)):
  assert a['contacts']==b['contacts']and max(np.max(abs(np.asarray(a[k])-b[k]))for k in['qpos','qvel','ctrl','mocap'])<=1e-8
  assert max(np.max(abs(np.asarray(a['qpos'])-z['qpos'][tick])),np.max(abs(np.asarray(a['qvel'])-z['qvel'][tick])),np.max(abs(np.asarray(a['ctrl'])[ids]-z['controls'][tick])))<=1e-8
 observations=[]
 for label in['ACTUAL','REPEAT']:
  local=copy.deepcopy(trackers[step]);items=json.load(gzip.open(folder/(label+'_OBSERVATIONS.json.gz'),'rt'))
  for item in items:
   packet=item['packet'];assert packet_equal(packet,sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,noise));_,state=local.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);assert state==item['state']and check_forecast(config,state)['passed'];times=np.arange(657)*.01;lo,hi=future_cells(state['outer_state_cells'],times);truth=np.asarray([motion.xy(state['time']+t)for t in times]);assert np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max()<=1e-7 and(np.linalg.norm(truth-truth[0],axis=1)-.08*times).max()<=1e-7;coverage_count+=986
  observations.append(items)
 assert observations[0]==observations[1]
 rows.append(dict(step=step,qualified=row['qualified'],minimum_causal_clearance_m=float(v.min()),complete_goal_progress_m=goal_gain,full_native_repeat_error=0.))
assert len(rows)==len(entries)==1 and private==result['counts']['private_native']<=200000
executed=sum(x['component_executed']for x in result['records']);assert result['counts']['old_replay_native']==2360 and result['counts']['component_native']==result['counts']['component_repeat_native']==336*executed
freeze=read(own/'INPUT_FREEZE.json')['files'];assert all(sha(repo/n)==h for n,h in freeze.items())
out=dict(status='EARLY_JOINT_FIXED_NATIVE_INDEPENDENT_PASS',component_passed=any(x['qualified']for x in rows),records=rows,counts=result['counts'],minimum_actual_clearance_m=result['minimum_actual_clearance_m'],maximum_native_state_ctrl_error=result['maximum_native_state_ctrl_error'],actual_and_repeat_329_657_samples=coverage_count,new_models=0,new_integrations=0)
dump(root/'FINAL_INDEPENDENT_AUDIT.json',out);print(json.dumps(out))
