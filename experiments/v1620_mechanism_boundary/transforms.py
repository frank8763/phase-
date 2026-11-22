"""Narrow, SHA-bound ablations; never execute a legacy module or model here."""
import ast
import copy
import hashlib
import types
from spec import R, C, digest

TIMING = 'experiments/v1271_ew_joint_phase_validation/timed_source.py'
ONWARD = 'experiments/v1218_fixed24_current/goal_package/current_goal_source.py'


def transformed(source, kind, variant):
    tree = ast.parse(source)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'generate')
    fn = copy.deepcopy(fn)
    if kind == 'time':
        assert variant == 'no_time'
        candidates = [n for n in ast.walk(fn) if isinstance(n, ast.If) and
                      ast.unparse(n.test) == 'passed and (rank is None or (-slack, wait) < rank)']
        assert len(candidates) == 1, 'TIMING_SELECTION_SOURCE_SEAM_CHANGED'
        original = copy.deepcopy(candidates[0].test)
        candidates[0].test = ast.BoolOp(op=ast.And(), values=[
            ast.Compare(left=ast.Name(id='wait', ctx=ast.Load()),
                        ops=[ast.Eq()], comparators=[ast.Constant(0)]), original])
        # Every original evaluation/proof remains; only the eligible wait changes.
        assert sum(isinstance(n, ast.For) and ast.unparse(n.iter) == 'range(0, 2000, 50)'
                   for n in ast.walk(fn)) == 1
    else:
        assert kind == 'onward' and variant == 'no_onward'
        loops = [n for n in ast.walk(fn) if isinstance(n, ast.For) and
                 ast.unparse(n.target) == '(i, c)' and
                 ast.unparse(n.iter) == 'enumerate(candidates[:8])']
        assert len(loops) == 1, 'ONWARD_SOURCE_SEAM_CHANGED'
        # Qualify the selected PREFIX with the original feedback/continuous
        # shadow/complete stop checker, using its own endpoint only as that
        # prefix's terminal. The actual task goal x is not modified. The real
        # measured-handoff generate(onward_only=True) remains mandatory.
        loops[0].body = ast.parse('''
if time.monotonic() >= fallback_end:
    break
k = len(c['controls'])
prefix_input = copy.deepcopy(x)
prefix_input['goal'] = c['states'][-1,:2].tolist()
prefix_admission, _ = feedback_preview(prefix_input, table, origin,
    shadow_origin, offset, c, deadline)
preview_work += prefix_admission['python_native']
attempts.append(dict(refuge=i, passed=False,
    preexecution_onward_preview_removed=True,
    prefix_feedback_shadow_admission=prefix_admission))
if not prefix_admission['passed']:
    continue
selected = dict(rows=c['rows'],states=c['states'],controls=c['controls'],
    memory=c['memory'],proof=c['record']['proof'],admission=prefix_admission,
    prefix_rows=c['rows'],prefix_native=k,composition_error=None,
    selected_refuge=i,measured_onward_still_required=True,
    prefix_counts_as_whole_arrival=False)
break
''').body
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    return module, dict(kind=kind, variant=variant,
                        original_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                        transformed_AST_sha256=digest(ast.dump(module, include_attributes=False)),
                        legacy_module_executed=False, numerical_qualified=False,
                        physical_authorized=False)


def bind(original_module, prepared_sources, *, kind, variant):
    """Explicit future-driver API; model/actual authority belongs to its owner."""
    relative = TIMING if kind == 'time' else ONWARD
    path = R/relative
    identity = hashlib.sha256(path.read_bytes()).hexdigest()
    assert prepared_sources[relative] == identity
    assert original_module.generate.__code__.co_filename == str(path)
    if variant == 'full':
        return original_module.generate, dict(original_function_identity=True,
            variant='full', source_sha256=identity, physical_authorized=False)
    module, proof = transformed(path.read_text(), kind, variant)
    namespace = vars(original_module).copy()
    before = original_module.generate
    exec(compile(module, str(C/('generated_'+kind+'.py')), 'exec'), namespace)
    result = namespace['generate']
    assert isinstance(result, types.FunctionType) and original_module.generate is before
    return result, proof
