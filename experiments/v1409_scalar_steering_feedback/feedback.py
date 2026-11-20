"""Read current scalar model coordinates; preserve exact measured origin."""
import math


def from_state(state):
    assert len(state)==8 and all(math.isfinite(float(x))for x in state), 'MODEL_FEEDBACK_NONFINITE_STATE'
    k=math.tan(float(state[6]))/.6;dk=(1+math.tan(float(state[6]))**2)/.6*float(state[7])
    positions=[];velocities=[]
    for sign in (1.,-1.):
        denominator=1-sign*.27*k
        assert denominator>0., 'MODEL_STEERING_COORDINATE_DOMAIN'
        a=.6*k/denominator;positions.append(math.atan(a));velocities.append(.6*dk/(denominator*denominator*(1+a*a)))
    return positions+velocities


def current(predictor):
    assert type(predictor.steps)is int and predictor.steps>=0, 'MODEL_FEEDBACK_STEP_HISTORY'
    assert predictor.high_speed_episode is False, 'DUAL_WHEEL_HIGH_SPEED_EPISODE_NOT_SCALAR_FEEDBACK'
    if predictor.steps==0:
        value=[*predictor.front.tolist(),*predictor.front_rate.tolist()]
        assert len(value)==4 and all(math.isfinite(float(x))for x in value)
        return value
    return from_state(predictor.state)
