"""Exact original allocator methods, with unused prediction imports excluded.

This binding is restricted to the current <=.1m/s unguarded controller episode.
It never constructs a vehicle/model or calls an analytical speed predictor.
Saved-history output equivalence is checked before using this binding further.
"""
import ast
import importlib.util
import sys
import types
from pathlib import Path
R=Path(__file__).resolve().parents[2]
FORBIDDEN_PREVIEW_CALLS=[]


def forbidden(*args,**kwargs):
    FORBIDDEN_PREVIEW_CALLS.append(True)
    raise AssertionError('NO_PREDICTION_IN_METADATA_QUALIFICATION')


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,R/path)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value
    spec.loader.exec_module(value)
    return value


def binding():
    assert 'kernel' not in sys.modules and 'braking_reserve' not in sys.modules
    import json
    signed=module('clock_original_signed','experiments/v1035_signed_timed_input_source/signed_control.py')
    kernel=types.ModuleType('kernel')
    kernel.PARAMETERS=json.loads((R/'experiments/v1044_curvature_speed_prediction/PARAMETERS.json').read_text())
    kernel.law=signed
    sys.modules['kernel']=kernel
    path=R/'experiments/rpccr_execution_core/braking_reserve.py'
    tree=ast.parse(path.read_text())
    # This import otherwise loads a predictor just to define speed_terms. The
    # selected episode never calls that dependency; make any attempted use fail.
    removed=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='old' for t in n.targets)]
    assert len(removed)==1
    tree.body=[n for n in tree.body if n not in removed]
    reserve=types.ModuleType('braking_reserve');reserve.__file__=str(path)
    reserve.old=types.SimpleNamespace(speed_terms=forbidden)
    sys.modules['braking_reserve']=reserve
    exec(compile(tree,str(path),'exec'),reserve.__dict__)
    reserve.braking_upper=forbidden
    module('parked_control','experiments/v1108_parked_steering_handoff/parked_control.py')
    coupled=module('clock_original_coupled','experiments/v1114_coupled_steering_mode/coupled_control.py')
    return coupled.Adapter
