"""One bounded software qualification; never imports a physical factory."""
from pathlib import Path
import ast
import copy
import fcntl
import hashlib
import json
import math
import signal
import sys
import time
import traceback

C = Path(__file__).resolve().parent
R = C.parents[1]
O = R / 'runs/v1151_retained_recovery_qualification'
sys.path.insert(0, str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
RESOURCE = apply()
sys.path.insert(0, str(R/'experiments/v1121_coupled_route_night'))
from bindings import REQUIRED
from source import Engine, initial, python_replay
from runtime import Predictor
from kernel import checks
sys.path.insert(0, str(R/'experiments/v1135_causal_batch'))
from geometry import Geometry
sys.path.insert(0, str(C))
from tracking import request
from retention import digest, replace, retained_cursor
import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, value):
    def default(v):
        if isinstance(v, np.ndarray): return v.tolist()
        if isinstance(v, np.generic): return v.item()
        raise TypeError(type(v).__name__)
    data = json.dumps(value, ensure_ascii=False, indent=2,
                      allow_nan=False, default=default)+'\n'
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(data)
    temp.replace(path)


def transaction_qualification(packet):
    """Positive verifier is SYNTHETIC; real proof absence must be rejected."""
    previous = dict(domain_sha256='old-domain', absolute_start_time=packet['sim_time'],
                    start_native_tick=packet['native_tick'], remaining_native=5800)
    candidate = dict(packet_sha256=digest(packet), domain_parent_sha256='old-domain',
                     domain_sha256='nested-domain', source_tick=packet['native_tick'],
                     start_native_tick=packet['native_tick'],
                     absolute_start_time=packet['sim_time'], contract='RETAINED_RECOVERY_V1',
                     remaining_stop_native=2200, remaining_native=5800,
                     plan_sha256='synthetic-test-only')
    names = ['source_and_controls_bound', 'domain_subset', 'complete_native_coverage',
             'full_ctrl_and_memory', 'terminal_full_cycle', 'initial_set_membership',
             'all_successors_covered', 'model_disturbance_verified']
    synthetic = dict.fromkeys(names, True)
    synthetic.update(minimum_raw_m=REQUIRED+.001, covered_native=5800,
                     plan_sha256=candidate['plan_sha256'])
    old_hash = digest(previous)
    new, result = replace(previous, candidate, packet,
                          lambda *_: copy.deepcopy(synthetic), lambda: 0., 1.)
    assert result['committed'] and digest(previous) == old_hash
    rejected = []
    for name in names:
        bad = dict(synthetic, **{name: False})
        kept, result = replace(previous, candidate, packet,
                               lambda *_: bad, lambda: 0., 1.)
        assert kept is previous and not result['committed']
        rejected.append(name)
    for name, value in [('minimum_raw_m', REQUIRED-1e-6),
                        ('minimum_raw_m', float('nan')),
                        ('covered_native', 5799), ('plan_sha256', 'wrong')]:
        kept, result = replace(previous, candidate, packet,
                               lambda *_: dict(synthetic, **{name:value}), lambda:0., 1.)
        assert kept is previous and not result['committed']
        rejected.append(name)
    for name, value in [('packet_sha256', 'wrong'), ('domain_parent_sha256', 'wrong'),
                        ('source_tick', packet['native_tick']+1),
                        ('absolute_start_time', packet['sim_time']+.01),
                        ('remaining_stop_native', 2199), ('contract', 'BrakeOnly')]:
        kept, result = replace(previous, dict(candidate, **{name:value}), packet,
                               lambda *_: synthetic, lambda:0., 1.)
        assert kept is previous and not result['committed']
        rejected.append(name)
    times = iter([0., 2.])
    kept, result = replace(previous, candidate, packet, lambda *_: synthetic,
                           lambda:next(times), 1.)
    assert kept is previous and not result['committed']
    def failed(*_): raise TimeoutError('SYNTHETIC_OPTIMIZER_TIMEOUT')
    kept, result = replace(previous, candidate, packet, failed, lambda:0., 1.)
    assert kept is previous and not result['committed']
    index = retained_cursor(previous, packet['native_tick']+2712,
                             packet['sim_time']+27.12, 'old-domain')
    assert index == 2712
    rejected_cursor = 0
    for tick, t, domain in [(packet['native_tick']-1, packet['sim_time'], 'old-domain'),
                            (packet['native_tick']+5800, packet['sim_time']+58., 'old-domain'),
                            (packet['native_tick'], packet['sim_time']+.01, 'old-domain'),
                            (packet['native_tick'], packet['sim_time'], 'new-domain')]:
        try: retained_cursor(previous, tick, t, domain)
        except AssertionError: rejected_cursor += 1
    assert rejected_cursor == 4
    return dict(synthetic_positive=True, rejected_verification_or_binding_cases=len(rejected)+2,
                rejected_cursor_cases=rejected_cursor, old_certificate_unchanged=True,
                synthetic_tests_are_not_a_tube_certificate=True)


