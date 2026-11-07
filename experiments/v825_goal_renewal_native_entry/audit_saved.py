"""Independent saved native, causal, control and norm checks; no models."""
import copy,gzip,importlib.abc,importlib.util,json,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('SAVED_AUDIT_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
from helpers import *
from exact_footprint import build,pose_values
from independent_norm import radial_lower,static_field
from motion_tracker import Tracker
from motion_evaluator import check_forecast
from union_belief import future_cells
from dynamic_scene import Motion
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from self_geometry import containment_margin
from unseen_prior import set_public_origin
root=repo/'runs/v825_goal_renewal_native_entry';result=read(root/'RESULT.json')
assert read(root/'COMPLETION.json')['status']=='GOAL_REFERENCE_COMPONENTS_EVALUATED'
protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);base=static_field(protocol)
noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();trackers={}
traces,states,decisions,routes=fixed_inputs()
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:
 for packet in map(json.loads,f):
  if packet['step']>500:break
  assert packet_equal(packet,sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,noise))
  _,state=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles'])
  if packet['step']in(282,500):assert state==states[packet['step']];trackers[packet['step']]=copy.deepcopy(tracker)
physical=[]
with gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')as f:
 for record in map(json.loads,f):
  physical.append(record);b=np.asarray(record['actual_bounds']);geometry=SimpleNamespace(**{**base.__dict__,'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(record['time']),.1]])})
  clearance=float(pose_values(geometry,[pose(record['qpos'])])[0]);margin=float(containment_margin(b,np.asarray(protocol['footprint_bounds'])))
  assert abs(clearance-record['clearance_m'])<=1e-10 and clearance>=.15 and abs(margin-record['self_margin_m'])<=1e-10 and margin>=0
  assert all(c['contact_type']not in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in record['contacts'])
old=[r for r in physical if r['context']=='OLD_REPLAY'];assert len(old)==4000
original_contacts={}
with gzip.open(cell/'contacts.jsonl.gz','rt')as f:
 for event in map(json.loads,f):
  if event['physics_step']>4000:break
  original_contacts.setdefault(event['physics_step'],[]).append(event)
for i,record in enumerate(old):assert record['contacts']==original_contacts.get(i+1,[]),'ORIGINAL_NATIVE_CONTACT_EVENTS_DIFFERED'
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:
 for i,line in enumerate(f):
  if i>=4000:break
  r=json.loads(line);p=old[i]
  assert max(np.max(abs(np.asarray(p['qpos'])-r['qpos_full'])),np.max(abs(np.asarray(p['qvel'])-r['qvel_full'])),np.max(abs(np.asarray(p['ctrl'])-r['actual_ctrl'])),np.max(abs(np.asarray(p['mocap'])-r['mocap_pos'])))<=1e-8
spec=importlib.util.spec_from_file_location('unrefined_original',repo/'experiments/v812_soft_global_reference/motion_tracker.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate']);ids=contract['ids'];checks=[];coverage_count=0
for row in result['records']:
 step=row['step'];folder=root/f'step{step:04d}'
 assert row['old_first_command_and_score_match'] and row['old_nominal_maximum_pose_error']<=1e-8
 if not row['component_executed']:
  checks.append(dict(step=step,component_qualified=False,evidence_preserved=True));continue
 z=np.load(folder/'CERTIFICATE.npz');state=json.loads(str(z['forecast_state']));p=poses(z['qpos']);world=copy.deepcopy(read(cell/'planning_0265.json')['causal_input']);world['rectangles']=[*protocol['known_rectangles'],state['current_outer_rectangle']]
 field=build(F,world);original.install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);t=np.arange(1,329)*.01
 expected=np.maximum(field.causal_values_at_times(p,t),np.minimum(pose_values(base,p),radial_lower(base,p,state,t)))
 error=float(np.max(abs(expected-z['causal_values'])));assert error<=1e-10 and expected.min()>=.155
 assert containment_margin(z['self_bounds'],np.asarray(protocol['footprint_bounds'])).min()>=.002 and np.linalg.norm(z['qvel'][-1,:2])<=.025
 controls=z['controls'];assert len(controls)==328 and np.all(controls>=limits[:,0]-1e-12)and np.all(controls<=limits[:,1]+1e-12)and np.all(abs(np.diff(controls,axis=0))<=rate+1e-12)
 assert np.all(abs(controls[0]-z['initial_ctrl'][ids])<=rate+1e-12)
 reference,source=new_reference(step);assert np.array_equal(reference,z['reference'])
 current=pose(z['initial_qpos']);assert np.max(abs(current-reference[0,:3]))<=1e-8 and np.linalg.norm(reference[-1,:2]-protocol['goal_xy'])<.28
 prefix_gain=float(np.linalg.norm(current[:2]-protocol['goal_xy'])-np.linalg.norm(z['qpos'][7,:2]-protocol['goal_xy']));assert prefix_gain>0 and abs(prefix_gain-row['prefix8_target_progress_m'])<=1e-10
 a=np.load(folder/'ACTUAL.npz');b=np.load(folder/'REPEAT.npz');repeat_error=float(np.max(abs(a['integration']-b['integration'])));assert repeat_error<=1e-8
 observations=[]
 for label in['ACTUAL','REPEAT']:
  local=copy.deepcopy(trackers[step]);items=json.load(gzip.open(folder/(label+'_OBSERVATIONS.json.gz'),'rt'))
  for item in items:
   packet=item['packet'];assert packet_equal(packet,sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,noise))
   _,s=local.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);assert s==item['state'];assert check_forecast(config,s)['passed']
   times=np.arange(657)*.01;lo,hi=future_cells(s['outer_state_cells'],times);truth=np.asarray([motion.xy(s['time']+x)for x in times]);assert np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max()<=1e-7
   assert (np.linalg.norm(truth-truth[0],axis=1)-.08*times).max()<=1e-7;coverage_count+=986
  observations.append(items)
 assert observations[0]==observations[1]
 aa=[r for r in physical if r['context']==f'S{step}_ACTUAL'];bb=[r for r in physical if r['context']==f'S{step}_REPEAT'];assert len(aa)==len(bb)==328
 for tick,(actual,repeated)in enumerate(zip(aa,bb)):
  assert actual['contacts']==repeated['contacts']
  assert max(np.max(abs(np.asarray(actual[k])-repeated[k]))for k in['qpos','qvel','ctrl','mocap'])<=1e-8
  assert max(np.max(abs(np.asarray(actual['qpos'])-z['qpos'][tick])),np.max(abs(np.asarray(actual['qvel'])-z['qvel'][tick])),np.max(abs(np.asarray(actual['ctrl'])[ids]-controls[tick])))<=1e-8
 checks.append(dict(step=step,component_qualified=True,full_native_geometry_error=error,minimum_causal_m=float(expected.min()),full_integration_repeat_error=repeat_error,prefix8_target_progress_m=prefix_gain,complete328_target_progress_m=row['complete328_target_progress_m'],native_vectors_contacts_packets_exact=True))
executed=sum(r['component_executed']for r in result['records']);counts=result['counts']
assert counts['old_replay_native']==4000 and counts['component_native']==counts['component_repeat_native']==328*executed and counts['private_native']<=360400 and counts['new_navigation']==counts['new_confirmation']==0
freeze=read(Path(__file__).parent/'INPUT_FREEZE.json')['files'];assert all(sha(repo/p)==h for p,h in freeze.items())
out=dict(status='SAVED_REFERENCE_COMPONENT_EVIDENCE_PASS',records=checks,primary282_native_qualified=checks[0]['component_qualified'],raw_original_packets=501,actual_and_repeat_329_657_coverage_samples=coverage_count,counts=counts,minimum_actual_clearance_m=result['minimum_actual_clearance_m'],maximum_native_state_ctrl_error=result['maximum_native_state_ctrl_error'],models=0,new_integrations=0,full_global_dynamic_passed=False)
dump(root/'FINAL_INDEPENDENT_AUDIT.json',out);print(json.dumps(out))
