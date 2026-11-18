"""Finite forward control-space proposals; the original proof authorizes none by default.

Nodes retain exact dynamics and controller memory. Grid keys prune proposals only;
they never stand for a certified state cell. Preview origins are analytical, not
fabricated sensor packets and never directly eligible for physical execution.
"""
from dataclasses import dataclass
from pathlib import Path
import copy
import heapq
import math
import sys
import time

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'experiments/v1186_live_observer_regeneration'))
from current_state_tools import q, np, validate_input

CAP = .42722137342572125
TURNS = (-CAP, -.32, -.16, 0., .16, .32, CAP)
DURATIONS = (100, 200)
MAX_MOTION = 6000
MAX_EXPANSIONS = 6000
MAX_NODES = 48000
MAX_TERMINAL = 64
MARGIN = .002


@dataclass
class Node:
    origin: dict
    native: int
    moving: int
    parent: int
    row: tuple | None
    minimum: float


def endpoint(origin, states, memory, moving):
    """Transfer the entire predictor state, controller memory and mode flags."""
    return dict(state=states[-1].copy(), last_ctrl=memory[-1, :4].copy(),
                integral=float(memory[-1, 4]), coupled_episode=False,
                steering_motion_active=False,
                steering_load_episode=True if moving else origin['steering_load_episode'])


class OffsetGeometry:
    def __init__(self, geometry, offset):
        self.geometry = geometry
        self.offset = int(offset)

    def components(self, poses, ticks):
        return self.geometry.components(poses, np.asarray(ticks) + self.offset)

    def cycle(self, poses):
        return self.geometry.cycle(poses)


class StaticGeometry:
    """Offline diagnostic ablation; never an execution certificate."""
    def __init__(self, geometry):
        self.geometry = geometry

    def components(self, poses, ticks):
        a, _ = self.geometry.components(poses, ticks)
        return a, np.full_like(a, np.inf)

    def cycle(self, poses):
        return self.geometry.geometry.static.clearances(poses)[0]


def compact(rows):
    out = []
    for t, v, n, mode in rows:
        row = (float(t), float(v), int(n), int(mode))
        if out and out[-1][:2] == row[:2] and out[-1][3] == mode and out[-1][2]+n <= 12000:
            old = out.pop()
            row = (row[0], row[1], old[2]+row[2], row[3])
        out.append(row)
    return out


def state_key(node, absolute_start, period):
    s = node.origin['state']
    # Exact state and memory remain in Node, including quantities omitted here.
    # This is a heuristic pruning key, not a reachable-set approximation.
    return (round(s[0]/.075), round(s[1]/.075), round(s[2]/.075),
            round(s[6]/.04), round(s[7]/.10), round(s[3]/.02),
            round(s[4]/.005), round(s[5]/.03),
            round(node.origin['integral']/.02),
            int(((absolute_start + .01*node.native) % period)/.5),
            node.origin['steering_load_episode'])


def path_rows(nodes, index):
    rows = []
    while index >= 0:
        node = nodes[index]
        if node.row is not None:
            rows.append(node.row)
        index = node.parent
    return compact(list(reversed(rows)))


