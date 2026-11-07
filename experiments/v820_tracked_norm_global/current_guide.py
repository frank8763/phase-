"""Current-occupancy global reference; future reachability is a SOFT cost only.

This module cannot authorize controls. The original complete native dynamic
prefix/tail gate, its uncertainty sets, and all coverage checks remain separate.
"""
from types import MethodType
import numpy as np
from motion_tracker import future_boxes, paired_rectangle_clearance

HORIZON = 6.56
HEAT_TIMES = np.linspace(0., HORIZON, 7)
HEAT_DECAY_S = 3.28
HEAT_CLEARANCE_M = .30
HEAT_SCALE_M = 1.
HEAT_EDGE_WEIGHT = 1.

def attach(field, state):
    # The route checker therefore uses the CURRENT geometric field, exactly
    # as global search does, never the fictitious route-arrival clock.
    field.temporal_state = None
    field.soft_forecast_state = None if state['center'] is None else state
    if field.soft_forecast_state is not None:
        lo, hi = future_boxes(state, HEAT_TIMES)
        field.soft_box_centers = (lo + hi) / 2
        field.soft_box_half = (hi - lo) / 2

    def reference_values(self, poses, times):
        assert len(poses) == len(times)
        return self.pose_values(poses)

    def soft_forecast_cost(self, poses):
        p = np.asarray(poses, float).reshape(-1, 3)
        result = np.zeros(len(p))
        if self.soft_forecast_state is None:
            return result
        for t, center, half in zip(HEAT_TIMES, self.soft_box_centers, self.soft_box_half):
            clearance = paired_rectangle_clearance(self, p,
                np.broadcast_to(center, (len(p), 2)), np.broadcast_to(half, (len(p), 2)))
            heat = np.clip((HEAT_CLEARANCE_M - clearance) / HEAT_SCALE_M, 0., 1.)
            result = np.maximum(result, np.exp(-t / HEAT_DECAY_S) * heat)
        return result

    field.reference_values = MethodType(reference_values, field)
    field.soft_forecast_cost = MethodType(soft_forecast_cost, field)
    return field

def route_world(world, state):
    result = dict(world)
    result['sensor_points'] = []
    if state['center'] is None:
        return result, dict(status='NO_DETECTION_NO_PROJECTION', hidden_world_geometry_used=False)
    return result, dict(status='CURRENT_OCCUPANCY_WITH_SOFT_REACHABILITY',
        horizon_s=HORIZON, soft_heat_samples=7, heat_decay_s=HEAT_DECAY_S,
        heat_clearance_m=HEAT_CLEARANCE_M, heat_scale_m=HEAT_SCALE_M,
        heat_edge_weight=HEAT_EDGE_WEIGHT,
        current_causal_rectangle_retained=True, future_cost_is_soft=True,
        reference_has_no_execution_arrival_clock=True,
        all_actual_328_native_admission_unchanged=True,
        all_original_657_coverage_unchanged=True,
        reference_is_not_dynamic_execution_certificate=True,
        hidden_world_geometry_used=False,
        scope='Global spatial proposal and soft predicted risk only; original complete dynamic control/tail admission required before every actual command.')
