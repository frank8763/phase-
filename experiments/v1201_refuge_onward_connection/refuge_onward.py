"""Compose a certified intermediate refuge with a certified onward source."""
import copy
import math
import time
from preview_search import q, np, search, R
from connection import CAP, compact, endpoint
from current_state_tools import validate_input


def build_refuges(x, table):
    """No sensor prediction: all candidates use the original current causal domain."""
    validate_input(x)
    origin = dict(q.initial(x['packet']), steering_load_episode=False)
    engine = q.accelerator.Engine(x['setup'], q.model.parameters()['coefficients'])
    geometry = q.Geometry(x, table)
    candidates = []
    records = []
    for count in [100, 200, 400, 600, 800]:
        for target in [-CAP, -.32, -.16, 0., .16, .32, CAP]:
            rows = [(float(target), .12, count, 0), (0., 0., 2200, 0)]
            states, controls, memory = engine.simulate(origin, rows)
            local = copy.deepcopy(x)
            local['goal'] = states[-1, :2].tolist()
            proof = q.proof(geometry, local, states, controls, q.requests_of(rows), memory)
            pose = states[-1, :3]
            guide = np.array([1.72, -1.14, -.67])
            angle = abs(math.atan2(math.sin(pose[2]-guide[2]), math.cos(pose[2]-guide[2])))
            score = float(np.linalg.norm(pose[:2]-guide[:2])) + .2*angle
            record = dict(target=float(target), moving_native=count, passed=proof['passed'],
                          proof=proof, guide_score=score, terminal_pose=pose.tolist(),
                          scope='intermediate refuge only; original goal unchanged')
            records.append(record)
            if proof['passed']:
                candidates.append(dict(record=record, rows=rows, states=states,
                                       controls=controls, memory=memory,
                                       origin=endpoint(origin, states, memory, True)))
    candidates.sort(key=lambda candidate:(candidate['record']['guide_score'],
                                         -candidate['record']['proof']['minimum_raw_m'],
                                         candidate['record']['moving_native'],
                                         candidate['record']['target']))
    return candidates, records, engine.native


def synthesize(x, table, deadline, checkpoint=lambda _:None):
    """A prefix or a preview cannot count as complete arrival on its own."""
    validate_input(x)
    if time.monotonic() >= deadline:
        return dict(passed=False, candidates=[], attempts=[], analytical_cpp_native=0,
                    models=0, new_mujoco_native=0, physical_eligible=False,
                    stop_reason='DEADLINE_BEFORE_WORK')
    candidates, records, prefix_work = build_refuges(x, table)
    original = dict(q.initial(x['packet']), steering_load_episode=False)
    engine = q.accelerator.Engine(x['setup'], q.model.parameters()['coefficients'])
    geometry = q.Geometry(x, table)
    results = []
    onward_work = 0
    selected = None
    for index, candidate in enumerate(candidates[:8]):
        if time.monotonic() >= deadline:
            break
        offset = len(candidate['controls'])
        preview = dict(origin=candidate['origin'], native_offset=offset)
        onward = search(x, table, min(deadline, time.monotonic()+8),
            lambda p:checkpoint(dict(stage='onward_search', refuge=index, **p)),
            preview=preview)
        onward_work += onward['analytical_cpp_native']
        result = dict(refuge=index, prefix=candidate['record'], passed=onward['passed'],
                      expanded=sum(onward['phase_expanded']),
                      onward_cpp_native=onward['analytical_cpp_native'],
                      best=onward['best'])
        results.append(result)
        if not onward['passed']:
            continue
        rows = compact(candidate['rows'] + onward['rows'])
        states, controls, memory = engine.simulate(original, rows)
        error = max(float(abs(states[:offset+1]-candidate['states']).max()),
                    float(abs(controls[:offset]-candidate['controls']).max()),
                    float(abs(memory[:offset+1]-candidate['memory']).max()),
                    float(abs(states[offset:]-onward['states']).max()),
                    float(abs(controls[offset:]-onward['controls']).max()),
                    float(abs(memory[offset:]-onward['memory']).max()))
        assert error <= 1e-8, 'FULL_PREFIX_ONWARD_STATE_MEMORY_COMPOSITION'
        proof = q.proof(geometry, x, states, controls, q.requests_of(rows), memory)
        assert proof['passed'], 'ONWARD_PREVIEW_IS_NOT_A_FULL_ORIGINAL_SOURCE'
        selected = dict(rows=rows, states=states, controls=controls, memory=memory,
                        proof=proof, prefix_rows=candidate['rows'],
                        onward_rows=onward['rows'], selected_refuge=index,
                        composition_error=error, native_offset=offset)
        break
    answer = dict(passed=selected is not None, candidates=records, attempts=results,
                  prefix_cpp_native=prefix_work, onward_cpp_native=onward_work,
                  composition_cpp_native=engine.native,
                  analytical_cpp_native=prefix_work+onward_work+engine.native,
                  models=0, new_mujoco_native=0, physical_eligible=False,
                  actual_source_native=x['source']['source_native_tick'],
                  actual_packet_native=x['packet']['native_tick'],
                  no_future_scans=True)
    if selected is not None:
        answer.update(selected)
    return answer