def connect(x, table, deadline, checkpoint=lambda _: None, *, origin=None,
            native_offset=0, static_only=False):
    """Find one fully re-propagated source; finite refusal is not infeasibility.

    A caller may preview an exact predicted endpoint with native_offset. Its
    causal domain and clock still originate in the real x. Every returned
    object has physical_eligible=False, including a passing nominal source.
    """
    validate_input(x)
    assert type(native_offset) is int and native_offset >= 0
    initial = copy.deepcopy(origin) if origin is not None else dict(
        q.initial(x['packet']), steering_load_episode=False)
    assert not initial.get('coupled_episode', False)
    assert not initial.get('steering_motion_active', False)
    assert type(initial['steering_load_episode']) is bool
    g = q.Geometry(x, table)
    engine = q.accelerator.Engine(x['setup'], q.model.parameters()['coefficients'])
    shifted = OffsetGeometry(g, native_offset)
    proof_geometry = StaticGeometry(shifted) if static_only else shifted
    proof_input = copy.deepcopy(x)
    # Original proof uses this field for the first command's slew check only.
    # Never present the preview as a new real sensor measurement.
    proof_input['packet']['controller_memory']['last_ctrl'] = initial['last_ctrl'].tolist()
    nodes = []
    queue = []
    visited = {}
    expansions = 0
    terminal_attempts = 0
    selected = None
    best = None
    edge_rejections = dict(static=0, dynamic=0)
    started = time.monotonic()

    def bounds(states, offset):
        a, b = g.components(states[:, :3], np.arange(len(states))+native_offset+offset)
        return a, np.full_like(a, np.inf) if static_only else b

    def priority(node):
        state = node.origin['state']
        delta = np.asarray(x['goal']) - state[:2]
        distance = float(np.linalg.norm(delta))
        heading = abs(math.atan2(math.sin(math.atan2(delta[1], delta[0])-state[2]),
                                 math.cos(math.atan2(delta[1], delta[0])-state[2])))
        return (.01*node.moving + .0002*(node.native-node.moving) +
                2.2*distance/.12 + 1.2*heading + .02/max(.005, node.minimum-q.REQUIRED))

    def add(node):
        if len(nodes) >= MAX_NODES:
            return
        key = state_key(node, x['packet']['sim_time']+.01*native_offset, g.period)
        score = node.moving + .02*(node.native-node.moving)
        if key in visited and score >= visited[key]-1e-9:
            return
        visited[key] = score
        index = len(nodes)
        nodes.append(node)
        heapq.heappush(queue, (priority(node), index))

    # Waits cover one publicly specified motion period, not the true actor phase.
    # Every wait is actually propagated and checked at all native states.
    period_native = int(math.ceil(g.period/.01))
    waits = range(0, min(period_native, 2000)+1, 100)
    for wait in waits:
        if time.monotonic() >= deadline:
            break
        if wait:
            ss, _, mm = engine.simulate(initial, [(0., 0., wait, 0)])
            org = endpoint(initial, ss, mm, False)
        else:
            ss = np.asarray(initial['state'])[None, :]
            org = initial
        a, b = bounds(ss, 0)
        minimum = float(np.minimum(a, b).min())
        if minimum >= q.REQUIRED + MARGIN:
            add(Node(org, wait, 0, -1, (0., 0., wait, 0) if wait else None, minimum))

    while queue and expansions < MAX_EXPANSIONS and len(nodes) < MAX_NODES:
        if time.monotonic() >= deadline:
            break
        _, index = heapq.heappop(queue)
        node = nodes[index]
        state = node.origin['state']
        distance = float(np.linalg.norm(state[:2] - x['goal']))
        if best is None or distance < best['distance']:
            best = dict(distance=distance, native=node.native, moving=node.moving,
                        state=state.tolist(), path_minimum=node.minimum,
                        rows=path_rows(nodes, index))
            checkpoint(dict(stage='control_space_search', expanded=expansions,
                nodes=len(nodes), best=best, cpp_native=engine.native,
                terminal_attempts=terminal_attempts, static_only=static_only))
        if distance <= .35 and terminal_attempts < MAX_TERMINAL:
            # This is only a cheap shortlist filter, not the terminal certificate.
            if static_only or float(g.cycle(state[None, :3])[0]) >= q.REQUIRED-.03:
                terminal_attempts += 1
                rows = compact(path_rows(nodes, index) + [(0., 0., 2200, 0)])
                ss, uu, mm = engine.simulate(initial, rows)
                proof = q.proof(proof_geometry, proof_input, ss, uu, q.requests_of(rows), mm)
                if proof['passed'] and not static_only:
                    selected = dict(rows=rows, states=ss, controls=uu, memory=mm,
                                    proof=proof)
                    break
                if static_only:
                    if proof['passed']:
                        selected = dict(rows=rows, states=ss, controls=uu, memory=mm,
                            proof=proof, static_connection_only=True)
                        break
        expansions += 1
        if node.moving >= MAX_MOTION:
            continue
        for target in TURNS:
            for duration in DURATIONS:
                if time.monotonic() >= deadline:
                    break
                if node.moving + duration > MAX_MOTION:
                    continue
                row = (float(target), .12, duration, 0)
                ss, _, mm = engine.simulate(node.origin, [row])
                a, b = bounds(ss, node.native)
                if a.min() < q.REQUIRED + MARGIN:
                    edge_rejections['static'] += 1
                    continue
                if b.min() < q.REQUIRED + MARGIN:
                    edge_rejections['dynamic'] += 1
                    continue
                org = endpoint(node.origin, ss, mm, True)
                add(Node(org, node.native+duration, node.moving+duration,
                         index, row, min(node.minimum, float(np.minimum(a, b).min()))))
    result = dict(passed=selected is not None and not static_only,
        static_connection_found=selected is not None if static_only else None,
        static_only=static_only, expanded=expansions, nodes=len(nodes),
        terminal_attempts=terminal_attempts, edge_rejections=edge_rejections,
        analytical_cpp_native=engine.native, best=best, wall_s=time.monotonic()-started,
        models=0, new_mujoco_native=0, physical_eligible=False,
        native_offset=native_offset, nominal_preview=origin is not None,
        stop_reason='SOURCE_FOUND' if selected else 'FINITE_SEARCH_NO_SOURCE',
        termination=dict(time=time.monotonic() >= deadline,
                         nodes=len(nodes) >= MAX_NODES,
                         expansions=expansions >= MAX_EXPANSIONS,
                         frontier_empty=not queue))
    if selected is not None:
        result.update(selected)
    return result


def select_observation_refuge(candidates, assess_onward):
    """Downstream assessment is mandatory; old guide proximity breaks ties only.

    assess_onward receives each full nominal candidate, including elapsed time
    and memory. It must use the current causal domain, never future recorded
    scans. A proposal/preview is never returned as physical authorization.
    """
    assessed = []
    for candidate in candidates:
        if not candidate['proof']['passed']:
            continue
        onward = assess_onward(candidate)
        assert onward.get('physical_eligible') is False
        rank = (not onward.get('passed', False),
                (onward.get('best') or {}).get('distance', float('inf')),
                candidate['guide_score'])
        assessed.append((rank, candidate, onward))
    if not assessed:
        return dict(passed=False, physical_eligible=False, assessed=0)
    rank, candidate, onward = min(assessed, key=lambda row: row[0])
    return dict(passed=bool(onward.get('passed')), candidate=candidate,
                onward=onward, assessed=len(assessed), physical_eligible=False,
                scope='nominal downstream-aware refuge proposal; fresh scan required')
