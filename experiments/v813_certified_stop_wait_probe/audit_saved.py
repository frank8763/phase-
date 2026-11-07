"""Independent saved-evidence audit; imports/constructs no physics models."""
import copy, gzip, hashlib, importlib.abc, importlib.util, json, sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np

own=Path(__file__).parent;repo=own.parents[1];root=repo/'runs/v813_certified_stop_wait_probe/physical'
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,*args):
        if fullname=='mujoco' or fullname.startswith('mujoco.'):
            raise RuntimeError('INDEPENDENT_SAVED_AUDIT_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
for p in ['runtime/mk-mini/training/phase14_lidar_depth_nav/envs',
          'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1',
          'experiments/v733_early_low_translation_scan',
          'experiments/v753_coupled_progress_repaired',
          'experiments/v812_soft_global_reference']:
    sys.path.insert(0,str(repo/p))
from motion_tracker import Tracker, install_time_gate
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from dynamic_scene import Motion
from exact_footprint import build,pose_values
from self_geometry import containment_margin
from unseen_prior import set_public_origin
from union_belief import future_cells
from motion_evaluator import check_forecast

read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
completion=read(root/'COMPLETION.json');assert completion['status']in['FIXED_STOP_WAIT_COMPONENT_QUALIFIED','FIXED_STOP_WAIT_COMPONENT_NOT_QUALIFIED']
result=read(root/'RESULT.json');pair=repo/'runs/v812_soft_global_reference/main_slot01/paired';cell=pair/'geometry_memory'
protocol=read(pair/'STATIC_PROTOCOL.json');motion=Motion(read(pair/'DYNAMIC_PROTOCOL.json'));noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
world=read(cell/'planning_0303.json')['causal_input'];bounds=np.asarray(protocol['footprint_bounds']);static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
def poses(q):
    q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f][:587]
set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();trackers={}
for p in packets:
    tracker.update_packet(p,protocol['known_rectangles'],protocol['known_circles'])
    if p['step']in[402,586]:trackers[p['step']]=copy.deepcopy(tracker)
physical_rows=[]
with gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')as f:
    for line in f:
        r=json.loads(line);physical_rows.append(r)
        box=np.asarray(r['actual_bounds']);truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(r['time']),.1]])})
        value=float(pose_values(truth,poses(np.asarray(r['qpos'])[None]))[0])
        assert abs(value-r['clearance_m'])<=1e-10 and value>=.15
        assert abs(float(containment_margin(box,bounds))-r['self_margin_m'])<=1e-10 and r['self_margin_m']>=0
        assert all(c['contact_type']not in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in r['contacts'])
old_native=[]
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:
    for i,line in enumerate(f):
        if i>=4688:break
        old_native.append(json.loads(line))
old_rows=[r for r in physical_rows if r['context']=='ORIGINAL_REPLAY'];assert len(old_rows)==4688
for actual,old in zip(old_rows,old_native):
    assert max(np.max(abs(np.asarray(actual['qpos'])-old['qpos_full'])),np.max(abs(np.asarray(actual['qvel'])-old['qvel_full'])),np.max(abs(np.asarray(actual['ctrl'])-old['actual_ctrl'])),np.max(abs(np.asarray(actual['mocap'])-old['mocap_pos'])))<=1e-8
rows=[];certificates=0;coverage_samples=0;branch_total=0;maximum=0.
contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');ids=contract['ids'];limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate'])
for record in result['records']:
    checkpoint=record['checkpoint'];branch=root/f'checkpoint_{checkpoint}';local=copy.deepcopy(trackers[checkpoint])
    with gzip.open(branch/'OBSERVATIONS.json.gz','rt')as f:observations=json.load(f)
    for item in observations[1:]:
        p=item['packet'];assert packet_equal(p,sensed_packet(p['xy'],p['yaw'],p['time'],p['step'],protocol,motion,noise))
        _,state=local.update_packet(p,protocol['known_rectangles'],protocol['known_circles']);assert state==item['state'],'BRANCH_CAUSAL_STATE_MISMATCH'
        assert check_forecast(motion.config,state)['passed']
        times=np.arange(657)*.01;lo,hi=future_cells(state['outer_state_cells'],times);truth=np.asarray([motion.xy(state['time']+t)for t in times]);assert np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max()<=1e-7
        coverage_samples+=986
    z=np.load(branch/'FULL_BRANCH.npz');n=len(z['controls']);branch_total+=n
    err=float(np.max(abs(z['integration']-z['replay_integration'])));maximum=max(maximum,err);assert err<=1e-8
    applied=z['controls'][:,ids];assert np.all(applied>=limits[:,0]-1e-12) and np.all(applied<=limits[:,1]+1e-12)
    assert np.all(abs(np.diff(applied,axis=0))<=rate+1e-12),'ACTUATOR_RATE_INVALID'
    for check in record['admission_checks']:
        if not check['brake_only_accepted']:continue
        certificate=np.load(root/check['certificate_file']);state=json.loads(str(certificate['forecast_state']))
        w=copy.deepcopy(world);w['sensor_points']=[];w['circles']=protocol['known_circles'];w['rectangles']=[*protocol['known_rectangles'],state['current_outer_rectangle']]
        field=build(F,w);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
        values=field.trajectory_values(poses(certificate['qpos']),.01);margin=float(containment_margin(certificate['self_bounds'],bounds).min())
        assert len(values)==328 and values.min()>=.155 and margin>=.002
        assert abs(float(values.min())-float(certificate['minimum']))<=1e-8
        assert np.linalg.norm(certificate['qvel'][-1,:2])<=.025
        assert check['summary']['recovery_kind']=='BRAKE_ONLY';certificates+=1
    # Independent functional recomputation from the actual saved terminal pose.
    contexts=[r for r in physical_rows if r['context']==f'STOP_WAIT_{checkpoint}']
    goal=np.asarray(protocol['goal_xy']);terminal=float(np.linalg.norm(np.asarray(contexts[-1]['qpos'])[:2]-goal))
    stopped=float(np.linalg.norm(np.asarray(contexts[319]['qpos'])[:2]-goal));speed=float(np.linalg.norm(np.asarray(contexts[-1]['qvel'])[:2]))
    qualified=bool(record['resume_public_steps']>0 and stopped-terminal>=.30 and speed<=.025)
    assert abs(terminal-record['terminal_goal_m'])<=1e-10 and qualified==record['component_qualified']
    assert sum(c['native_ticks']for c in record['chunks'])==n==record['physical_native']
    rows.append(dict(checkpoint=checkpoint,component_qualified=qualified,actual_native=n,terminal_goal_m=terminal,resumed_goal_progress_m=stopped-terminal,terminal_speed_m_s=speed,full_state_replay_error=err))
assert len(rows)==2 and branch_total==result['counts']['branch_native']==result['counts']['branch_replay'] and branch_total<=3232
assert result['counts']['original_replay']==4688 and result['counts']['private_native']<=3000000
assert (result['status']=='FIXED_STOP_WAIT_COMPONENT_QUALIFIED')==all(r['component_qualified']for r in rows)
assert result['full_global_dynamic_passed']is False and result['new_global_navigation']==0
audit=dict(status='FIXED_STOP_WAIT_ALL_SAVED_EVIDENCE_VERIFIED',component_qualified=all(r['component_qualified']for r in rows),records=rows,
           certificates_complete_328_verified=certificates,coverage_samples=coverage_samples,maximum_full_state_error=maximum,new_models=0,new_integrations=0,full_global_dynamic_passed=False)
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit))
