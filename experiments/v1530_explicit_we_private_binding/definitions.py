"""Exact original definition imports in one fresh CPU2 process; no execution.

This preserves the original import statements and numerical bodies. Existing
generic module names are refused, never replaced. No origin or method-state
epoch can be constructed or authorized through this definitions-only seam.
"""
import fcntl
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import sys
import time
import types

R = Path(__file__).resolve().parents[2]
FILES = {
    'resource_policy': 'experiments/v1067_causal_replan_brake_reserve/resource_policy.py',
    'runtime': 'experiments/v1118_coupled_live_qualification/runtime.py',
    'bindings': 'experiments/v1117_fixed_tick_native_sqp/bindings.py',
    'kernel': 'experiments/v1067_causal_replan_brake_reserve/kernel.py',
    'common': 'experiments/v1114_coupled_steering_mode/common.py',
    'coupled_model': 'experiments/v1114_coupled_steering_mode/coupled_model.py',
    'coupled_control': 'experiments/v1114_coupled_steering_mode/coupled_control.py',
    'prediction': 'experiments/rpccr_execution_core/prediction.py',
    'parked_control': 'experiments/v1108_parked_steering_handoff/parked_control.py',
    'braking_reserve': 'experiments/rpccr_execution_core/braking_reserve.py',
    'whole_input': 'experiments/v1046_retreat_entry_timed_route/whole_input.py',
    'fast_predict': 'experiments/v1046_retreat_entry_timed_route/fast_predict.py',
}
MODEL = 'experiments/v1159_bounded_steering_load/model.py'
ENGINE = 'experiments/v1159_bounded_steering_load/engine.py'
PARAMETERS = 'experiments/v1159_bounded_steering_load/PARAMETERS.json'
LIBRARY = 'runs/v1159_bounded_steering_load/profile.so'
PRIVATE_NAMES = ('phase_v1530_exact_v1159_model', 'phase_v1530_exact_v1159_engine')
COLLISION_NAMES = tuple(k for k in FILES if k != 'resource_policy') + PRIVATE_NAMES + (
    'geometry_model', 'timed_input', 'exact_timed', 'logic', 'source', 'solver',
    'qualify', 'tracking', 'capture', 'current_state_tools', 'chain', 'chain_tools',
    'recovery_tools', 'science', 'worker', 'campaign', 'vehicle', 'factory',
)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def preflight(prepared_sources, *, modules=None):
    modules = sys.modules if modules is None else modules
    collisions = [name for name in COLLISION_NAMES if name in modules]
    assert not collisions, ('ORIGINAL_WE_DEFINITION_NAMESPACE_NOT_FRESH', collisions)
    checked = {}
    for name in [*FILES.values(), MODEL, ENGINE, PARAMETERS, LIBRARY]:
        path = R / name
        assert path.is_file() and not path.is_symlink()
        identity = sha(path)
        assert prepared_sources[name] == identity, ('ORIGINAL_WE_SOURCE_IDENTITY_CHANGED', name)
        checked[name] = identity
    resource = modules.get('resource_policy')
    if resource is not None:
        assert Path(resource.__file__).resolve() == R / FILES['resource_policy']
        assert resource._pid == os.getpid() and resource._state['cpu_affinity'] == [2]
    return checked


def bootstrap(prepared_sources):
    """Original resource bootstrap only; call before immutable writeguard."""
    assert os.environ.get('PHASE_REPO') == str(R)
    assert sorted(os.sched_getaffinity(0)) == [2]
    checked = preflight(prepared_sources)
    sys.path.insert(0, str((R / FILES['resource_policy']).parent))
    resource = importlib.import_module('resource_policy')
    assert Path(resource.__file__).resolve() == R / FILES['resource_policy']
    value = resource.apply()
    assert value['cpu_affinity'] == [2] and value['nice'] == 19
    assert value['gpu_visible'] == '' and value['mujoco_gl'] == 'osmesa'
    return dict(resource=value, original_source_sha256=checked[FILES['resource_policy']],
                bootstrap_only=True, model_definitions_loaded=False)


def code_identity(function, expected_file):
    """Compare original full-module code, including future/nested constants."""
    path = R / expected_file
    assert Path(function.__code__.co_filename).resolve() == path
    tree = compile(path.read_text(), str(path), 'exec', dont_inherit=True)
    wanted = function.__qualname__.split('.')
    current = tree
    for name in wanted:
        choices = [x for x in current.co_consts if isinstance(x, types.CodeType) and x.co_name == name]
        assert len(choices) == 1, ('ORIGINAL_WE_CODE_AMBIGUOUS', expected_file, wanted)
        current = choices[0]
    assert current == function.__code__, ('ORIGINAL_WE_CODE_IDENTITY', expected_file, wanted)
    return dict(file=expected_file, qualname=function.__qualname__, flags=current.co_flags,
                source_sha256=sha(path), full_module_code_identity=True)


