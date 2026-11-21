"""Same finite response semantics with before-gate lossless stream persistence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import traceback

R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent


def exact(name,path,guard):
    guard.check()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[str(path.relative_to(R))]
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save_json(folder,name,value,writer,codec):
    raw=codec.encoded(value)
    assert len(raw)<=16384
    codec.write_atomic(folder/name,raw,writer)


def names(method):
    assert len(method['fixed_boundaries'])==281
    return [f'b{index:03d}_{kind}'for index in range(281)for kind in ('current','prospective')]+['nominal']


def binding(method,stage,codec):
    order=names(method)
    return dict(scientific_integration_revision=10,stage=stage,
        response_method_sha256=method['response_method_sha256'],
        base_method_input_sha256=method['base_method_semantic_sha256'],
        geometry_kind=method['geometry_kind'],causal_snapshot_sha256=method['causal_snapshot_sha256'],
        fixed_origin_native=method['base_method']['fixed_origin_native'],
        fixed_origin_sim_time=method['base_method']['fixed_origin_sim_time'],
        ordered_names_sha256=hashlib.sha256(codec.encoded(order)).hexdigest())


def run(method,setup,defs,origin,*,guard,stage,folder,writer,boundary,expected_folder=None):
    guard.check()
    assert stage in {'PYTHON_GENERATION','CPP_AUDIT'}
    assert (expected_folder is not None)==(stage=='CPP_AUDIT')
    old=R/'experiments/v1552_complete_canonical_witness'
    source=R/'experiments/v1550_canonical_observer_policy'
    schedules=exact('v1554_same_original_schedule',source/'schedule.py',guard)
    carriers=exact('v1554_same_continuous_response',source/'trajectory.py',guard)
    evidence=exact('v1554_same_array_construction',old/'evidence.py',guard)
    gates=exact('v1554_same_numeric_gates',old/'gates.py',guard)
    oldphase=exact('v1554_same_array_comparison',old/'witness.py',guard)
    codec=exact('v1554_original_codec',R/'experiments/v1507_priest_response_evidence/branch_store.py',guard)
    stream_module=exact('v1554_lossless_bound_stream',C/'stream.py',guard)
    result=dict(passed=False,closed=False,first_error=None,secondary_errors=[],
        response_method_sha256=method['response_method_sha256'],stage=stage,
        complete_nominal_native=0,complete_current_prospective_pairs=0,
        all_arrays_saved_before_gates=False,nominal_reference_complete=False,
        analytical_native=0,analytical_inflight_unknown=False,
        internal_Allocator_constructors=None,physical_native=0,replay_native=0,optimizer_calls=0,whole_navigation_passed=False)
    stream=None;active=None;nominal=None;active_name=None;saved=set()
    try:
        rows=schedules.raw_rows(guard.source)
        assert schedules.boundaries(rows)==tuple(tuple(value)for value in method['fixed_boundaries'])
        current_binding=binding(method,stage,codec)
        stream=stream_module.Stream(folder,writer=writer,boundary=boundary,binding=current_binding,ordered_names=names(method))
        expected=None
        if stage=='CPP_AUDIT':
            assert guard.audit_dependency
            expected=stream_module.Reader(expected_folder,expected_binding=binding(method,'PYTHON_GENERATION',codec),
                expected_result_sha256=hashlib.sha256((expected_folder/'GENERATION.json').read_bytes()).hexdigest(),
                ordered_names=names(method),check=guard.check)
        geom,forecast=gates.geometry(method,setup,guard)
        save_json(folder,'CAUSAL_SOURCE.json',forecast,writer,codec)
        gear=method['base_method']['physical_source']['gear_memory']
        if stage=='PYTHON_GENERATION':
            trajectory=carriers.PythonTrajectory(defs,setup,origin,gear,method,guard)
        else:
            parameters=json.loads((R/'experiments/v1159_bounded_steering_load/PARAMETERS.json').read_text())
            trajectory=carriers.CPPTrajectory.create(defs,setup,parameters['coefficients'],origin,gear,method,guard)
        nominal=evidence.Branch(trajectory)

        def persist(branch,name,n,current_only):
            arrays=branch.arrays()
            stream.save_data(name,arrays,accounting=guard.counts(),complete=len(branch.rows)==n)
            saved.add(name)
            assert len(branch.rows)==n,'NONZERO_INCOMPLETE_SAVED_BRANCH'
            proof=gates.evaluate(arrays,method,setup,geom,expected_native=n,zero_suffix=2200,raw_current_only=current_only)
            comparison=None if expected is None else oldphase.compare(arrays,expected.arrays(name))
            stream.save_proof(name,dict(safety=proof,comparison=comparison,arrays_already_saved=True,
                response_method_sha256=method['response_method_sha256']))
            assert proof['passed'],'NONZERO_COMPLETE_BRANCH_GATE_REFUSED:'+name
            assert comparison is None or comparison['passed'],'NONZERO_INDEPENDENT_CPP_DIFFERED:'+name

        for index,(offset,count)in enumerate(schedules.boundaries(rows)):
            assert trajectory.native==method['base_method']['fixed_origin_native']+offset
            for kind in ('current','prospective'):
                guard.set_bucket(stage,'witness')
                active_name=f'b{index:03d}_{kind}'
                child=trajectory.fork();active=evidence.Branch(child)
                if kind=='prospective':
                    for j in range(count):active.advance(child,schedules.at(rows,offset+j))
                for _ in range(2200):active.advance(child,(0.,0.,0))
                persist(active,active_name,2200+(count if kind=='prospective'else 0),kind=='current')
                active=None
            result['complete_current_prospective_pairs']+=1
            guard.set_bucket(stage,'nominal')
            for j in range(count):
                nominal.advance(trajectory,schedules.at(rows,offset+j))
                result['complete_nominal_native']+=1
        active=nominal;active_name='nominal'
        persist(nominal,'nominal',13600,False);active=None
        count=guard.account[stage]
        assert count['native']==1263600 and count['copy']==562
        assert count['nominal_native']==13600 and count['witness_native']==1250000
        assert not count['inflight_unknown']and count['construction_inflight']is None
        assert result['complete_current_prospective_pairs']==281 and result['complete_nominal_native']==13600
        result.update(passed=True,closed=True,analytical_native=count['native'],accounting=guard.counts(),
            all_arrays_saved_before_gates=True,nominal_reference_complete=True,construction_inflight=None)
        name='GENERATION.json'if stage=='PYTHON_GENERATION'else'AUDIT.json'
        save_json(folder,name,result,writer,codec)
        stream.seal(generation_result_sha256=hashlib.sha256((folder/name).read_bytes()).hexdigest())
    except BaseException as error:
        result.update(passed=False,first_error=repr(error),traceback=traceback.format_exc())
        # Preserve one latest rejected/incomplete branch and the continuous
        # nominal prefix in the SINGLE pre-reserved emergency slot.
        if stream is not None:
            try:
                if active is not None and active_name not in saved:
                    stream.emergency(active_name,active.arrays(),first_error=result['first_error'],accounting=guard.counts(),
                        nominal_prefix=nominal.arrays()if nominal is not None and nominal is not active else None)
                elif nominal is not None and 'nominal'not in saved:
                    stream.emergency('nominal_partial',nominal.arrays(),first_error=result['first_error'],accounting=guard.counts())
            except BaseException as secondary:
                result['secondary_errors'].append('emergency_save:'+repr(secondary))
            try:stream.abort(first_error=result['first_error'],accounting=guard.counts())
            except BaseException as secondary:result['secondary_errors'].append('stream_abort:'+repr(secondary))
    finally:
        count=guard.account[stage]
        result.update(closed=True,analytical_native=count['native'],analytical_inflight_unknown=count['inflight_unknown'],
            construction_inflight=count['construction_inflight'],accounting=guard.counts())
        # A success file was already stored before sealing. Never rewrite it
        # after seal; a failed seal must instead save the closed failure.
        if not result['passed']:
            try:save_json(folder,'GENERATION.json'if stage=='PYTHON_GENERATION'else'AUDIT.json',result,writer,codec)
            except BaseException as secondary:
                result['secondary_errors'].append('phase_result_save:'+repr(secondary))
                print('LOSSLESS_WITNESS_RESULT_SAVE_GAP:'+repr(result),flush=True)
    return result
