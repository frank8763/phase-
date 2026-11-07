"""Independent finite-work, route, packet, state and true-contact saved audit."""
import copy,fcntl,gzip,hashlib,json,math,os,signal,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
import mujoco.rollout
def forbidden(*a,**k):raise AssertionError('SAVED_AUDIT_MODEL_OR_INTEGRATION_FORBIDDEN')
for name in ['mj_step','mj_step1','mj_step2','mj_forward']:
    setattr(mujoco,name,forbidden)
mujoco.MjModel=SimpleNamespace(from_binary_path=forbidden,from_xml_path=forbidden)
mujoco.MjData=forbidden;mujoco.MjSpec=forbidden;mujoco.rollout.rollout=forbidden
repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v798_legacy_tracking_transplant'
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
sys.path.insert(0,str(repo/'experiments/v793_complete_joint_navigation'));sys.path.insert(0,str(own))
sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
sys.path.insert(1,str(repo/'experiments/v733_early_low_translation_scan'))
sys.path.insert(1,str(repo/'experiments/v753_coupled_progress_repaired'))
from legacy_method import schedule,environment,guidance,OriginalNominal
from learned_proposer import Proposer
from corridor_method import metrics,score
from actuator_commands import CommandMap
from motion_tracker import Tracker,install_time_gate
from motion_evaluator import check_forecast
from exact_footprint import pose_values
from self_geometry import containment_margin
from dynamic_scene import Motion
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from unseen_prior import set_public_origin
from union_belief import future_cells
root=repo/'runs/v798_legacy_tracking_transplant'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert(repo/'REVIEW_PENDING').exists()and read(root/'ROUND_WINDOW.json')['round_closed']
supplement=repo/'runs/v798_supplemental_saved_audit';assert not supplement.exists();supplement.mkdir()
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SAVED_AUDIT_900S_STOP')));signal.alarm(900)
assert all(sha(repo/n)==h for n,h in read(own/'INPUT_FREEZE.json')['files'].items())
result=read(root/'RESULT.json');assert result['status']=='LEGACY_PROPOSER_TRANSPLANT_COMPLETE'
pair=repo/'runs/v793_complete_joint_navigation/main_slot01/paired';cell=pair/'geometry_memory'
protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
set_public_origin(protocol['start_qpos'][:2])
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old_packets=[json.loads(s)for s in f]
tracker=Tracker()
for p in old_packets:
    _,state=tracker.update_packet(p,protocol['known_rectangles'],protocol['known_circles'])
    if p['step']==200:break
assert p['step']==200
path_record=read(own/'REFERENCE_PATH.json');original_plan=read(repo/path_record['source'])
assert original_plan['step']==153<200 and original_plan['path']==path_record['path']
assert original_plan['causal_route_input']['rectangles']==protocol['known_rectangles']
assert original_plan['causal_route_input']['circles']==protocol['known_circles']
reference=np.asarray(path_record['path']);assert np.all(reference[:,3]==1)
static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),
    rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),
    circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,
    config=SimpleNamespace(lower=-5.,upper=5.))
assert pose_values(static,reference[:,:3]).min()>=.155
command=CommandMap.__new__(CommandMap);contract=read(own/'ACTUATOR_CONTRACT.json')
command.lower=np.asarray(contract['lower']);command.upper=np.asarray(contract['upper']);command.rate=np.asarray(contract['rate_per_public'])
logs={};account=0;bad=0
with gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')as f:
    for line in f:
        r=json.loads(line);account+=1;assert r['account_native']==account
        assert r['clearance']>=.15 and r['self_margin']>=0
        bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in r['contacts'])
        logs.setdefault(r['context'],[]).append(r)
assert bad==0
old_prefix=logs['ORIGINAL_REPLAY'];assert len(old_prefix)==1600
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:
    for i,line in enumerate(f):
        if i==1600:break
        old=json.loads(line);actual=old_prefix[i]
        assert max(np.max(abs(np.asarray(actual['qpos'])-old['qpos_full'])),
                   np.max(abs(np.asarray(actual['qvel'])-old['qvel_full'])),
                   np.max(abs(np.asarray(actual['ctrl'])-old['actual_ctrl'])))<=1e-8
checked=committed=packet_count=0;max_error=0.;maximum_progress=None;crossed=False;discovery=None
all_actual=[];last_initial=old_prefix[-1];cached_label=None;manifest=read(root/'EXECUTED_CHUNKS.json')
handovers=read(root/'HANDOVERS.json')if(root/'HANDOVERS.json').exists()else[]
def pvalues(q):
    q=np.asarray(q);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    return np.c_[q[:,:2],yaw]

