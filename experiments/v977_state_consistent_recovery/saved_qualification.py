"""Independent fine integration and unchanged complete-body envelope checks."""
import copy
import importlib.util
import math
import json
import time
from pathlib import Path
import numpy as np

C = Path(__file__).parent
_spec = importlib.util.spec_from_file_location('v977_state_reference_candidate', C/'state_reference.py')
candidate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(candidate)
_spec = importlib.util.spec_from_file_location('v977_independent_polygon_math', C.parents[1]/'experiments/v938_rpccr_recovery_segments/independent_geometry.py')
independent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(independent)


def independently_check_geometry(dense, known, prior):
    obstacle = independent.enclosure(prior)
    rectangles = [np.array([x,y])+independent.SIGNS*np.array([hx,hy]) for x,y,hx,hy in known['known_rectangles']]
    static_min = dynamic_min = math.inf
    for x,y,a,_ in dense:
        rotation = np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
        body = independent.SIGNS*independent.HALF @ rotation.T + [x,y]
        static = float(np.min(5-abs(body)))
        for rectangle in rectangles:
            static = min(static, independent.polygon_distance(body, rectangle))
        for cx,cy,radius in known['known_circles']:
            local = np.array([cx-x,cy-y])@rotation
            static = min(static, float(np.linalg.norm(np.maximum(abs(local)-independent.HALF,0)))-radius)
        static_min = min(static_min,static)
        dynamic_min = min(dynamic_min,independent.polygon_distance(body,obstacle)-.1-2e-6)
    return min(static_min,dynamic_min)


def reconstruct(initial, targets):
    # Separate fine midpoint integrator; no call to candidate.primitive.
    state = np.asarray(initial, float).copy()
    rows = [state.copy()]
    ds = .0005
    for target in targets:
        for _ in range(200):
            d1 = float(np.clip(target, state[3]-.6/.05*ds, state[3]+.6/.05*ds))
            k = math.tan((state[3]+d1)/2)/.6
            middle = state[2]+k*ds/2
            state[:2] += ds*np.array([math.cos(middle), math.sin(middle)])
            state[2] += k*ds
            state[3] = d1
            rows.append(state.copy())
    return np.asarray(rows)


def run(saved):
    checks, rows = {}, []
    for i, original in enumerate(saved['rows']):
        packet, source = original['search_packet'], original['search_source']
        started=time.perf_counter()
        plan = candidate.construct(packet, source, original['original_goal'], saved['known'], packet['body_measured_at'])
        row = dict(index=i, passed=plan['passed'], status=plan['status'], plan=plan,constructor_wall_s=time.perf_counter()-started)
        if plan['passed']:
            dense = reconstruct(plan['initial_state'], plan['edge_targets'])
            reference = np.asarray(plan['state_path'])
            numerical = float(abs(reference-dense[::25]).max())
            geometry = candidate._old.Geometry(saved['known'], source['periodic'])
            static, dynamic = geometry.clearances(dense[:, :3])
            online_minimum = float(np.minimum(static, dynamic).min())
            minimum = independently_check_geometry(dense,saved['known'],source['periodic'])
            rate = abs(np.diff(dense[:, 3]))/(.0005/.05)
            current = dict(measured_initial_state_exact=bool(np.max(abs(reference[0]-candidate.snapshot_state(packet, source, packet['body_measured_at']))) <= 1e-12),
                           independent_quadrature_within_added_reserve=numerical < candidate.NUMERICAL_RESERVE,
                           independent_polygon_agrees=abs(minimum-online_minimum)<1e-8,
                           complete_fine_body_full_cycle_geometry=minimum >= candidate.REQUIRED,
                           original_steering_rate=bool(rate.max() <= .6+1e-10),
                           actual_progress_requirement_retained=plan['actual_goal_progress_lower_m'] >= .4,
                           no_physical_claim=plan['physical_tracking_qualified'] is False and plan['stop_authority_created'] is False)
            row.update(checks=current, passed=all(current.values()), independent_numerical_error=numerical,
                       fine_minimum_clearance_m=minimum, maximum_virtual_rate=float(rate.max()))
        rows.append(row)
        checks['fixed_state_'+str(i)] = row['passed']
    packet, source = copy.deepcopy(saved['rows'][0]['search_packet']), copy.deepcopy(saved['rows'][0]['search_source'])
    now = packet['body_measured_at']
    negatives = []
    def reject(name, p, s, at, reason):
        try:
            candidate.snapshot_state(p, s, at)
        except AssertionError as error:
            ok = str(error) == reason
        else:
            ok = False
        negatives.append(dict(name=name, passed=ok))
    reject('stale_body', packet, source, now+.051, 'STALE_BODY')
    p = copy.deepcopy(packet); p['steering']['native_tick'] -= 1
    reject('incoherent_encoders', p, source, now, 'INCOHERENT_ENCODERS')
    p = copy.deepcopy(packet); p['steering']['position'][1] = .3
    reject('inconsistent_ackermann_pair', p, source, now, 'INCONSISTENT_ACKERMANN_ENCODERS')
    s = copy.deepcopy(source); s['source_native_tick'] = packet['native_tick']+1
    reject('future_source', packet, s, now, 'FUTURE_SOURCE')
    s = copy.deepcopy(source); s['periodic']['source_tick'] = s['source_native_tick']+1
    reject('future_periodic_prior', packet, s, now, 'FUTURE_PERIODIC_SOURCE')
    p = copy.deepcopy(packet); p['body'][3] = .031
    reject('moving_body_rejected', p, source, now, 'RECOVERY_REQUIRES_ACTUAL_STOP')
    checks['all_negative_state_cases'] = all(x['passed'] for x in negatives)
    nominal, lower = candidate.progress_lower_bound([0.,0.,0.], [.45,0.,0.], np.array([4.,0.]))
    checks['insufficient_actual_progress_is_red'] = nominal > .4 and lower < .4
    blocked=copy.deepcopy(saved['known'])
    blocked['known_rectangles'].append([packet['body'][0],packet['body'][1],1.,1.])
    unsafe=candidate.construct(packet,source,saved['rows'][0]['original_goal'],blocked,now)
    checks['unsafe_initial_geometry_rejected']=not unsafe['passed'] and unsafe['status']=='UNSAFE_INITIAL_REFERENCE_STATE'
    old = json.loads((C.parents[1]/'runs/v977_state_consistent_recovery/BASELINE_RED.json').read_text())
    checks['old_constructor_red_retained'] = old['passed'] is False and len(old['rows'])==2 and all(not x['passed'] for x in old['rows'])
    return dict(passed=all(checks.values()), checks=checks, models=0, integrations=0,
                private_dynamics_predictions=0, analytical_reference_only=True,
                qualification_scope='Independent analytical reference geometry and state contract only; see separate real installed RPP software results', physical_ready=False,
                negatives=negatives, rows=rows)