def main():
    assert not O.exists(), 'ONE_QUALIFICATION_ONLY_NO_RESTART'
    O.mkdir(parents=True)
    lock = (R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard = sha(R/'REVIEW_PENDING')
    assert guard == '4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    begin = time.monotonic()
    dump(O/'ROUND_WINDOW.json', dict(started_unix=time.time(), started_monotonic=begin,
         absolute_deadline_unix=time.time()+600, hard_stop_monotonic=begin+600,
         boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
         software_only=True, models_authorized=False, previous_windows_unchanged=True))
    def halt(*_): raise TimeoutError('SOFTWARE_QUALIFICATION_600S')
    signal.signal(signal.SIGALRM, halt)
    signal.setitimer(signal.ITIMER_REAL, 600)
    error = None
    results = []
    engine = None
    cpp_native = 0
    python_native = 0
    step_inflight = False
    summary = {}
    frozen = {}
    try:
        parent = R/'runs/v1148_overnight_causal_recovery'
        base = parent/'v120_e200_h15'
        selected = json.loads((base/'SELECTED.json').read_text())
        x = selected['input']
        saved = np.load(base/'SOURCE.npz')
        table = np.load(parent/'actual_source/JOINT_TABLE.npz')
        for path in [*C.glob('*.py'), C/'PROTOCOL.md', base/'SELECTED.json',
                     base/'SOURCE.npz', base/'SOURCE_PROOF.json', base/'ALL8_BACKUPS.json',
                     parent/'actual_source/JOINT_TABLE.npz',
                     R/'runs/v1118_coupled_live_qualification/profile.so']:
            frozen[str(path.relative_to(R))] = sha(path)
        for module in list(sys.modules.values()):
            file = getattr(module, '__file__', None)
            if file and Path(file).resolve().is_relative_to(R):
                path = Path(file).resolve()
                if path.suffix == '.py': frozen[str(path.relative_to(R))] = sha(path)
        dump(C/'SOURCE_FREEZE.json', dict(files=frozen))
        for f in C.glob('*.py'): ast.parse(f.read_text())
        txn = transaction_qualification(x['packet'])
        dump(O/'TRANSACTION_QUALIFICATION.json', txn)
        g = Geometry(x, {k: table[k] for k in ['bounds','centers']})
        origin = initial(x['packet'])
        rows = selected['rows']
        n = sum(int(row[2]) for row in rows)
        assert n == 5800 and sum(row[2] for row in rows if row[1] != 0) == 2000
        assert all(row[3] == 0 for row in rows)
        engine = Engine(x['setup'])
        ss, uu = engine.simulate(origin, rows)
        cpp_native = engine.native
        step_inflight = True
        ps, pu, pm, episodes, active = python_replay(x['setup'], origin, rows)
        step_inflight = False
        python_native += n
        difference = max(float(abs(ss-ps).max()), float(abs(uu-pu).max()),
                         float(abs(saved['states']-ps).max()),
                         float(abs(saved['controls']-pu).max()),
                         float(abs(saved['memory']-pm).max()))
        assert difference <= 1e-8, 'ORIGINAL_SOURCE_RECONSTRUCTION'
        proof, _ = g.final(x, ps, pu, rows)
        assert proof['passed'], 'ORIGINAL_NOMINAL_SOURCE_CHANGED'
        a, b = g.components(ps[:,:3], np.arange(n+1))
        lower = np.minimum(a,b)
        suffix_min = np.minimum.accumulate(lower[::-1])[::-1]
        indices = list(range(0,n-2200+1,8))
        inherited = [{'native': i, 'remaining_native': n-i,
                      'minimum_suffix_raw_m': float(suffix_min[i]),
                      'state_sha256': hashlib.sha256(ps[i].tobytes()).hexdigest(),
                      'memory_sha256': hashlib.sha256(pm[i].tobytes()).hexdigest()}
                     for i in indices]
        assert len(inherited) == 451 and all(q['minimum_suffix_raw_m'] >= REQUIRED
                                             for q in inherited)
        dump(O/'NOMINAL_SUFFIXES.json', dict(all8_suffixes=inherited,
             nominal_only=True, absolute_start_time=x['packet']['sim_time'],
             exact_complete_state_memory_and_policy_required=True,
             not_a_perturbed_state_proof=True))
        # Sound rigid-transform envelope for exact fixed-command dynamics only.
        rho = math.hypot(.44,.375)
        radius = .04+2*math.sin(.035/2)*(np.linalg.norm(ps[:,:2]-ps[0,:2],axis=1)+rho)
        delivery = .1*(.13+rho*.16)+.02*(.13+rho*.16+.08)
        tube_lower = lower-radius-delivery
        pose_only = dict(assumptions='exact model, identical non-pose state and body-command schedule; initial XY ball .04 and yaw interval .035; no later disturbances',
                         sufficient_geometry_passed=bool(tube_lower.min() >= .155),
                         minimum_lower_m=float(tube_lower.min()),
                         required_after_once_only_reserves_m=.155,
                         dynamic_error_and_feedback_not_covered=True,
                         max_position_radius_m=float(radius.max()),
                         failure_not_an_impossibility_proof=True)
        dump(O/'EXACT_MODEL_POSE_ENVELOPE.json', pose_only)
        schedule = [(float(target), float(speed)) for target,speed,ticks,mode in rows
                    for _ in range(int(ticks))]
        cases = [('nominal',0.,0.,0.), ('x_plus',.04,0.,0.), ('x_minus',-.04,0.,0.),
                 ('y_plus',0.,.04,0.), ('y_minus',0.,-.04,0.),
                 ('yaw_plus',0.,0.,.035), ('yaw_minus',0.,0.,-.035)]
        for name, dx, dy, dyaw in cases:
            assert time.monotonic() < begin+570, 'ROLLOUT_TIME_RESERVE'
            packet = copy.deepcopy(x['packet'])
            packet['body'][0] += dx
            packet['body'][1] += dy
            packet['body'][2] += dyaw
            p = Predictor(x['setup'], initial(packet))
            states, ctrl, requests, memory = [p.state.copy()], [], [], [np.r_[p.adapter.last,p.adapter.integral]]
            for i, (target, speed) in enumerate(schedule):
                v, w, err = request(p.state, ps[i], target, speed)
                step_inflight = True
                state, u = p.step(v,w,False)
                step_inflight = False
                python_native += 1
                states.append(state); ctrl.append(u); requests.append([v,w,0.])
                memory.append(np.r_[p.adapter.last,p.adapter.integral])
            states, ctrl, requests, memory = map(np.array, [states,ctrl,requests,memory])
            a, b = g.components(states[:,:3], np.arange(n+1))
            low = float(np.minimum(a,b).min())
            cc, upper = checks(states,ctrl,requests,packet,x['setup'],np.array(x['goal']),low,REQUIRED)
            terminal = float(g.cycle(states[-1:,:3])[0])
            position = float(np.linalg.norm(states[-1,:2]-ps[-1,:2]))
            heading = abs(math.atan2(math.sin(states[-1,2]-ps[-1,2]),math.cos(states[-1,2]-ps[-1,2])))
            cc.update(full2200_stop=bool((requests[-2200:] == 0.).all()),
                      terminal_full_cycle=terminal >= REQUIRED,
                      same_terminal_position=position <= .025,
                      same_terminal_heading=heading <= .1,
                      request_speed=bool((requests[:,0] >= 0).all() and (requests[:,0] <= .12).all()),
                      complete_controller_memory=bool(len(memory) == n+1 and (memory[1:,:4] == ctrl).all()))
            maximum = float(np.linalg.norm(states[:,:2]-ps[:,:2],axis=1).max())
            case = dict(case=name, passed=bool(all(cc.values())), checks=cc,
                        failed_checks=[k for k,v in cc.items() if not v],
                        initial_pose_offset=[dx,dy,dyaw], minimum_raw_m=low,
                        terminal_cycle_raw_m=terminal, goal_upper_m=upper,
                        terminal_position_error_m=position, terminal_heading_error_rad=heading,
                        maximum_position_error_m=maximum, native=n,
                        finite_case_not_robust_proof=True)
            dump(O/(name+'.json'), case)
            np.savez_compressed(O/(name+'.npz'), states=states, controls=ctrl,
                                requests=requests, memory=memory)
            results.append(case)
            dump(O/'PROGRESS.json', dict(completed_cases=len(results), cases=results,
                 analytical_cpp_native=engine.native, analytical_python_native=python_native))
        summary.update(original_source_error=difference, nominal_source_passed=True,
                       nominal_all8_retained_suffixes=len(inherited),
                       transaction_qualification=txn, pose_only_envelope=pose_only,
                       feedback_cases_passed=sum(r['passed'] for r in results),
                       feedback_cases_total=7,
                       model_disturbance_bound_verified=False,
                       feedback_recovery_tube_verified=False,
                       physical_eligible=False,
                       stop_reason='FINITE_SOFTWARE_QUALIFICATION_COMPLETE')
    except BaseException as exc:
        error = dict(error=repr(exc), traceback=traceback.format_exc())
        dump(O/'ERROR.json', error)
        summary.update(physical_eligible=False, stop_reason='SOFTWARE_OPERATION_OR_EVIDENCE_ERROR')
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        unchanged = all(sha(R/name) == value for name,value in frozen.items())
        summary.update(closed=True, error=error, cases=results,
             analytical_cpp_native=engine.native if engine else cpp_native,
             cpp_inflight_unknown=bool(engine and getattr(engine,'in_call',False)),
             analytical_python_native=python_native,
             python_inflight_unknown=step_inflight, models=0, physical_native=0,
             training_updates=0, source_unchanged=unchanged,
             guard_original=sha(R/'REVIEW_PENDING') == guard,
             wall_s=time.monotonic()-begin, resource_policy=RESOURCE,
             new24_executed=False, physical_auto_launch=False)
        dump(O/'COMPLETION.json', summary)
        print(json.dumps({k:v for k,v in summary.items() if k not in
                          ['cases','transaction_qualification','resource_policy','pose_only_envelope']},
                         ensure_ascii=False))
        fcntl.flock(lock,fcntl.LOCK_UN)
    return 0 if error is None and unchanged else 1


if __name__ == '__main__':
    sys.exit(main())