def verify_chunk(chunk,expected_n):
    global packet_count,max_error,discovery,last_initial,state
    label=chunk['label'];a=logs[label];b=logs[label+'_REPEAT'];assert len(a)==len(b)==expected_n
    z=np.load(root/(chunk['certificate']+'.npz'));start=chunk['start'];end=chunk['end']
    assert end-start==expected_n and start%8==end%8==0
    original=np.load(root/(label+'_ACTUAL.npz'));repeated=np.load(root/(label+'_REPEAT_ACTUAL.npz'))
    error=float(np.max(abs(original['integration']-repeated['integration'])));assert error<=1e-8;max_error=max(max_error,error)
    event=lambda c:{k:v for k,v in c.items()if k!='physics_step'}
    for tick,(x,y)in enumerate(zip(a,b)):
        assert list(map(event,x['contacts']))==list(map(event,y['contacts']))
        for k in ['qpos','qvel','ctrl','mocap']:
            error=float(np.max(abs(np.asarray(x[k])-y[k])));assert error<=1e-8;max_error=max(max_error,error)
        assert max(np.max(abs(np.asarray(x['qpos'])-z['qpos'][start+tick])),np.max(abs(np.asarray(x['qvel'])-z['qvel'][start+tick])))<=1e-8
        assert np.array_equal(np.asarray(x['ctrl'])[contract['ids']],z['controls'][start+tick])
    with gzip.open(root/(label+'_OBSERVATIONS.json.gz'),'rt')as f:obs=json.load(f)
    with gzip.open(root/(label+'_REPEAT_OBSERVATIONS.json.gz'),'rt')as f:again=json.load(f)
    assert obs==again and len(obs)==expected_n//8
    for i,value in enumerate(obs):
        p=value['packet'];x=a[i*8+7];q=np.asarray(x['qpos']);yaw=pvalues(q[None])[0,2]
        assert np.array_equal(q[:2].astype(np.float32),p['xy'])and abs(yaw-p['yaw'])<=1e-12
        assert p['time']==x['time']and p['step']==x['public']==chunk['public_start']+i+1
        assert packet_equal(p,sensed_packet(p['xy'],p['yaw'],p['time'],p['step'],protocol,motion,noise))
        _,state=tracker.update_packet(p,protocol['known_rectangles'],protocol['known_circles'])
        assert state==value['state']and check_forecast(config,state)['passed']
        times=np.arange(657)*.01;truth=np.array([motion.xy(state['time']+t)for t in times])
        if state['center']is None:excess=float(tracker.recursive_unseen_domain.point_lower(truth,state['time']+times).max())
        else:
            lo,hi=future_cells(state['outer_state_cells'],times)
            excess=float(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max())
        assert excess<=1e-7
        if state['center']is not None and discovery is None:discovery=dict(step=p['step'],time=p['time'],xy=p['xy'])
        packet_count+=2
    last_initial=a[-1];all_actual.extend(a)

