"""Independent readback of saved proposals, actual packets and native branches.

Model constructors and all integration entry points are sealed in this audit.
"""
import copy, gzip, hashlib, json, sys, os, signal
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
import mujoco.rollout
def forbidden(*a, **k): raise AssertionError('AUDIT_MODEL_OR_INTEGRATION_FORBIDDEN')
for name in ['mj_step','mj_step1','mj_step2','mj_forward','mj_rollout']:
    if hasattr(mujoco,name):setattr(mujoco,name,forbidden)
mujoco.MjModel=SimpleNamespace(from_binary_path=forbidden,from_xml_path=forbidden)
mujoco.MjData=forbidden;mujoco.MjSpec=forbidden;mujoco.rollout.rollout=forbidden
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
source=repo/'experiments/v793_complete_joint_navigation'
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
sys.path.insert(0,str(source));sys.path.insert(0,str(own))
sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
sys.path.insert(1,str(repo/'experiments/v733_early_low_translation_scan'))
sys.path.insert(1,str(repo/'experiments/v753_coupled_progress_repaired'))
from method import LOW,HIGH,samples,update,schedule,opportunity,merit
from actuator_commands import CommandMap
from motion_tracker import Tracker,install_time_gate
from exact_footprint import pose_values
from self_geometry import containment_margin
from dynamic_scene import Motion
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from unseen_prior import set_public_origin,clearance as unseen_clearance
root=repo/'runs/v794_cem_sensing_qualification'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SAVED_AUDIT_600S_STOP')))
signal.alarm(600)
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (repo/'REVIEW_PENDING').exists() and read(root/'ROUND_WINDOW.json')['round_closed']
assert not(root/'SAVED_AUDIT.json').exists()
assert all(sha(repo/n)==h for n,h in read(own/'INPUT_FREEZE.json')['files'].items())
result=read(root/'RESULT.json');assert result['status']=='FIXED_CEM_CAUSAL_SENSING_COMPONENT_COMPLETE'
pair=repo/'runs/v793_complete_joint_navigation/main_slot01/paired';cell=pair/'geometry_memory'
protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as stream:old=[json.loads(s)for s in stream]
set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();trackers={};states={}
for packet in old:
    _,state=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles'])
    if packet['step'] in [125,200]:trackers[packet['step']]=copy.deepcopy(tracker);states[packet['step']]=state
    if packet['step']>=200:break
static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),
    rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),
    circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,
    config=SimpleNamespace(lower=-5.,upper=5.))
