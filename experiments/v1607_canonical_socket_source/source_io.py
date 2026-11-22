"""Bounded source records. Hashes bind bytes; they do not confer authority."""
import hashlib
import importlib.util
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def exact(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_bound(path, *, maximum, expected_sha256):
    path = Path(path)
    assert path.is_absolute() and path.is_relative_to(R / 'runs')
    assert path.resolve() == path and not path.is_symlink(), 'SOURCE_PATH_ESCAPE'
    with path.open('rb') as stream:
        data = stream.read(maximum + 1)
    assert len(data) <= maximum, 'SOURCE_RECORD_CAP'
    assert hashlib.sha256(data).hexdigest() == expected_sha256, 'SOURCE_BYTES_CHANGED'
    return json.loads(data)
