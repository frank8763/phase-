"""All-period enclosure from current causal coefficient vertices only.

Equivalent to the existing full-period swept box, without changing the route
planner's HORIZON map or consulting actor anchor/phase/axis/truth. This supplies
a conservative obstacle for a future current-event witness, never permission.
"""
import copy
import math
from route_event import digest, finite_vector


def all_future(snapshot, *, current_native, current_sim_time):
    assert snapshot['model'] == 'PERIODIC' and snapshot['online_actor_truth'] is False, 'BRIDGE_MODEL_OR_TRUTH'
    assumptions = snapshot['class_assumptions']
    assert assumptions == dict(amplitude_m=.25, maximum_center_displacement_m=.5, omega_rad_s=.32, norm_speed_m_s=.08), 'BRIDGE_PUBLIC_CLASS_CHANGED'
    p = snapshot['periodic']
    assert p['omega'] == .32 and p['amplitude'] == .25, 'BRIDGE_PERIODIC_CLASS_CHANGED'
    assert type(current_native) is int and type(p['source_tick']) is int and 0 <= p['source_tick'] <= current_native, 'BRIDGE_FUTURE_COEFFICIENTS'
    assert math.isfinite(current_sim_time) and math.isfinite(p['last']) and 0 <= p['last'] <= current_sim_time+1e-8, 'BRIDGE_FUTURE_COEFFICIENT_TIME'
    assert p['coefficient_norm_outer_facets'] == 64 and p['coefficient_norm_radius'] == .25 and p['coefficient_norm_roundoff'] == 2e-7, 'BRIDGE_COEFFICIENT_PRIOR_CHANGED'
    assert p['public_motion_class_unchanged'] is True, 'BRIDGE_NEW_MOTION_PRIOR'
    vertices = p['vertices']
    assert isinstance(vertices,list) and len(vertices) == 8, 'BRIDGE_COEFFICIENT_DIRECTIONS'
    upper = []; negative_lower = []
    for polytope in vertices:
        assert isinstance(polytope,list) and len(polytope) >= 4, 'BRIDGE_COEFFICIENT_EMPTY'
        for vertex in polytope:
            finite_vector(vertex,3)
        # max_t(c+a sin(wt)+b cos(wt)) = c+hypot(a,b).
        # Maximization over a finite vertex enclosure commutes with max_t.
        upper.append(max(c+math.hypot(a,b) for c,a,b in polytope)+2e-7)
        negative_lower.append(max(-c+math.hypot(a,b) for c,a,b in polytope)+2e-7)
    lo = [-negative_lower[0],-negative_lower[4]]
    hi = [upper[0],upper[4]]
    assert all(a<=b for a,b in zip(lo,hi)), 'BRIDGE_EMPTY_COEFFICIENT_BOX'
    center = [(a+b)/2 for a,b in zip(lo,hi)]
    radius = math.dist(lo,hi)/2 + .10
    return dict(native_tick=current_native, sim_time=current_sim_time, periodic_source_tick=p['source_tick'],
                center=center, radius_m=radius, lower_xy=lo, upper_xy=hi,
                method='CURRENT_COEFFICIENT_FULL_PERIOD_SWEPT_DISK',
                invariant_for_all_future_under_declared_class=True, coefficient_snapshot_sha256=digest(snapshot),
                input_periodic=copy.deepcopy(p), independent_of_saved_handoff_tick=True,
                planner_forecast_unchanged=True, physical_admission=False)
