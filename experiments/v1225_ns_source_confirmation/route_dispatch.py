"""Bind two unchanged, qualified executors to one explicit current window."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import types

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent


def checked(path):
    expected = json.loads((C / 'PARENT_BINDINGS.json').read_text())['files']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected[str(path.relative_to(R))], 'PARENT_SOURCE_CHANGED'
    return path.read_text()


def load_legacy_tools():
    path = R / 'experiments/v1184_three_route_entry/route_tools.py'
    checked(path)
    name = 'v1225_immutable_legacy_route_tools'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def legacy_policy(remaining_fn):
    assert callable(remaining_fn), 'EXPLICIT_CURRENT_WINDOW_REQUIRED'
    path = R / 'experiments/v1184_three_route_entry/route_policy.py'
    source = checked(path)
    assert source.count('from route_tools import *') == 1
    module = types.ModuleType('v1225_bound_legacy_policy')
    module.__dict__.update(vars(load_legacy_tools()))
    module.__file__ = str(path)
    module.remaining = lambda w=None: remaining_fn() if w is None else (_ for _ in ()).throw(AssertionError('LEGACY_WINDOW_OVERRIDE_FORBIDDEN'))
    exec(compile(source.replace('from route_tools import *', ''), str(path), 'exec'), module.__dict__)
    return module


def branch(case):
    assert case in {'NORTH_SOUTH', 'EAST_WEST', 'WEST_EAST'}, 'UNREGISTERED_ROUTE'
    return {'WEST_EAST':'current_goal','NORTH_SOUTH':'ns_goal','EAST_WEST':'legacy_route'}[case]


def current_executor():
    path=C/'live_entry.py'
    checked(path)
    name='phase_v1225_live_executor'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    module=sys.modules[name]
    assert Path(module.__file__).resolve()==path,'CURRENT_EXECUTOR_IMPORT_COLLISION'
    return module


def ns_executor():
    path=C/'ns_live.py';checked(path)
    name='phase_v1225_ns_live'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
    m=sys.modules[name];assert Path(m.__file__).resolve()==path
    return m

def execute(v, setup, original, end, evidence, out, packet_fn, output, *, remaining_fn):
    assert callable(remaining_fn) and remaining_fn() > 0, 'CURRENT_WINDOW_EXPIRED'
    if branch(setup['case']['id']) == 'ns_goal':
        return ns_executor().execute(v,setup,original,end,evidence,out,packet_fn,output=output,remaining_fn=remaining_fn)
    if branch(setup['case']['id']) == 'current_goal':
        return current_executor().execute(v, setup, original, end, evidence, out, packet_fn,
                                          output=output, remaining_fn=remaining_fn)
    policy = legacy_policy(remaining_fn)
    return policy.execute(v, setup, original, end, evidence, out, packet_fn, output=output)
