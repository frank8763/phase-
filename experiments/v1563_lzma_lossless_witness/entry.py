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
spec=importlib.util.spec_from_file_location('v1563_source_common',C/'common.py')
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
        module=c.load('v1562_real_xor_stream',C/'stream.py')
        xor=c.load('v1562_real_record_codec',C/'record_codec.py')
        codec=c.load('v1562_original_codec',c.R/'experiments/v1507_priest_response_evidence/branch_store.py')
        wm=c.load('v1562_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
        io_module=c.load('v1562_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
        old=c.R/'experiments/v1562_xor_lossless_witness'
        for name in ['driver.py','origin.py','witness.py','capability.py','owner.py','source_owner.py','LIMITS.json']:
            assert(C/name).read_bytes()==(old/name).read_bytes()
        prior=c.R/'runs/v1559_causal_source_record'
        review=c.read(prior/'CLOSED_BYTE_REVIEW.json')
        recovery=c.read(c.R/'runs/v1561_witness_cap_runtime_recovery/FULL_REMOTE_VERIFIED.json')
        assert review['passed']and recovery['passed']and recovery['every_member_SHA_and_link_text']
        saved=prior/'model/generation/WITNESSES.bin'
        assert c.sha(saved)==review['whole_stream_sha256']
        target=c.O/'source_target';target.mkdir()
        count=0;old_payload_bytes=new_payload_bytes=0;selected=None;selected_description=None
        import io,struct,hashlib
        # New representation exercised against every already saved real DATA
        # record; pure storage only, no safety/model/gear recomputation.
        with saved.open('rb')as stream:
            while True:
                header=stream.read(16)
                if not header:break
                assert len(header)==16
                magic,metadata_size,payload_size=struct.unpack('>8sII',header)
                assert magic==b'WE13BR01'and metadata_size<=16384 and payload_size<=8*1024**2
                meta=json.loads(stream.read(metadata_size));payload=stream.read(payload_size)
                assert hashlib.sha256(payload).hexdigest()==meta['payload_sha256']
                if meta['kind']!='DATA':continue
                with np.load(io.BytesIO(payload),allow_pickle=False)as stored:
                    arrays={k:stored[k].copy()for k in stored.files}
                payload2,description,n=xor.encode(arrays)
                restored=xor.decode(payload2,description)
                assert description==meta['arrays']and all(restored[k].tobytes()==v.tobytes()for k,v in arrays.items())
                count+=1;old_payload_bytes+=len(payload);new_payload_bytes+=len(payload2)
                selected=arrays;selected_description=description
        assert count==433
        extra=[]
        for name in ['LAST_REJECTED_BRANCH.npz','NOMINAL_PREFIX.npz']:
            path=prior/'model/generation'/name
            with np.load(path,allow_pickle=False)as stored:arrays={k:stored[k].copy()for k in stored.files}
            packed,description,n=xor.encode(arrays);extra.append(dict(path=str(path.relative_to(c.R)),sha256=c.sha(path),native=n,old_bytes=path.stat().st_size,new_bytes=len(packed)))
            assert all(xor.decode(packed,description)[k].tobytes()==v.tobytes()for k,v in arrays.items())
        negative=[]
        packed,desc,n=xor.encode(selected)
        try:xor.decode(packed[:-7],desc)
        except Exception:negative.append('truncated_LZMA')
        else:raise AssertionError('TRUNCATED_LZMA_ACCEPTED')
        try:xor.decode(packed+b'EXTRA',desc)
        except AssertionError:negative.append('extra_LZMA_tail')
        else:raise AssertionError('LZMA_TRAILING_BYTES_ACCEPTED')
        full=target/'saved_record';full.mkdir()
        writer=wm.WriterBudget(full,role='PLANNER',maximum_bytes=32*1024**2,source_identity=c.digest(source))
        method=c.read(c.R/'runs/v1550_canonical_observer_policy/source_target/RESPONSE_METHOD.json')
        names=module.MAX_BRANCHES
        phases=c.load('v1562_frozen_witness_names',C/'witness.py');order=phases.names(method);binding=phases.binding(method,'PYTHON_GENERATION',codec)
        with io_module.OutputBoundary(full,writer.reserve)as boundary:
            sink=module.Stream(full,writer=writer,boundary=boundary,binding=binding,ordered_names=order)
            sink.save_data(order[0],selected,accounting=dict(models=0,software_storage_of_existing_arrays=True),complete=True)
            sink.save_proof(order[0],dict(safety=dict(passed=True,software_storage_placeholder=True),comparison=None))
            sink.abort(first_error='SOURCE_ONLY_SINGLE_RECORD_NOT_FULL_WITNESS',accounting=dict(models=0))
        # Actual new Reader.arrays accessor must decode original values. The
        # full563 seal/verification is inherited by exact source recipe;
        # this deliberately partial source stream is never declared sealed.
        path=full/'WITNESSES.bin'
        with path.open('rb')as f:
            magic,m,n=struct.unpack('>8sII',f.read(16));meta=json.loads(f.read(m));offset=f.tell();payload=f.read(n)
        assert magic==module.MAGIC==b'WE13XL01'
        accessor=object.__new__(module.Reader);accessor.path=path
        accessor.offsets={order[0]:(offset,n,hashlib.sha256(payload).hexdigest(),meta['arrays'])}
        decoded=accessor.arrays(order[0]);assert all(decoded[k].tobytes()==v.tobytes()for k,v in selected.items())
        assert not(full/'STREAM_SEAL.json').exists()
        fixed=c.read(prior/'FIXED_INPUTS.json');c.put(c.O/'FIXED_INPUTS.json',fixed)
        original=(old/'stream.py').read_text();new=(C/'stream.py').read_text()
        # Unchanged stream gates/caps, producer methods and all consumers'
        # numerical inputs retain their exact original source/value contract.
        assert module.MAX_STREAM==22*1024**2 and module.MAX_PAYLOAD==8*1024**2 and module.MAX_METADATA==16384 and module.MAX_BRANCHES==563
        old_tree=ast.parse(original);new_tree=ast.parse(new)
        old_class=next(v for v in old_tree.body if isinstance(v,ast.ClassDef)and v.name=='Stream')
        new_class=next(v for v in new_tree.body if isinstance(v,ast.ClassDef)and v.name=='Stream')
        for node in ast.walk(new_class):
            if isinstance(node,ast.Constant)and node.value=='XOR_ROW_BYTEPLANES_LZMA_V1':node.value='XOR_ROW_BYTEPLANES_V1'
        assert ast.dump(old_class,include_attributes=False)==ast.dump(new_class,include_attributes=False)
        old_reader=next(v for v in old_tree.body if isinstance(v,ast.ClassDef)and v.name=='Reader')
        new_reader=next(v for v in new_tree.body if isinstance(v,ast.ClassDef)and v.name=='Reader')
        assert ast.dump(old_reader,include_attributes=False)==ast.dump(new_reader,include_attributes=False)
        assert c.read(c.R/'runs/v1562_xor_lossless_witness/ENTRY_QUALIFICATION.json')['passed']
        c.put(target/'QUALIFICATION.json',dict(passed=True,models=0,old_saved_DATA_records=count,original_payload_bytes=old_payload_bytes,new_payload_bytes=new_payload_bytes,old_stream_metadata_headers_bytes=review['metadata_and_headers_bytes'],new_prefix_payload_plus_same_overhead_bytes=new_payload_bytes+review['metadata_and_headers_bytes'],full_response_compression_fit_guaranteed=False,all13arraydtype_shape_valuebytes_equal=True,old_XOR_extremebitpatterns_proof_reused_not_rerun=True,source_only_saved_arrays_not_new_model_or_safety_audit=True,additional_saved_inputs=extra,negative_cases=negative,production_Stream_first_DATA_PROOF_abort_saved=True,newReader_arrays_accessor_bitwise=True,fullReader_verify_not_executed=True,no_full_seal=True,old_Stream_ASTunchanged_except_representation_label=True,old_Reader_ASTunchanged=True,writer_charged_bytes=writer._read()['charged_bytes']))
        for path in C.iterdir():
            if path.is_file():
                if path.suffix=='.py':ast.parse(path.read_text())
                source[str(path.relative_to(c.R))]=c.sha(path)
        for path in [c.O/'FIXED_INPUTS.json',saved,prior/'model/generation/LAST_REJECTED_BRANCH.npz',prior/'model/generation/NOMINAL_PREFIX.npz',prior/'CLOSED_BYTE_REVIEW.json',c.R/'runs/v1562_xor_lossless_witness/ENTRY_QUALIFICATION.json',c.R/'runs/v1562_xor_lossless_witness/source_target/QUALIFICATION.json']:
            source[str(path.relative_to(c.R))]=c.sha(path)
        assert all(c.sha(c.R/name)==identity for name,identity in source.items())
        c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),entry_passed=True,source_only=True,models_authorized=False,complete_numeric_response_qualified=False),maximum=4*1024**2)
        result.update(passed=True,source_frozen=True,source_members=len(source),bootstrap=bootstrap,source_only=True,negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],old_saved_DATA_records=count,old_saved_payload_bytes=old_payload_bytes,new_payload_bytes=new_payload_bytes,old_definition_or_serializer_suite_rerun=False)
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None);sys.meta_path.remove(finder)
        result.update(closed=True,wall_s=time.monotonic()-start)
        c.put(c.O/'ENTRY_QUALIFICATION.json',result)
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