command=CommandMap.__new__(CommandMap)
command.lower=np.asarray(read(own/'ACTUATOR_CONTRACT.json')['lower'])
command.upper=np.asarray(read(own/'ACTUATOR_CONTRACT.json')['upper'])
command.rate=np.array([.10,.10,.70,.70])
checked=0;max_error=0.;obs_count=0;native_validation=0;native_replay=0
def check_optimizer(step,role,tr,state,count):
    global checked,max_error
    entries=read(root/f'S{step}_{role}_CANDIDATES.json');assert len(entries)==4*count
    draws=np.load(own/'STANDARD_NORMALS.npz')[f'S{step}_{role}']
    mean=(LOW+HIGH)/2;std=.5*(HIGH-LOW);incumbent=None;incumbent_score=-float('inf');best=None
    field=copy.copy(static);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
    for it in range(4):
        values=samples(draws[it],mean,std,incumbent,it);scores=[]
        for j,p in enumerate(values):
            r=entries[it*count+j];z=np.load(root/(r['label']+'.npz'))
            assert r['iteration']==it and r['index']==j and np.array_equal(p,r['parameters'])
            assert np.array_equal(z['controls'],schedule(p,z['initial_ctrl'],command))
            assert abs(float(z['initial_time'])-state['time'])<1e-8
            q=z['qpos'];v=z['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
            assert np.array_equal(z['poses'],np.c_[q[:,:2],yaw])
            causal=field.trajectory_values(z['poses'],.01);fixed=pose_values(static,z['poses'])
            err=max(float(np.max(abs(causal-z['causal_values']))),float(np.max(abs(fixed-z['static_values']))))
            max_error=max(max_error,err);assert err<=1e-10
            margin=float(containment_margin(z['self_bounds'],np.asarray(protocol['footprint_bounds'])).min())
            speed=float(np.linalg.norm(v[-1,:2]));angular=float(np.linalg.norm(v[-1,3:6]))
            progress=float(np.linalg.norm(z['initial_qpos'][:2]-protocol['goal_xy'])-np.linalg.norm(q[-1,:2]-protocol['goal_xy']))
            admissible=bool(causal.min()>=.155 and margin>=.002 and speed<=.025 and angular<=.025)
            info=opportunity(z['poses'],protocol,tr.recursive_unseen_domain,z['initial_qpos'][:2])if admissible else 0.
            heading=abs((float(yaw[-1])-np.arctan2(protocol['goal_xy'][1]-z['initial_qpos'][1],protocol['goal_xy'][0]-z['initial_qpos'][0])+np.pi)%(2*np.pi)-np.pi)
            score=merit(progress,heading,info,float(causal.min()),margin,speed,angular)
            assert r['admissible']==admissible and abs(score-r['score'])<1e-10 and abs(progress-r['progress_m'])<1e-12
            assert abs(info-r['observation_opportunity'])<1e-12
            scores.append(score);checked+=1
            if score>incumbent_score:incumbent_score=score;incumbent=p.copy()
            if admissible and(best is None or score>best['score']):best=r
        mean,std,_=update(values,scores,mean,std)
    return best

def check_actual(step,role,selected,tr,state):
    global obs_count,native_validation,native_replay,max_error
    label=f'S{step}_{role}';z=np.load(root/(selected['label']+'.npz'))
    actual=np.load(root/(label+'_ACTUAL.npz'));repeat=np.load(root/(label+'_REPEAT_ACTUAL.npz'))
    err=float(np.max(abs(actual['integration']-repeat['integration'])));assert err<=1e-8
    max_error=max(max_error,err);assert actual['integration'].shape[0]==328
    assert actual['safety'][:,0].min()>=.15 and actual['safety'][:,1].min()>=0
    with gzip.open(root/(label+'_OBSERVATIONS.json.gz'),'rt')as f:observations=json.load(f)
    with gzip.open(root/(label+'_REPEAT_OBSERVATIONS.json.gz'),'rt')as f:repeated=json.load(f)
    assert observations==repeated and len(observations)==41
    for value in observations:
        p=value['packet'];assert packet_equal(p,sensed_packet(p['xy'],p['yaw'],p['time'],p['step'],protocol,motion,noise))
        _,state=tr.update_packet(p,protocol['known_rectangles'],protocol['known_circles'])
        assert state==value['state'] and value['coverage']['execution']['passed']
        if state['center']is None:
            times=state['time']+np.arange(657)*.01;truth=np.array([motion.xy(t)for t in times])
            excess=float(tr.recursive_unseen_domain.point_lower(truth,times).max());assert excess<=1e-7
        obs_count+=2
    # Logs contain all actual native qpos/qvel/ctrl and evaluated true contacts.
    main=[];again=[]
    with gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')as f:
        for line in f:
            r=json.loads(line)
            if r['context'] not in [label,label+'_REPEAT']:continue
            (main if r['context']==label else again).append(r)
    assert len(main)==len(again)==328
    for i,(a,b)in enumerate(zip(main,again)):
        # Preregistered accounting ordinal is not a physical contact attribute.
        event=lambda c:{k:v for k,v in c.items()if k!='physics_step'}
        assert list(map(event,a['contacts']))==list(map(event,b['contacts']))
        for k in ['qpos','qvel','ctrl','mocap']:
            assert np.max(abs(np.asarray(a[k])-b[k]))<=1e-8
        assert max(np.max(abs(np.asarray(a['qpos'])-z['qpos'][i])),np.max(abs(np.asarray(a['qvel'])-z['qvel'][i])))<=1e-8
        assert np.array_equal(np.asarray(a['ctrl'])[:4],z['controls'][i])
    native_validation+=328;native_replay+=328
    return state

for record in result['records']:
    step=record['step'];tr=copy.deepcopy(trackers[step]);state=states[step]
    chosen=check_optimizer(step,'MANEUVER',tr,state,48);assert chosen==record['selected']
    if record['actual_executed']:
        assert chosen['progress_m']>=.05 and record['repeat_executed']
        state=check_actual(step,'MANEUVER',chosen,tr,state)
        forward=check_optimizer(step,'CONTINUATION',tr,state,32);assert forward==record['forward_continuation']
        if forward is not None and forward['progress_m']>=.02:
            z=np.load(root/(forward['label']+'.npz'))
            aged=np.minimum(pose_values(static,z['poses']),unseen_clearance(static,z['poses'],states[step],3.28+np.arange(1,329)*.01))
            renewed=z['causal_values'];gain=float(renewed.min()-aged.min())
            assert abs(gain-record['renewed_minus_aged_clearance_m'])<1e-10
            assert record['component_qualified']==bool(gain>=.01)
            state=check_actual(step,'CONTINUATION',forward,tr,state)
        else:assert not record['component_qualified']
    else:assert chosen is None or chosen['progress_m']<.05
assert result['private_integrations']==checked*328+2*656
assert result['actual_validation_native']==native_validation and result['branch_replay_native']==native_replay
assert result['actual_packets']==obs_count and result['original_replay_native']==1600
assert result['maximum_native_error']<=1e-8 and result['bad_contacts']==0
audit=dict(status='ALL_FIXED_CEM_SENSING_SAVED_EVIDENCE_VERIFIED',checked_proposals=checked,
    actual_packets=obs_count,actual_validation_native=native_validation,branch_replay_native=native_replay,
    private_integrations=result['private_integrations'],maximum_saved_error=max_error,
    model_initializations=0,integrations=0,component_qualified=result['component_qualified'],
    full_global_navigation_passed=False,new_confirmation=0)
(root/'SAVED_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))
signal.alarm(0)
