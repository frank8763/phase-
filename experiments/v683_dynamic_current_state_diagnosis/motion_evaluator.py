"""Evaluator-only joint current state and every-native-time union forecast."""
import numpy as np
from union_belief import future_cells

def check_forecast(config,state):
    if state['center']is None:return {'passed':False,'reason':'NO_INITIAL_ACTOR_OBSERVATION','truth_scope':'evaluation only'}
    times=np.linspace(0,3.28,329);low,high=future_cells(state['outer_state_cells'],times)
    true=np.asarray(config['anchor_xy'])+np.sin((state['time']+times)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
    excess=float(np.maximum(low-true[:,None,:],true[:,None,:]-high).max(axis=2).min(axis=1).max())
    velocity=np.cos(state['time']*config['omega_rad_s']+config['phase_rad'])*config['maximum_speed_m_s']*np.asarray(config['axis_xy']);a=np.asarray(state['outer_state_cells']);joint=float(np.maximum.reduce([a[:,0]-true[0],true[0]-a[:,1],a[:,2]-velocity,velocity-a[:,3]]).max(axis=1).min())
    return {'passed':max(excess,joint)<=1e-7,'maximum_future_center_union_excess_m':excess,'current_joint_position_velocity_excess':joint,'checked_future_samples':329,'horizon_s':3.28,'truth_scope':'current state disclosed for ORACLE_CURRENT_STATE_ONLY diagnosis; future truth evaluator-only'}
