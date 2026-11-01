"""Evaluator only. Never imported by tracker/planner/predictor; failure aborts.
Actual future is used only for coverage rejection, never to choose a control.
"""
import numpy as np
from motion_tracker import future_boxes

def check_forecast(config,state):
    if state['center']is None:return {'passed':False,'reason':'NO_INITIAL_ACTOR_OBSERVATION','truth_scope':'evaluation only; aborted result not a navigation success'}
    times=np.linspace(0,3.28,165);lo,hi=future_boxes(state,times);absolute=state['time']+times
    true=np.asarray(config['anchor_xy'])+np.sin(absolute*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
    excess=float(np.maximum(lo-true,true-hi).max())
    return {'passed':excess<=1e-7,'maximum_future_center_box_excess_m':excess,'checked_future_samples':165,'horizon_s':3.28,'truth_scope':'finite evaluator-only rejection; no true state enters online motion estimation or control'}