route_index=11;proposer=Proposer(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json')
for index,record in enumerate(result['records']):
    assert record['refresh']==index and record['public_start']==200+index*4
    label=f'S200_R{index:02d}';entries=read(root/(label+'_CANDIDATES.json'));assert 1<=len(entries)<=19
    assert record['old_retained_label']==cached_label and record['old_cursor']==(0 if index==0 else 32)
    assert record['old_fingerprint_unchanged']
    if cached_label is not None:
        old=np.load(root/(cached_label+'.npz'))
        assert max(np.max(abs(np.asarray(last_initial['qpos'])-old['qpos'][31])),np.max(abs(np.asarray(last_initial['qvel'])-old['qvel'][31])))<=1e-8
        assert np.array_equal(np.asarray(last_initial['ctrl'])[contract['ids']],old['controls'][31])
        assert abs(last_initial['time']-float(old['initial_time'])-.32)<=1e-8
    field=copy.copy(static);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
    current=pvalues(np.asarray(last_initial['qpos'])[None])[0]
    route_index,steer,speed=guidance(reference,current,route_index)
    real=SimpleNamespace(qpos=np.asarray(last_initial['qpos']),qvel=np.asarray(last_initial['qvel']),ctrl=np.asarray(last_initial['ctrl']),time=last_initial['time'])
    env=environment(real,SimpleNamespace(opt=SimpleNamespace(timestep=.01)))
    pointer=[0]
    def saved_prediction(target):
        j=pointer[0];pointer[0]+=1;r=entries[j];z=np.load(root/(r['label']+'.npz'))
        assert np.array_equal(target,z['parameters'])and np.array_equal(target,r['parameters'])
        return z
    legacy=OriginalNominal(command,proposer,saved_prediction)
    legacy.select(env,field,reference,route_index,current,steer,speed,real.ctrl[contract['ids']])
    assert pointer[0]==len(entries)==len(legacy.last_diagnostics)
    best=None
    for r,diag in zip(entries,legacy.last_diagnostics):
        assert diag==r['legacy_diagnostic']and r['route_index']==route_index
        z=np.load(root/(r['label']+'.npz'));q=z['qpos'];v=z['qvel']
        assert q.shape==(328,len(last_initial['qpos']))and np.array_equal(z['poses'],pvalues(q))
        assert np.array_equal(z['controls'],schedule(z['parameters'],z['initial_ctrl'],command))
        assert abs(float(z['initial_time'])-state['time'])<=1e-8
        assert max(np.max(abs(z['initial_qpos']-last_initial['qpos'])),np.max(abs(z['initial_qvel']-last_initial['qvel'])),np.max(abs(z['initial_ctrl']-np.asarray(last_initial['ctrl'])[contract['ids']])))<=1e-8
        causal=field.trajectory_values(z['poses'],.01);fixed=pose_values(static,z['poses'])
        error=max(float(np.max(abs(causal-z['causal_values']))),float(np.max(abs(fixed-z['static_values']))));assert error<=1e-10;max_error=max(max_error,error)
        margin=float(containment_margin(z['self_bounds'],np.asarray(protocol['footprint_bounds'])).min())
        speed_end=float(np.linalg.norm(v[-1,:2]));angular=float(np.linalg.norm(v[-1,3:6]))
        detail=metrics(pvalues(z['initial_qpos'][None])[0],z['poses'],reference)
        safe=bool(causal.min()>=.155 and margin>=.002 and speed_end<=.025 and angular<=.025)
        admissible=bool(safe and detail['arc_progress_m']>=-.01 and diag['reason']is None)
        value=diag.get('score')
        if value is None:value=score(detail,float(causal.min()),margin,speed_end,angular)
        assert r['safety_admissible']==safe and r['admissible']==admissible and abs(value-r['score'])<1e-10
        assert all(abs(detail[k]-r[k])<=1e-10 for k in detail)
        checked+=1
        if admissible and(best is None or value>best['score']):best=r
    assert best==record['selected']
    if best is None:
        assert not record['actual_executed']and index==len(result['records'])-1
        assert result['stopped_reason']=='NEW_CERTIFICATE_REJECTED_EXECUTE_OLD_RETAINED_TAIL';break
    assert record['actual_executed']and discovery is None
    h=handovers[committed];assert h['refresh']==index and h['old_label']==cached_label and h['old_cursor']==record['old_cursor']and h['new_label']==best['label']
    assert abs(h['created_time']-state['time'])<=1e-10 and h['created_step']==record['public_start']
    chunk=manifest[committed]
    assert chunk==dict(label=label+'_PREFIX',certificate=best['label'],start=0,end=32,public_start=200+index*4)
    verify_chunk(chunk,32);cached_label=best['label'];committed+=1
    if discovery is not None:assert index==len(result['records'])-1
if committed:
    tail=manifest[-1];assert tail==dict(label='S200_FINAL_RETAINED_TAIL',certificate=cached_label,start=32,end=328,public_start=200+committed*4)
    verify_chunk(tail,296)
    assert read(root/'FINAL_RETAINED_TAIL.json')['completed']
    assert len(manifest)==committed+1 and result['final_tail_completed']
    assert np.linalg.norm(np.asarray(last_initial['qvel'])[:2])<=.025 and np.linalg.norm(np.asarray(last_initial['qvel'])[3:6])<=.025
else:assert not manifest
assert result['legacy_200_calibration_error']<=1e-8
total_native=committed*32+(296 if committed else 0)
assert result['committed_replans']==committed and result['attempted_replans']==len(result['records'])
assert result['private_integrations']==checked*328+656<=200080
assert result['actual_validation_native']==result['branch_replay_native']==total_native<=1320
assert result['actual_packets']==packet_count and account==1600+2*total_native
q=np.asarray([x['qpos']for x in all_actual]);maximum_progress=float(np.max(8.-np.linalg.norm(q[:,:2]-protocol['goal_xy'],axis=1)));crossed=bool(np.any(q[:,0]>=0))
arc=metrics(pvalues(np.asarray(old_prefix[-1]['qpos'])[None])[0],pvalues(q),reference)['arc_progress_m']
assert abs(result['maximum_absolute_goal_progress_m']-maximum_progress)<=1e-10
assert abs(result['reference_arc_progress_m']-arc)<=1e-10 and result['central_root_center_crossed']==crossed and result['first_discovery']==discovery
qualified=bool(crossed and maximum_progress>=2.9791448279582813+.20 and arc>=1.)
assert result['component_qualified']==qualified and not result['full_global_dynamic_passed']
audit=dict(status='ALL_LEGACY_PROPOSER_SAVED_EVIDENCE_VERIFIED',checked_proposals=checked,committed_replans=committed,
    actual_packets=packet_count,private_integrations=result['private_integrations'],original_replay_native=1600,
    actual_validation_native=total_native,branch_replay_native=total_native,component_qualified=qualified,
    maximum_saved_error=max_error,legacy_200_calibration_error=result['legacy_200_calibration_error'],full_legacy_pipeline_identical=False,
    central_root_center_crossed=crossed,first_discovery=discovery,full_global_dynamic_passed=False,
    model_initializations=0,integrations=0)
(supplement/'RESULT.json').write_text(json.dumps(audit,indent=2)+'\n');signal.alarm(0);print(json.dumps(audit))
