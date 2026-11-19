"""Data-only boundary for the fixed shared-controller software probe."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def load_contract():
    spec = importlib.util.spec_from_file_location('phase_shared_contract', R / 'experiments/v1288_baseline_interface/contract.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def first_segment(path):
    assert len(path) >= 2 and all(len(p) == 4 and all(math.isfinite(x) for x in p) and p[3] in [-1, 1] for p in path)
    gear = int(path[1][3])
    end = len(path)
    for i in range(2, len(path)):
        if int(path[i][3]) != gear:
            end = i
            break
    return dict(gear=gear, poses=[p[:3] for p in path[:end]])


def raster_ball(grid, ball):
    result = dict(grid, data=list(grid['data']))
    x, y, radius = ball
    ox, oy = grid['origin'][:2]
    res = grid['resolution']
    count = 0
    for j in range(grid['height']):
        low_y = oy + j * res
        dy = max(low_y-y, y-low_y-res, 0.)
        for i in range(grid['width']):
            low_x = ox + i * res
            dx = max(low_x-x, x-low_x-res, 0.)
            if dx*dx + dy*dy <= radius*radius + 1e-14:
                result['data'][j*grid['width']+i] = 100
                count += 1
    return result, count


def hashes_ok():
    return all(sha(R / p) == h for p, h in read(C / 'SOURCE_FREEZE.json')['files'].items())
