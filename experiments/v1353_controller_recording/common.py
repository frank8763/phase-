"""Reuse the fixed V1352 data logic; only structured ROS result encoding changes."""
import importlib.util
from pathlib import Path

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name
BASE = R / 'experiments/v1352_shared_controller_probe'


def base_module(name):
    spec = importlib.util.spec_from_file_location('phase_v1352_' + name, BASE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_data = base_module('common')
json, math, read, sha, digest, load_contract = _data.json, _data.math, _data.read, _data.sha, _data.digest, _data.load_contract


def plain(value):
    if value is None or type(value) in (bool, int, float, str):
        return value
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if hasattr(value, 'get_fields_and_field_types'):
        return {key: plain(getattr(value, key)) for key in value.get_fields_and_field_types()}
    raise TypeError('UNSUPPORTED_RESULT_TYPE ' + type(value).__name__)


def dump(path, value):
    _data.dump(path, plain(value))


def hashes_ok():
    return all(sha(R / p) == h for p, h in read(C / 'SOURCE_FREEZE.json')['files'].items())
