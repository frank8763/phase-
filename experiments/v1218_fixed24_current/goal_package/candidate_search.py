"""Balanced search with explicit analytical endpoint/time preview, never a fake scan."""
from dataclasses import dataclass
from pathlib import Path
import heapq
import copy
import math
import sys
import time

R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R/'experiments/v1198_control_space_connection'))
sys.path.insert(0, str(R/'experiments/v1186_live_observer_regeneration'))
from current_state_tools import q, np
from .connection import Node, TURNS, DURATIONS, endpoint, state_key, path_rows, compact
from current_state_tools import validate_input
from .connection import OffsetGeometry


class PreviewGeometry(OffsetGeometry):
    @property
    def period(self):
        return self.geometry.period


@dataclass
class TimedNode(Node):
    phase: int
    shadow_origin: dict


def search(x, table, deadline, checkpoint=lambda _:None, *, preview=None, admit=None, expansion_limit=3000):
    validate_input(x)
    assert type(expansion_limit)is int and 0<expansion_limit<=3000
    native_offset = 0 if preview is None else preview['native_offset']
    assert type(native_offset) is int and native_offset >= 0
    origin = (dict(q.initial(x['packet']), steering_load_episode=False)
              if preview is None else copy.deepcopy(preview['origin']))
    shadow_origin=copy.deepcopy(origin if preview is None else preview.get('shadow_origin',origin))
    origin['state'] = np.asarray(origin['state'], float)
    origin['last_ctrl'] = np.asarray(origin['last_ctrl'], float)
    assert origin['state'].shape == (8,) and origin['last_ctrl'].shape == (4,)
    assert np.isfinite(origin['state']).all() and np.isfinite(origin['last_ctrl']).all()
    assert np.isfinite(origin['integral'])
    assert type(origin['steering_load_episode']) is bool
    assert not origin.get('coupled_episode', False)
    assert not origin.get('steering_motion_active', False)
    geometry = PreviewGeometry(q.Geometry(x, table), native_offset)
    proof_input = copy.deepcopy(x)
    proof_input['packet']['controller_memory']['last_ctrl'] = origin['last_ctrl'].tolist()
    engine = q.accelerator.Engine(x['setup'], q.model.parameters()['coefficients'])
    limits = np.asarray(x['setup']['limits'])
    rates = np.asarray(x['setup']['slew_per_second'])*.01
    waits = list(range(0, min(2000, int(geometry.period/.01))+1, 100))
    frontiers = [[] for _ in waits]
    visited = [{} for _ in waits]
    expanded = [0 for _ in waits]
    nodes = []
    terminal_attempts = 0
    rejected = dict(body_or_control=0, static=0, dynamic=0)
    best = None
    selected = None
    admission_records = []
    started = time.monotonic()

    def legal(states, controls, initial):
        return bool(np.isfinite(states).all() and np.isfinite(controls).all()
            and abs(states[:,3]).max() <= .13
            and abs(states[:,4]).max() <= .03
            and abs(states[:,5]).max() <= .16
            and (controls >= limits[:,0]-1e-10).all()
            and (controls <= limits[:,1]+1e-10).all()
            and (abs(np.diff(np.vstack([initial['last_ctrl'], controls]), axis=0)) <= rates+1e-10).all())

    def margins(states, native):
        return geometry.components(states[:,:3], np.arange(len(states))+native)

    def score(node):
        state = node.origin['state']
        delta = np.asarray(x['goal'])-state[:2]
        direction = math.atan2(delta[1], delta[0])
        angle = abs(math.atan2(math.sin(direction-state[2]), math.cos(direction-state[2])))
        return .01*node.moving + 2.2*float(np.linalg.norm(delta))/.12 + 1.2*angle

    def add(node):
        if len(nodes) >= 48000:
            return
        shadow_node=Node(node.shadow_origin,node.native,node.moving,node.parent,node.row,node.minimum)
        key = (state_key(node, x['packet']['sim_time']+.01*native_offset, geometry.period),
               state_key(shadow_node,x['packet']['sim_time']+.01*native_offset,geometry.period))
        old = visited[node.phase].get(key)
        if old is not None and old <= node.moving:
            return
        visited[node.phase][key] = node.moving
        index = len(nodes)
        nodes.append(node)
        heapq.heappush(frontiers[node.phase], (score(node), index))

    for phase, wait in enumerate(waits):
        if time.monotonic() >= deadline:
            break
        if wait:
            ss, uu, mm = engine.simulate(origin, [(0.,0.,wait,0)])
            if not legal(ss, uu, origin):
                continue
            initial = endpoint(origin, ss, mm, False)
            shadow_ss,shadow_uu,shadow_mm=engine.simulate(shadow_origin,[(0.,0.,wait,0)])
            if not legal(shadow_ss,shadow_uu,shadow_origin):continue
            shadow_initial=endpoint(shadow_origin,shadow_ss,shadow_mm,False)
        else:
            ss = origin['state'][None,:]
            initial = origin
            shadow_ss=np.asarray(shadow_origin['state'])[None,:];shadow_initial=shadow_origin
        static, dynamic = margins(ss, 0)
        sh_static,sh_dynamic=margins(shadow_ss,0)
        lower = float(min(np.minimum(static,dynamic).min(),np.minimum(sh_static,sh_dynamic).min()))
        if lower >= q.REQUIRED+.002:
            add(TimedNode(initial, wait, 0, -1,
                          (0.,0.,wait,0) if wait else None, lower, phase,shadow_initial))

    while sum(expanded) < expansion_limit and len(nodes) < 48000 and time.monotonic() < deadline:
        active = [p for p, queue in enumerate(frontiers) if queue]
        if not active:
            break
        # Each active initial phase receives the same expansion opportunity.
        phase = min(active, key=lambda p:(expanded[p], frontiers[p][0][0], p))
        _, index = heapq.heappop(frontiers[phase])
        node = nodes[index]
        state = node.origin['state']
        distance = float(np.linalg.norm(state[:2]-x['goal']))
        if best is None or distance < best['distance']:
            best = dict(distance=distance, state=state.tolist(), native=node.native,
                        rows=path_rows(nodes,index), minimum=node.minimum, phase=phase)
            checkpoint(dict(expanded=sum(expanded), phase_expanded=expanded.copy(),
                            nodes=len(nodes), best=best, cpp_native=engine.native))
        if distance <= .35 and terminal_attempts < 64:
            if min(float(geometry.cycle(state[None,:3])[0]),float(geometry.cycle(np.asarray(node.shadow_origin['state'])[None,:3])[0])) >= q.REQUIRED-.03:
                terminal_attempts += 1
                rows = compact(path_rows(nodes,index)+[(0.,0.,2200,0)])
                ss, uu, mm = engine.simulate(origin, rows)
                proof = q.proof(geometry,proof_input,ss,uu,q.requests_of(rows),mm)
                shadow_ss,_,_=engine.simulate(shadow_origin,rows)
                shadow_proof=q.proof(geometry,proof_input,shadow_ss,uu,q.requests_of(rows),mm)
                if proof['passed'] and shadow_proof['passed']:
                    candidate = dict(rows=rows, states=ss, controls=uu, memory=mm,
                                     proof=proof, initial_wait=waits[phase])
                    admission = dict(passed=True, legacy_nominal_only=True) if admit is None else admit(candidate)
                    admission_records.append(admission)
                    if admission['passed']:
                        selected = dict(candidate, admission=admission)
                        break
        expanded[phase] += 1
        for target in TURNS:
            for count in DURATIONS:
                if node.moving+count > 6000 or time.monotonic() >= deadline:
                    continue
                row = (float(target),.12,count,0)
                ss, uu, mm = engine.simulate(node.origin,[row])
                if not legal(ss,uu,node.origin):
                    rejected['body_or_control'] += 1
                    continue
                shadow_ss,shadow_uu,shadow_mm=engine.simulate(node.shadow_origin,[row])
                if not legal(shadow_ss,shadow_uu,node.shadow_origin):
                    rejected['body_or_control']+=1;continue
                static,dynamic = margins(ss,node.native)
                sh_static,sh_dynamic=margins(shadow_ss,node.native)
                static=np.minimum(static,sh_static);dynamic=np.minimum(dynamic,sh_dynamic)
                if static.min() < q.REQUIRED+.002:
                    rejected['static'] += 1
                    continue
                if dynamic.min() < q.REQUIRED+.002:
                    rejected['dynamic'] += 1
                    continue
                initial = endpoint(node.origin,ss,mm,True)
                add(TimedNode(initial,node.native+count,node.moving+count,index,row,
                    min(node.minimum,float(np.minimum(static,dynamic).min())),phase,endpoint(node.shadow_origin,shadow_ss,shadow_mm,True)))
    result = dict(passed=selected is not None, best=best, phase_expanded=expanded,
        nodes=len(nodes),terminal_attempts=terminal_attempts,rejected=rejected,
        analytical_cpp_native=engine.native,wall_s=time.monotonic()-started,
        models=0,new_mujoco_native=0,physical_eligible=False,
        nominal_preview=preview is not None, native_offset=native_offset,admission_records=admission_records,
        scope='exposed-state nominal source only; no robust or physical acceptance')
    if selected is not None:
        result.update(selected)
    return result