def load_definitions(prepared_sources, *, authority, lock):
    """Return definitions/proof only; the returned classes grant no authority.

    The owner must keep its constructor/step/FFI ban active while inspecting
    these definitions. Every future numerical scope needs a different authority.
    """
    assert authority['scope'] == 'ORIGINAL_WE_DEFINITIONS_ONLY'
    assert authority['models_authorized'] is False and authority['method_origin_authorized'] is False
    assert authority['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    assert time.time() < authority['absolute_deadline_unix'] <= 1795395600
    assert time.monotonic() < authority['hard_stop_monotonic']
    assert os.environ.get('PHASE_REPO') == str(R) and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert sorted(os.sched_getaffinity(0)) == [2]
    assert Path('/proc/self/fd/' + str(lock.fileno())).resolve() == R / 'runs/v648_static_unknown/execution.lock'
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    checked = preflight(prepared_sources)
    resource = sys.modules.get('resource_policy')
    assert resource is not None and resource._pid == os.getpid(), 'ORIGINAL_WE_RESOURCE_BOOTSTRAP_MISSING'
    original_path = list(sys.path)
    before = set(sys.modules)
    try:
        # Pin the operational globals before any old transitive source can
        # resolve a different generic common.py. No existing name is replaced.
        sys.path.insert(0, str((R / FILES['common']).parent))
        common = importlib.import_module('common')
        assert Path(common.__file__).resolve() == R / FILES['common']
        sys.path.insert(0, str((R / FILES['runtime']).parent))
        runtime = importlib.import_module('runtime')
        imported = {}
        for name, relative in FILES.items():
            module = sys.modules[name]
            assert Path(module.__file__).resolve() == R / relative, ('ORIGINAL_WE_IMPORT_COLLISION', name)
            assert sha(R / relative) == prepared_sources[relative]
            imported[name] = module
        exact = []
        for name, relative in zip(PRIVATE_NAMES, [MODEL, ENGINE]):
            assert name not in sys.modules
            spec = importlib.util.spec_from_file_location(name, R / relative)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            exact.append(module)
        model, engine = exact
        bindings = imported['bindings']
        coupled = imported['coupled_model']
        assert model.Original is runtime.Predictor
        assert runtime.QualifiedPredictor is bindings.Predictor is coupled.Predictor
        assert coupled.Original is imported['prediction'].Predictor
        assert imported['prediction'].Legacy is imported['kernel'].Predictor
        assert bindings.Adapter is imported['coupled_control'].Adapter
        assert coupled.Adapter is bindings.Adapter
        assert model.BASE is engine.PARAMETERS is bindings.PARAMETERS is imported['kernel'].PARAMETERS
        assert model.virtual is imported['kernel'].virtual
        functions = [(model.Predictor.__init__, MODEL), (model.Predictor.step, MODEL),
                     (model.rate_law, MODEL), (engine.Engine.__init__, ENGINE),
                     (engine.Engine.simulate, ENGINE), (runtime.Predictor.__init__, FILES['runtime']),
                     (runtime.initial, FILES['runtime']), (coupled.Predictor.step, FILES['coupled_model']),
                     (coupled.initial, FILES['coupled_model']),
                     (bindings.Adapter.compute, FILES['coupled_control'])]
        identities = [code_identity(fn, path) for fn, path in functions]
        new_module_sources = {}
        for name in sorted(set(sys.modules) - before):
            module = sys.modules[name]
            filename = getattr(module, '__file__', None)
            if filename and Path(filename).resolve().is_relative_to(R):
                relative = str(Path(filename).resolve().relative_to(R))
                assert prepared_sources[relative] == sha(R / relative), ('UNDECLARED_IMPORTED_PHASE_SOURCE', name, relative)
                new_module_sources[name] = dict(path=relative, sha256=prepared_sources[relative])
        assert all(sha(R / name) == identity for name, identity in checked.items())
        proof = dict(passed=True, scope='ORIGINAL_WE_DEFINITIONS_ONLY', checked_files=checked,
                     imported_modules={name:FILES[name] for name in imported},
                     additional_registered_module_sources=new_module_sources,
                     exact_function_code=identities, original_V1159_V1118_V1114_inheritance=True,
                     original_parameters_and_virtual_identity=True,
                     library_sha256=checked[LIBRARY], library_loaded_or_called=False,
                     original_numerical_bodies_unmodified=True,
                     complete_dynamic_callgraph_qualified=False, method_epoch_qualified=False,
                     numerical_origin_conversion_qualified=False,
                     models_authorized=False, method_origin_authorized=False,
                     physical_or_navigation_admission=False)
        return dict(model=model, engine=engine, runtime=runtime, bindings=bindings,
                    kernel=imported['kernel'], Adapter=bindings.Adapter), proof
    finally:
        sys.path[:] = original_path


def create_origin(*args, **kwargs):
    raise AssertionError('ORIGINAL_WE_METHOD_EPOCH_AND_NUMERIC_SCOPE_NOT_QUALIFIED')


def construct_predictor(*args, **kwargs):
    raise AssertionError('ORIGINAL_WE_MODEL_CONSTRUCTION_NOT_ADMITTED')


def construct_engine(*args, **kwargs):
    raise AssertionError('ORIGINAL_WE_FFI_CONSTRUCTION_NOT_ADMITTED')
