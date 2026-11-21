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
spec=importlib.util.spec_from_file_location('v1559_source_common',C/'common.py')
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
                    assert path in {c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py'}
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
        module=c.load('v1559_complete_causal_record',C/'witness.py')
        codec=c.load('v1559_original_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
        writer_module=c.load('v1559_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
        io=c.load('v1559_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
        old=c.R/'experiments/v1557_origin_diagnostic_views'
        for name in ['driver.py','origin.py','stream.py','capability.py','owner.py','source_owner.py','LIMITS.json']:
            assert(C/name).read_bytes()==(old/name).read_bytes()
        # Complete exact saved source, not a synthesized forecast or new math.
        saved=c.R/'runs/v1542_parent_preparation_payloads/model/GENERATION_CAUSAL_SOURCE.json'
        assert c.sha(saved)=='3dfaad4c2675940105420090c66f8f13f3afe4cf81ec202cf489eeed9ea65a0f'
        value=c.read(saved);encoded=codec.encoded(value)
        assert len(encoded)==42025 and 16384<len(encoded)<=128*1024
        method_path=c.R/'runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json'
        method=c.read(method_path)
        assert value['input_periodic']==method['base_method']['physical_source']['causal_snapshot']['periodic']
        assert value['coefficient_snapshot_sha256']==method['causal_snapshot_sha256']
        fixed=c.read(c.R/'runs/v1557_origin_diagnostic_views/FIXED_INPUTS.json')
        assert c.sha(c.INPUT)==fixed['base_method_file_sha256']and c.sha(method_path)==fixed['response_method_file_sha256']
        target=c.O/'source_target';target.mkdir()
        complete=target/'complete';complete.mkdir()
        writer=writer_module.WriterBudget(complete,role='PLANNER',maximum_bytes=32*1024**2,source_identity=c.digest(source))
        negative=[]
        with io.OutputBoundary(complete,writer.reserve):
            receipt=module.save_causal_source(complete,value,writer,codec)
        assert(complete/'CAUSAL_SOURCE.json').read_bytes()==encoded
        assert c.read(complete/'CAUSAL_SOURCE.json')==value and receipt['bytes']==len(encoded)
        assert receipt['sha256']==c.sha(complete/'CAUSAL_SOURCE.json')
        cap=target/'cap';cap.mkdir()
        with io.OutputBoundary(cap,writer.reserve):
            try:module.save_causal_source(cap,{'software_cap_probe':'a'*(128*1024)},writer,codec)
            except AssertionError as error:
                assert 'FULL_CAUSAL_SOURCE_RECORD_CAP'in str(error);negative.append('full_source_cap_before_write')
            else:raise AssertionError('CAUSAL_RECORD_CAP_NOT_ENFORCED')
        assert not list(cap.iterdir())
        denied=target/'denied';denied.mkdir()
        def deny(*args,**kwargs):raise OSError('CAUSAL_RECORD_WRITER_DENIED')
        with io.OutputBoundary(denied,deny):
            try:module.save_causal_source(denied,value,writer,codec)
            except OSError as error:
                assert 'CAUSAL_RECORD_WRITER_DENIED'in str(error);first=repr(error);negative.append('writer_error_propagated')
            else:raise AssertionError('CAUSAL_RECORD_WRITER_ERROR_LOST')
        assert not(denied/'CAUSAL_SOURCE.json').exists()
        c.put(target/'FIRST_ERROR.json',dict(first_error=first,models=0,known_native=0,unknown=False))
        assert module.save_json.__code__.co_consts.count(16384)==1
        # Dedicated128KiB record remains inside original2MiB phase metadata
        # and32MiB writer. Neither original proof cap nor whole reserve grows.
        limits=c.limits();assert limits['phase_metadata_headroom']==2*1024**2 and limits['phase_writer_bytes']==32*1024**2
        assert 2*128*1024<limits['phase_metadata_headroom']
        before=ast.parse((old/'witness.py').read_text());after=ast.parse((C/'witness.py').read_text())
        after.body=[node for node in after.body if not(isinstance(node,ast.FunctionDef)and node.name=='save_causal_source')]
        class UndoRecord(ast.NodeTransformer):
            def visit_Call(self,node):
                self.generic_visit(node)
                if isinstance(node.func,ast.Name)and node.func.id=='save_causal_source':
                    node.func.id='save_json';node.args.insert(1,ast.Constant(value='CAUSAL_SOURCE.json'))
                return node
        assert ast.dump(before,include_attributes=False)==ast.dump(UndoRecord().visit(after),include_attributes=False)
        c.put(c.O/'FIXED_INPUTS.json',fixed)
        c.put(target/'QUALIFICATION.json',dict(passed=True,models=0,source_saved_bytes=42025,
            complete_source_all_fields_unchanged=True,original_periodic_snapshot_identity=True,
            no_math_or_model_calls=True,negative_cases=negative,first_error_saved=True,
            original_branch16KiB_and_phase32MiB_caps_unchanged=True,
            writer_charged_bytes=writer._read()['charged_bytes'],actual_response_compression_unexecuted=True))
        for path in C.iterdir():
            if path.is_file():
                if path.suffix=='.py':ast.parse(path.read_text())
                source[str(path.relative_to(c.R))]=c.sha(path)
        for path in [c.O/'FIXED_INPUTS.json',saved]:source[str(path.relative_to(c.R))]=c.sha(path)
        assert all(c.sha(c.R/name)==identity for name,identity in source.items())
        c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,
            source_only=True,models_authorized=False,complete_numeric_response_qualified=False),maximum=4*1024**2)
        result.update(passed=True,source_frozen=True,source_members=len(source),bootstrap=bootstrap,
            source_only=True,negative_cases=len(negative),source_saved_bytes=42025,
            writer_charged_bytes=writer._read()['charged_bytes'],old_definition_or_serializer_suite_rerun=False)
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder)
        result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
