"""Finite saved-only certificate-aging and stop-duration diagnosis.

Repeated fixed poses are geometric queries, never a new stop-control rollout.
"""
import gzip,json,math,os,signal,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
def forbidden(*a,**k):raise AssertionError('DIAGNOSIS_MODEL_AND_INTEGRATION_FORBIDDEN')
for name in ['MjModel','MjData','MjSpec','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,name,forbidden)
import mujoco.rollout
mujoco.rollout.rollout=forbidden
repo=Path(__file__).resolve().parents[2];source=repo/'experiments/v793_complete_joint_navigation'
sys.path.insert(0,str(source))
from unseen_prior import clearance as unknown_clearance
from renewal_state import decode
from persistent_norm import Historical
from exact_footprint import pose_values
root=repo/'runs/v796_corridor_cem_continuation';read=lambda p:json.loads(p.read_text())
assert(repo/'REVIEW_PENDING').exists()and read(root/'ROUND_WINDOW.json')['round_closed']
assert not(root/'REFRESH_DIAGNOSIS.json').exists()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('FIXED_SAVED_DIAGNOSIS_180S_STOP')));signal.alarm(180)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
pair=repo/'runs/v793_complete_joint_navigation/main_slot01/paired';protocol=read(pair/'STATIC_PROTOCOL.json')
static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),
    rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),
    circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,
    config=SimpleNamespace(lower=-5.,upper=5.))
observations={};native=[]
for segment in [0,1]:
    with gzip.open(root/f'S200_P{segment:02d}_OBSERVATIONS.json.gz','rt')as f:
        for value in json.load(f):observations[value['packet']['step']]=value
with gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')as f:
    for line in f:
        row=json.loads(line)
        if row['context'].startswith('S200_P')and not row['context'].endswith('_REPEAT'):native.append(row)
assert len(native)==656
by_public={x['public']:x for i,x in enumerate(native)if i%8==7}
queries=[]
for public in [211,220,230,241,252,261,271,282]:
    state=observations[public]['state'];assert state['center']is None
    row=by_public[public];q=np.asarray(row['qpos']);yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
    pose=np.array([q[0],q[1],yaw]);times=np.arange(329)*.01
    values=unknown_clearance(static,np.repeat(pose[None],329,axis=0),state,times)
    bad=np.flatnonzero(values<.155)
    queries.append(dict(public=public,time=state['time'],actual_xy=q[:2].tolist(),
        current_fixed_pose_unknown_lower_m=float(values[0]),future_fixed_pose_3_28s_lower_m=float(values[-1]),
        first_fixed_pose_query_below_155_s=None if not len(bad)else float(times[bad[0]]),
        not_a_physical_stop_forecast=True))
rows=read(root/'S200_P02_CANDIDATES.json');best=max(rows,key=lambda x:x['clearance_m'])
z=np.load(root/(best['label']+'.npz'));tick=int(np.argmin(z['causal_values']));pose=z['poses'][tick];state=observations[282]['state'];domain=decode(state['free_space_renewal'])
axisx=np.linspace(-.44,.44,45);axisy=np.linspace(-.375,.375,39);xx,yy=np.meshgrid(axisx,axisy,indexing='ij');local=np.c_[xx.ravel(),yy.ravel()];c,s=np.cos(pose[2]),np.sin(pose[2]);points=pose[:2]+np.c_[c*local[:,0]-s*local[:,1],s*local[:,0]+c*local[:,1]]
absolute=state['time']+(tick+1)*.01;rho=.5*math.hypot(axisx[1]-axisx[0],axisy[1]-axisy[0]);support=[]
for name,fn in [('current',domain.current_point_lower),('historical',Historical(domain).point_lower)]:
    values=fn(points,np.full(len(points),absolute));i=int(np.argmin(values))
    support.append(dict(provider=name,body_tile_minimum_lower_m=float(values[i]-rho-.10),
        limiting_point_xy=points[i].tolist(),limiting_local_xy=local[i].tolist()))
speed=np.linalg.norm(np.asarray([x['qvel']for x in native])[:,:2],axis=1)
angular=np.linalg.norm(np.asarray([x['qvel']for x in native])[:,3:6],axis=1)
slow=(speed<=.025)&(angular<=.025)
result=dict(status='FIXED_SAVED_CERTIFICATE_REFRESH_DIAGNOSIS_COMPLETE',
    last_proposals=len(rows),last_all_static_safe=all(x['static_minimum_m']>=.155 for x in rows),
    last_all_self_safe=all(x['self_margin_m']>=.002 for x in rows),
    last_all_terminal_linear_safe=all(x['terminal_speed_m_s']<=.025 for x in rows),
    last_all_terminal_angular_safe=all(x['terminal_angular_rad_s']<=.025 for x in rows),
    last_all_future_clearance_rejected=all(x['clearance_m']<.155 for x in rows),
    best_rejected_candidate=best,limiting_tick=tick+1,limiting_static_minimum_m=float(z['static_values'].min()),
    future_body_support_diagnostics=support,fixed_actual_pose_aging_queries=queries,
    actual_native=656,actual_simulation_s=6.56,actual_low_linear_and_angular_speed_native=int(slow.sum()),
    actual_low_linear_and_angular_speed_s=float(slow.sum()*.01),
    completed_entire_stop_contracts=2,
    hypothesis='Every compound proposal is run through its complete braking tail before replanning; this consumes observation-age budget at low speed. Test retained-tail receding-horizon handover as a distinct future candidate, with fresh actual observations and the old full tail retained on rejection.',
    hypothesis_not_causally_verified=True,receding_horizon_candidate_not_implemented_or_run=True,
    no_all_control_impossibility_claim=True,no_future_measurement_assumed_for_safety=True,
    model_initializations=0,integrations=0)
(root/'REFRESH_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');signal.alarm(0);print(json.dumps(result))
