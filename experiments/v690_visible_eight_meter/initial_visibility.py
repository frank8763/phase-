"""Causal t0 packet prerequisite plus evaluator-only coverage, no integrations."""
import numpy as np
from motion_tracker import Tracker
from motion_evaluator import check_forecast
from range_circle_memory import measured_rays
from instrumentation import dump

def certify_initial_visibility(env,rect,circ,config,out):
    # Reads exactly the same refreshed initial packet as the first decision;
    # does not refresh sensors, step physics, change RNG, or return a truth
    # state to the online tracker. The live tracker is separately initialized.
    circles,state=Tracker().update(env,rect,circ,0)
    coverage=check_forecast(config,state)
    packet={'step':0,'time':float(env.data.time),'xy':np.asarray(env.robot_xy).tolist(),'yaw':float(env.robot_yaw),'lidar':np.asarray(env.phase17c_last_lidar).tolist(),'depth':np.asarray(env.phase17c_last_depth).tolist(),'lidar_max_range':float(env.phase17c_lidar_max_range),'depth_max_range':float(env.phase17c_depth_max_range),'rays':measured_rays(env).tolist()}
    checks={'causal_detection_present':state['center']is not None and state['certified_unknown_rays']>0,'finite329_forecast_coverage':coverage['passed']and coverage.get('checked_future_samples')==329,'no_hidden_world_state_input':state['hidden_world_geometry_used']is False,'zero_physics_time':float(env.data.time)==0.}
    report={'passed':bool(all(checks.values())),'checks':checks,'packet':packet,'causal_state':state,'coverage_evaluator_only':coverage,'robot_integrations':0,'training_updates':0,'scope':'new declared initially observable course only, no unobserved-space safety claim'}
    dump(out/'INITIAL_VISIBILITY.json',report)
    return report
