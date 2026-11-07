"""Registered causal saved inputs and finite proposal parameters; no truth access."""
import hashlib
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / 'runs/v842_staged_long_navigation/v843_main_slot02/paired/geometry_memory'
STEPS = (374, 683, 893, 1198)
BATCH, HORIZON, PATH_NODES = 512, 42, 128


def parameters():
    # Fixed finite proposal noise, unrelated to environment/noise/confirmation seeds.
    rng = np.random.default_rng(84420261106)
    offsets = np.repeat(rng.normal(0., .12, (BATCH, 7)), 6, axis=1)
    wheels = np.repeat(rng.uniform(2., 12., (BATCH, 7)), 6, axis=1)
    follow = np.ones(BATCH, dtype=bool)
    lookahead = np.where(np.arange(BATCH) % 2, .55, .35)
    brakes = np.asarray([20, 26, 30])[np.arange(BATCH) % 3]
    index = 0
    for steer in np.linspace(-.42722137342572125, .42722137342572125, 7):
        for wheel in [-12., -8., -4., 0., 4., 8., 12.]:
            for brake in [20, 26, 30]:
                offsets[index] = steer
                wheels[index] = wheel
                follow[index] = False
                brakes[index] = brake
                index += 1
    for look in [.35, .55]:
        for wheel in [4., 8., 12.]:
            for brake in [20, 26, 30]:
                offsets[index] = 0.
                wheels[index] = wheel
                lookahead[index] = look
                brakes[index] = brake
                index += 1
    return dict(offsets=offsets, wheels=wheels, follow=follow,
                lookahead=lookahead, brakes=brakes)


def load():
    trace = json.loads((RAW / 'trace.json').read_text())
    contract = json.loads((RAW / 'ACTUATOR_COMMAND_CONTRACT.json').read_text())
    cases = []
    sources = []
    for step in STEPS:
        source = RAW / f'planning_{step:04d}.json'
        row = json.loads(source.read_text())
        world = row['causal_route_input']
        assert row['stats']['status'] == 'SAFE_PROGRESS_PREFIX'
        assert row['stats']['spatial_soft_reference']['forward_reference_selected']
        reference = np.asarray(row['path'], dtype=np.float64)
        assert len(reference) >= 2
        # The qualification follows the currently active first gear segment only.
        gear = reference[1, 3]
        end = 1
        while end + 1 < len(reference) and reference[end + 1, 3] == gear:
            end += 1
        reference = reference[:end + 1]
        if len(reference) > PATH_NODES:
            reference = reference[:PATH_NODES]
        path = np.repeat(reference[-1:, :3], PATH_NODES, axis=0)
        path[:len(reference)] = reference[:, :3]
        rectangles = np.tile([1000., 1000., .01, .01], (32, 1))
        circles = np.tile([1000., 1000., 0.], (32, 1))
        assert len(world['rectangles']) <= 32 and len(world['circles']) <= 32
        rectangles[:len(world['rectangles'])] = world['rectangles']
        circles[:len(world['circles'])] = world['circles']
        bounds = np.asarray(world['footprint_bounds'])
        cases.append(dict(step=step, pose=np.asarray(row['pose'], dtype=np.float64),
                          last=np.asarray(trace[step - 1]['applied_ctrl'][:4], dtype=np.float64),
                          goal=np.asarray(world['goal'], dtype=np.float64), path=path,
                          rectangles=rectangles, circles=circles,
                          half=(bounds[2:] - bounds[:2]) / 2,
                          lower=np.asarray(contract['limits'])[:, 0],
                          upper=np.asarray(contract['limits'])[:, 1],
                          rate=np.asarray(contract['rate']),
                          path_nodes=len(reference), gear=float(gear)))
        sources.append(dict(path=str(source.relative_to(REPO)),
                            sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    for name in ['trace.json', 'ACTUATOR_COMMAND_CONTRACT.json']:
        source = RAW / name
        sources.append(dict(path=str(source.relative_to(REPO)),
                            sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    return cases, sources
