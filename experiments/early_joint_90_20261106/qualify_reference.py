"""Array-only positive/negative controller, continuation and budget checks."""
import copy
import importlib.abc
import json
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name=='mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('ZERO_MODEL_REFERENCE_QUALIFICATION')
sys.meta_path.insert(0,NoModels())
repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v841_early_joint'
sys.path.insert(0,str(own))
from reference_recovery import reference_target, budget
import reference_certificate_audit as independent
from actuator_commands import CommandMap
root=repo/'runs/early_joint_90_20261106/qualification'
limits=np.array([[-.52,.52],[-.52,.52],[-24.,24.],[-24.,24.]])
rate=np.array([.1,.1,.7,.7])
path=np.c_[np.linspace(0.,2.,80),.20*np.linspace(0.,2.,80)**2,np.arctan(.4*np.linspace(0.,2.,80)),np.ones(80)]
q=[]
for tick in range(329):
    x=.003*tick; yaw=math.atan(.4*x)
    q.append([x,.20*x*x,.2,math.cos(yaw/2),0.,0.,math.sin(yaw/2)])
q=np.asarray(q);initial=q[0];future=q[1:];command=np.zeros(4);commands=[];targets=[];index=0;target=np.zeros(4)
for tick in range(0,328,8):
    if tick<208:
        state=initial if tick==0 else future[tick-1]
        yaw=2*math.atan2(state[6],state[3])
        target,index=reference_target(np.array([*state[:2],yaw]),path,index,.35,8.,.60)
    else:
        target=target.copy();target[2:]=0.
    command=np.clip(np.clip(target,limits[:,0],limits[:,1]),command-rate,command+rate)
    commands.extend([command.copy()for _ in range(8)]);targets.extend([target.copy()for _ in range(8)])
c=dict(reference_following=dict(path=path.tolist(),index=0,goal_xy=[3.,1.],wheel_base=.60,lookahead_m=.35,wheel_speed=8.,drive_ticks=208,targets=np.asarray(targets).tolist()),
    prefix_command=np.zeros(4).tolist(),prefix_initial_qpos=initial.tolist(),initial_qpos=initial.tolist(),qpos=future[:320].tolist(),
    controls=np.asarray(commands)[:320].tolist(),brake_after_native_ticks=208,signed_longitudinal_displacement_m=float(future[319,0]),
    one_cycle_continuation=dict(extra_qpos=future[320:].tolist(),extra_controls=np.asarray(commands)[320:].tolist()))
independent.expected_follow(c,limits,rate)
assert np.ptp(np.asarray(targets)[:208,0])>.001,'FIXED_STEER_MASQUERADING_AS_REFERENCE_FOLLOWING'
negative=0
for change in ['control','target','path','lookahead','future_extra_control']:
    wrong=copy.deepcopy(c)
    if change=='control':wrong['controls'][16][0]+=.02
    elif change=='target':wrong['reference_following']['targets'][0][0]+=.02
    elif change=='path':wrong['reference_following']['path'][1][3]=-1
    elif change=='lookahead':wrong['reference_following']['lookahead_m']=.7
    else:wrong['one_cycle_continuation']['extra_controls'][0][2]+=.2
    try:independent.expected_follow(wrong,limits,rate)
    except (AssertionError,IndexError):negative+=1
    else:raise AssertionError('MUTATION_NOT_REJECTED_'+change)
os.environ['PHASE_PRIVATE_NATIVE_CAP']='16'
try:budget(SimpleNamespace(prediction_steps=12),8)
except AssertionError:negative+=1
else:raise AssertionError('NATIVE_CAP_NOT_ENFORCED')
os.environ.pop('PHASE_PRIVATE_NATIVE_CAP')
os.environ['PHASE_MODEL_ABSOLUTE_DEADLINE']='0'
try:budget(SimpleNamespace(prediction_steps=0),8)
except AssertionError:negative+=1
else:raise AssertionError('ABSOLUTE_DEADLINE_NOT_ENFORCED')
os.environ.pop('PHASE_MODEL_ABSOLUTE_DEADLINE')
# A synthetic bound function only exercises the 328/336 index seam, not physics.
old_values=independent.independent_values
independent.independent_values=lambda poses,*_:np.full(len(poses),.20)
extra=c['one_cycle_continuation'];extra.update(minimum_clearance_m=.20,minimum_self_margin_m=.01,terminal_speed_m_s=0.,extra_qvel=np.zeros((8,6)).tolist(),extra_poses=np.c_[future[320:,:2],2*np.arctan2(future[320:,6],future[320:,3])].tolist(),extra_self_bounds=np.repeat([[-.4,-.3,.4,.3]],9,axis=0).tolist(),no_future_observations_assumed=True,absolute_end_time=3.36)
c.update(prefix_poses=np.repeat([[0.,0.,0.]],8,axis=0).tolist(),created_time=0.,forecast_state={},minimum_causal_predicted_clearance_m=.20,recovery_kind='REFERENCE_FOLLOW_BRAKE')
protocol=dict(footprint_bounds=[-.44,-.375,.44,.375])
independent.check_successor(c,protocol,limits,rate)
for change in ['successor_clearance','extra_time','observation_assumption','extra_qpos']:
    wrong=copy.deepcopy(c)
    if change=='successor_clearance':wrong['one_cycle_continuation']['minimum_clearance_m']=.21
    elif change=='extra_time':wrong['one_cycle_continuation']['absolute_end_time']=3.28
    elif change=='observation_assumption':wrong['one_cycle_continuation']['no_future_observations_assumed']=False
    else:wrong['one_cycle_continuation']['extra_qpos'][0][0]+=.02
    try:independent.check_successor(wrong,protocol,limits,rate)
    except AssertionError:negative+=1
    else:raise AssertionError('SUCCESSOR_MUTATION_NOT_REJECTED_'+change)
independent.independent_values=old_values
result=dict(passed=True,controller_independent_array_reconstruction=True,nonconstant_steer=True,negative_cases=negative,
    original328_and_extra8_index_seam=True,synthetic_bound_scope='interface only; not physical clearance or model audit',models=0,integrations=0)
(root/'REFERENCE_ARRAY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
