"""Only the new saved-list diagnostic view and its first-error persistence seam."""
import ast
import copy
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
from types import SimpleNamespace

C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v1557_source_common',C/'common.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def main():
    start=time.monotonic()
    assert sorted(os.sched_getaffinity(0))==[2] and os.environ.get('PHASE_REPO')==str(c.R)
    with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
        phase_FFI_loads=0,Allocator_recomputations=0,optimizer_calls=0,replay_native=0,old_policy_calls=0)
    class NoModels(importlib.abc.MetaPathFinder):
        def find_spec(self,name,*args):
            if name.split('.')[0] in {'jax','jaxlib','mujoco','torch','rclpy','runtime','bindings','kernel','prediction','coupled_model','vehicle','factory','gear_handoff'}:
                raise AssertionError('DIAGNOSTIC_VIEW_NO_MODEL_IMPORT:'+name)
    finder=NoModels();sys.meta_path.insert(0,finder)
    def profile(frame,event,arg):
        if event=='call':
            path=Path(frame.f_code.co_filename)
            if path.is_absolute()and path.is_relative_to(c.R):
                assert frame.f_code.co_name not in {'initial','step','select','simulate','compute','predict','expand','advance','load_definitions'}
                if frame.f_code.co_name=='__init__'and not path.is_relative_to(C):
                    raise AssertionError('DIAGNOSTIC_VIEW_NO_EXTERNAL_CONSTRUCTOR:'+str(path))
            assert time.monotonic()-start<120
    def audit_hook(event,args):
        if event=='ctypes.dlopen'and args and args[0]:
            path=Path(args[0]);assert not path.is_absolute()or not path.resolve().is_relative_to(c.R)
    sys.addaudithook(audit_hook);sys.setprofile(profile)
    try:
        bootstrap=c.bootstrap();c.guard()
        import numpy as np
        parent=c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json')
        assert parent['active_round']is None and parent['active_math_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==10
        source=c.read(c.BASE)['files'].copy()
        assert all(c.sha(c.R/name)==value for name,value in source.items())
        origin=c.load('v1557_production_origin_views',C/'origin.py')
        saved_path=c.R/'runs/v1554_lossless_witness_stream/model/CURRENT_ORIGIN.json'
        saved=c.read(saved_path)
        assert c.sha(saved_path)=='96fcf7ac232661c613d68b80d97bb56b821032a05c997206b2f7b048f2524823'
        assert saved['passed']is False and 'initial_state_bytes'not in saved
        saved_sha=c.sha(saved_path)
        original=copy.deepcopy(saved['origin']['state']);before=copy.deepcopy(original)
        assert isinstance(original,list)and len(original)==8
        a=origin.state_view(original);b=np.asarray(original,dtype=np.float64)
        assert a.shape==(8,)and a.dtype==np.float64 and a.tobytes()==b.tobytes()and not a.flags.writeable
        indices=[0,1,2,3,5]
        assert a[indices].tobytes()==b[indices].tobytes()and original==before
        flags=b.flags.writeable;raw=b.tobytes();v=origin.state_view(b)
        assert v is not b and np.shares_memory(v,b)and b.flags.writeable==flags and not v.flags.writeable
        readonly=b.view();readonly.setflags(write=False)
        assert origin.state_view(readonly).tobytes()==raw and not readonly.flags.writeable
        negative=[]
        try:a[0]=0.
        except ValueError:negative.append('diagnostic_view_write_refused')
        else:raise AssertionError('DIAGNOSTIC_VIEW_WRITABLE')
        try:origin.state_view(['malformed'])
        except ValueError:negative.append('malformed_scalar_refused')
        else:raise AssertionError('MALFORMED_SCALAR_ACCEPTED')
        try:origin.state_view(original[:3])[indices]
        except IndexError:negative.append('short_shape_index_refused')
        else:raise AssertionError('SHORT_STATE_INDEX_ACCEPTED')
        assert original==before and b.tobytes()==raw and b.flags.writeable==flags
        # The unmodified definition/projection already actually returned in
        # V1554. Reuse its proof and immutable input hashes; never call initial.
        defs_path=c.R/'runs/v1554_lossless_witness_stream/model/DEFINITION_BINDING.json'
        definitions=c.read(defs_path);assert definitions['passed']and not definitions['library_loaded_or_called']
        assert all(c.sha(c.R/name)==identity for name,identity in definitions['checked_files'].items())
        fixed=c.read(c.R/'runs/v1554_lossless_witness_stream/FIXED_INPUTS.json')
        assert c.sha(c.INPUT)==fixed['base_method_file_sha256']
        method_path=c.R/'runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json'
        method=c.read(method_path)
        assert c.sha(method_path)==fixed['response_method_file_sha256']and method['response_method_sha256']==fixed['response_method_sha256']
        # First-error closure is the real production prepare path, stopped
        # at its guard before definitions/runtime. No fake runtime function.
        target=c.O/'source_target';target.mkdir()
        def reject():raise RuntimeError('NEW_DIAGNOSTIC_SOURCE_FIRST')
        guard=SimpleNamespace(check=reject)
        received=[]
        def save(proof):received.append(copy.deepcopy(proof));c.put(target/'FIRST_ERROR.json',proof)
        try:origin.prepare(method,{},guard,save)
        except AssertionError as error:
            assert 'NEW_DIAGNOSTIC_SOURCE_FIRST'in str(error)and error.secondary is None
            assert received and received[0]['origin']is None and not received[0]['passed']
        else:raise AssertionError('SOURCE_FIRST_ERROR_LOST')
        def broken_save(proof):raise OSError('NEW_DIAGNOSTIC_SOURCE_SECONDARY')
        try:origin.prepare(method,{},guard,broken_save)
        except AssertionError as error:
            assert 'NEW_DIAGNOSTIC_SOURCE_FIRST'in str(error)and 'NEW_DIAGNOSTIC_SOURCE_SECONDARY'in error.secondary
            c.put(target/'FIRST_SECONDARY.json',dict(first_error=str(error),secondary_error=error.secondary,proof=error.proof))
        else:raise AssertionError('SOURCE_SECONDARY_ERROR_LOST')
        assert c.sha(saved_path)==saved_sha
        # Prove the numerical return/body is unchanged; only diagnostics use
        # a view. Equality compares the complete prepare AST after undoing
        # precisely this one diagnostic binding insertion.
        base=ast.parse((c.R/'experiments/v1552_complete_canonical_witness/origin.py').read_text())
        updated=ast.parse((C/'origin.py').read_text())
        old_prepare=next(n for n in base.body if isinstance(n,ast.FunctionDef)and n.name=='prepare')
        new_prepare=next(n for n in updated.body if isinstance(n,ast.FunctionDef)and n.name=='prepare')
        for node in ast.walk(new_prepare):
            for field,value in ast.iter_fields(node):
                if isinstance(value,list):
                    value[:]=[n for n in value if not(isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='state'for t in n.targets)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='state_view')]
        class UndoView(ast.NodeTransformer):
            def visit_Name(self,node):
                if node.id=='state'and isinstance(node.ctx,ast.Load):
                    return ast.Subscript(value=ast.Name(id='answer',ctx=ast.Load()),slice=ast.Constant(value='state'),ctx=ast.Load())
                return node
        new_prepare=UndoView().visit(new_prepare)
        assert ast.dump(old_prepare,include_attributes=False)==ast.dump(new_prepare,include_attributes=False)
        c.put(c.O/'FIXED_INPUTS.json',fixed)
        reuse=dict(origin_path=str(saved_path.relative_to(c.R)),origin_sha256=saved_sha,
            definitions_path=str(defs_path.relative_to(c.R)),definitions_sha256=c.sha(defs_path),
            old_missing_state_byte_proof_preserved=True,original_initial_not_called=True,
            source_only=True,numerical_origin_or_response_not_qualified=True)
        c.put(target/'REUSED_BINDING_PROOF.json',reuse)
        c.put(target/'QUALIFICATION.json',dict(passed=True,saved_list_diagnostic_bytes_hex=a.tobytes().hex(),
            shape=list(a.shape),dtype=str(a.dtype),list_and_array_bytes_equal=True,
            original_list_array_values_and_flags_unchanged=True,negative_cases=negative,
            first_secondary_saved=True,production_prepare_AST_only_diagnostic_view_change=True,
            original_return_unchanged=True,models=0,original_initial_calls=0))
        for path in C.iterdir():
            if path.is_file():
                if path.suffix=='.py':ast.parse(path.read_text())
                source[str(path.relative_to(c.R))]=c.sha(path)
        for path in [c.O/'FIXED_INPUTS.json',target/'REUSED_BINDING_PROOF.json',saved_path,defs_path]:
            source[str(path.relative_to(c.R))]=c.sha(path)
        assert all(c.sha(c.R/name)==identity for name,identity in source.items())
        c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
            source_only=True,models_authorized=False,complete_numeric_response_qualified=False),maximum=4*1024**2)
        result.update(passed=True,source_frozen=True,source_members=len(source),bootstrap=bootstrap,
            source_only=True,negative_cases=len(negative),old_initial_calls=0,old_definition_or_serializer_suite_rerun=False)
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder)
        result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
