"""Saved native-state, control, contact, sensor and refined geometry audit."""
import copy,gzip,hashlib,importlib.abc,importlib.util,json,sys
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v818_tracked_norm_native_probe'
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('SAVED_COMPONENT_AUDIT_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
for p in ['runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','runtime/mk-mini/training/phase14_lidar_depth_nav/envs',
          'experiments/v733_early_low_translation_scan','experiments/v753_coupled_progress_repaired','experiments/v812_soft_global_reference','experiments/v817_tracked_norm_qualification']:
    sys.path.insert(0,str(repo/p))
from independent_norm import radial_lower,static_field
from motion_tracker import Tracker,install_time_gate
from motion_evaluator import check_forecast
from union_belief import future_cells
from exact_footprint import build,pose_values
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from dynamic_scene import Motion
from unseen_prior import set_public_origin
from self_geometry import containment_margin
from types import SimpleNamespace
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(root/'COMPLETION.json')['status']=='DECLARED_NORM_NATIVE_COMPONENT_COMPLETE'
assert all(sha(repo/n)==h for n,h in read(own/'INPUT_FREEZE.json')['files'].items())
pair=repo/'runs/v812_soft_global_reference/main_slot01/paired';cell=pair/'geometry_memory'
protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];base=static_field(protocol)
world=read(cell/'planning_0303.json')['causal_input'];result=read(root/'RESULT.json')
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f][:599]
set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();trackers={}
for p in packets:
    assert packet_equal(p,sensed_packet(p['xy'],p['yaw'],p['time'],p['step'],protocol,motion,noise))
    tracker.update_packet(p,protocol['known_rectangles'],protocol['known_circles'])
    if p['step']in[586,598]:trackers[p['step']]=copy.deepcopy(tracker)
physical=[]
with gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')as f:
    for line in f:
        r=json.loads(line);physical.append(r);b=np.asarray(r['actual_bounds'])
        geometry=SimpleNamespace(**{**base.__dict__,'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(r['time']),.1]])})
        q=np.asarray(r['qpos']);pose=[q[0],q[1],np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
        clearance=float(pose_values(geometry,[pose])[0]);margin=float(containment_margin(b,np.asarray(protocol['footprint_bounds'])))
        assert abs(clearance-r['clearance_m'])<=1e-10 and clearance>=.15 and abs(margin-r['self_margin_m'])<=1e-10 and margin>=0
        assert all(c['contact_type']not in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in r['contacts'])
old=[r for r in physical if r['context']=='OLD_REPLAY'];assert len(old)==4784
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:
    for i,line in enumerate(f):
        if i>=4784:break
        r=json.loads(line);p=old[i]
        assert max(np.max(abs(np.asarray(p['qpos'])-r['qpos_full'])),np.max(abs(np.asarray(p['qvel'])-r['qvel_full'])),np.max(abs(np.asarray(p['ctrl'])-r['actual_ctrl'])),np.max(abs(np.asarray(p['mocap'])-r['mocap_pos'])))<=1e-8
contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate']);ids=contract['ids'];checks=[];coverage_count=0
for row in result['records']:
    step=row['step'];folder=root/f'step{step:04d}';z=np.load(folder/'CERTIFICATE.npz');state=json.loads(str(z['forecast_state']));q=z['qpos'];poses=np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
    original=build(F,world);install_time_gate(original,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
    times=np.arange(1,329)*.01;expected=np.maximum(original.trajectory_values(poses,.01),np.minimum(pose_values(base,poses),radial_lower(base,poses,state,times)))
    error=float(np.max(abs(expected-z['causal_values'])));assert error<=1e-10 and expected.min()>=.155
    margin=float(containment_margin(z['self_bounds'],np.asarray(protocol['footprint_bounds'])).min());assert margin>=.002 and np.linalg.norm(z['qvel'][-1,:2])<=.025
    controls=z['controls'];assert len(controls)==328 and np.all(controls>=limits[:,0]-1e-12)and np.all(controls<=limits[:,1]+1e-12)and np.all(abs(np.diff(controls,axis=0))<=rate+1e-12)
    actual=np.load(folder/'ACTUAL.npz');repeat=np.load(folder/'REPEAT.npz');repeat_error=float(np.max(abs(actual['integration']-repeat['integration'])));assert repeat_error<=1e-8
    observations=[]
    for label in ['ACTUAL','REPEAT']:
        local=copy.deepcopy(trackers[step])
        with gzip.open(folder/(label+'_OBSERVATIONS.json.gz'),'rt')as f:items=json.load(f)
        for item in items:
            p=item['packet'];assert packet_equal(p,sensed_packet(p['xy'],p['yaw'],p['time'],p['step'],protocol,motion,noise))
            _,s=local.update_packet(p,protocol['known_rectangles'],protocol['known_circles']);assert s==item['state']
            assert check_forecast(config,s)['passed'];t=np.arange(657)*.01;lo,hi=future_cells(s['outer_state_cells'],t);truth=np.asarray([motion.xy(s['time']+x)for x in t]);assert np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max()<=1e-7
            cells=np.asarray(s['outer_state_cells']);assert np.maximum(cells[:,0]-truth[0],truth[0]-cells[:,1]).max(axis=1).min()<=1e-7
            assert (np.linalg.norm(truth-truth[0],axis=1)-.08*t).max()<=1e-7;coverage_count+=986
        observations.append(items)
    assert observations[0]==observations[1]
    # Match all qpos/qvel/ctrl/mocap saved actual vectors and contact events
    # against the repeated branch, independently of the full integration array.
    aa=[x for x in physical if x['context']==f'S{step}_ACTUAL'];bb=[x for x in physical if x['context']==f'S{step}_REPEAT'];assert len(aa)==len(bb)==328
    for a,b in zip(aa,bb):
        assert a['contacts']==b['contacts']
        assert max(np.max(abs(np.asarray(a[k])-b[k]))for k in ['qpos','qvel','ctrl','mocap'])<=1e-8
    checks.append(dict(step=step,full_native_geometry_error=error,minimum_refined_causal_m=float(expected.min()),full_integration_state_repeat_error=repeat_error,native_vectors_contacts_and_sensor_repeat_exact=True,passed=True))
assert result['counts']==dict(old_replay_native=4784,private_native=656,component_native=656,component_replay_native=656,new_navigation=0,new_confirmation=0)
out=dict(status='DECLARED_NORM_NATIVE_COMPONENT_EVIDENCE_PASS',records=checks,raw_original_packets=599,original_causal_states_exact=[586,598],actual_and_repeat_329_657_coverage_samples=coverage_count,
    minimum_actual_clearance_m=result['minimum_actual_clearance_m'],maximum_native_state_ctrl_error=result['maximum_native_state_ctrl_error'],counts=result['counts'],models=0,new_integrations=0,full_global_dynamic_passed=False,
    scope='Two fixed old-task complete native brake-only branches. Valid only under declared .08 Euclidean course speed; no claim for broader .12/axis class or full navigation success.')
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
