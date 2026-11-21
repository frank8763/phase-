"""Finite current/prospective response ownership and success-only comparison.

Draft production assembly. No CLI/admission/once owner is provided here. No
model construction on import; every exposed numerical seam requires Guard.
"""
import hashlib
import importlib.util
from pathlib import Path
import traceback

R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent


def exact(name,path,guard):
    guard.check()
    relative=str(path.relative_to(R))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==guard.source[relative]
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save_json(folder,name,value,writer,codec):
    assert Path(name).name==name
    codec.write_atomic(folder/name,codec.encoded(value),writer)


def read_expected(folder,name,method):
    import json
    import numpy as np
    receipt=json.loads((folder/(name+'.json')).read_text())
    assert receipt['complete'] is True and receipt['first_error'] is None
    assert receipt['response_method_sha256']==method['response_method_sha256']
    row=receipt['arrays']
    assert Path(row['path']).name==row['path']
    path=folder/row['path']
    assert path.stat().st_size==row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    with np.load(path,allow_pickle=False) as stored:
        return {key:stored[key].copy()for key in stored.files}


def compare(arrays,expected):
    import numpy as np
    assert set(arrays)==set(expected)
    differences={}
    for key,value in arrays.items():
        assert value.shape==expected[key].shape and value.dtype==expected[key].dtype
        differences[key]=float(np.max(abs(value-expected[key]))) if value.size else 0.
    return dict(passed=all(value<=1e-8 for value in differences.values()),maximum_errors=differences,
                independent_state_memory_mode_gear_continuous=True,
                no_generated_state_or_control_as_per_step_input=True)


def run(method,setup,defs,origin,*,guard,stage,folder,writer,expected_folder=None):
    """One phase; caller must arm CPP audit only after saved full success."""
    guard.check()
    assert stage in {'PYTHON_GENERATION','CPP_AUDIT'}
    if stage=='CPP_AUDIT':
        assert guard.audit_dependency is True and expected_folder is not None
    else:
        assert expected_folder is None
    source=R/'experiments/v1550_canonical_observer_policy'
    schedules=exact('v1552_frozen_original_rows',source/'schedule.py',guard)
    carriers=exact('v1552_frozen_continuous_carriers',source/'trajectory.py',guard)
    evidence=exact('v1552_current_evidence',C/'evidence.py',guard)
    gates=exact('v1552_current_saved_array_gates',C/'gates.py',guard)
    codec=exact('v1552_original_bounded_codec',R/'experiments/v1507_priest_response_evidence/branch_store.py',guard)
    result=dict(passed=False,closed=False,first_error=None,secondary_errors=[],
                response_method_sha256=method['response_method_sha256'],stage=stage,
                complete_nominal_native=0,complete_current_prospective_pairs=0,
                analytical_native=0,analytical_inflight_unknown=False,
                all_arrays_saved_before_gates=False,nominal_reference_complete=False,
                internal_Allocator_constructors=None,physical_native=0,replay_native=0,
                optimizer_calls=0,whole_navigation_passed=False)
    nominal=None
    active=None
    active_name=None
    active_expected=None
    saved_names=set()
    try:
        rows=schedules.raw_rows(guard.source)
        assert schedules.boundaries(rows)==tuple(tuple(value)for value in method['fixed_boundaries'])
        geom,forecast=gates.geometry(method,setup,guard)
        save_json(folder,'CAUSAL_SOURCE.json',forecast,writer,codec)
        gear=method['base_method']['physical_source']['gear_memory']
        if stage=='PYTHON_GENERATION':
            trajectory=carriers.PythonTrajectory(defs,setup,origin,gear,method,guard)
        else:
            import json
            parameters=json.loads((R/'experiments/v1159_bounded_steering_load/PARAMETERS.json').read_text())
            trajectory=carriers.CPPTrajectory.create(defs,setup,parameters['coefficients'],origin,gear,method,guard)
        nominal=evidence.Branch(trajectory)

        def persist(branch,name,n,*,current_only,first_error=None):
            arrays,receipt=evidence.save_before_gate(branch,folder=folder,name=name,writer=writer,
                 method=method,expected_native=n,accounting=guard.counts(),first_error=first_error)
            saved_names.add(name)
            assert receipt['complete'], 'NONZERO_INCOMPLETE_SAVED_BRANCH'
            proof=gates.evaluate(arrays,method,setup,geom,expected_native=n,zero_suffix=2200,raw_current_only=current_only)
            comparison=None
            if expected_folder is not None:
                comparison=compare(arrays,read_expected(expected_folder,name,method))
            save_json(folder,name+'_PROOF.json',dict(safety=proof,comparison=comparison,
                        arrays_already_saved=True,response_method_sha256=method['response_method_sha256']),writer,codec)
            assert proof['passed'], 'NONZERO_COMPLETE_BRANCH_GATE_REFUSED:'+name
            assert comparison is None or comparison['passed'], 'NONZERO_INDEPENDENT_CPP_DIFFERED:'+name
            return arrays

        for boundary,(offset,count) in enumerate(schedules.boundaries(rows)):
            assert trajectory.native==method['base_method']['fixed_origin_native']+offset
            for kind in ('current','prospective'):
                active_name=f'b{boundary:03d}_{kind}'
                active_expected=2200+(count if kind=='prospective'else 0)
                child=trajectory.fork()
                active=evidence.Branch(child)
                if kind=='prospective':
                    for index in range(count):
                        active.advance(child,schedules.at(rows,offset+index))
                for _ in range(2200):
                    active.advance(child,(0.,0.,0))
                persist(active,active_name,active_expected,current_only=kind=='current')
                active=None
            result['complete_current_prospective_pairs']+=1
            for index in range(count):
                nominal.advance(trajectory,schedules.at(rows,offset+index))
                result['complete_nominal_native']+=1
        active_name='nominal'
        active=nominal
        active_expected=13600
        persist(nominal,'nominal',13600,current_only=False)
        active=None
        count=guard.account[stage]
        assert count['native']==1263600 and count['copy']==562
        assert count['inflight_unknown'] is False and count['construction_inflight'] is None
        assert result['complete_current_prospective_pairs']==281
        assert result['complete_nominal_native']==13600
        result.update(passed=True,all_arrays_saved_before_gates=True,nominal_reference_complete=True)
    except BaseException as error:
        result.update(passed=False,first_error=repr(error),traceback=traceback.format_exc())
        # Do not regenerate, rerun, invent an acknowledged row or erase an
        # original complete rejection. Model count and saved-prefix count are
        # separate if a post-step snapshot/write failed.
        if active is not None and active_name not in saved_names:
            try:
                evidence.save_before_gate(active,folder=folder,name=active_name+'_partial',writer=writer,
                     method=method,expected_native=active_expected,accounting=guard.counts(),first_error=result['first_error'])
            except BaseException as secondary:
                result['secondary_errors'].append('active_partial_save:'+repr(secondary))
        if nominal is not None and 'nominal' not in saved_names and nominal is not active:
            try:
                evidence.save_before_gate(nominal,folder=folder,name='nominal_partial',writer=writer,
                     method=method,expected_native=13600,accounting=guard.counts(),first_error=result['first_error'])
            except BaseException as secondary:
                result['secondary_errors'].append('nominal_partial_save:'+repr(secondary))
    finally:
        count=guard.account[stage]
        result.update(closed=True,analytical_native=count['native'],analytical_inflight_unknown=count['inflight_unknown'],
                      construction_inflight=count['construction_inflight'],accounting=guard.counts())
        try:
            save_json(folder,'GENERATION.json'if stage=='PYTHON_GENERATION'else'AUDIT.json',result,writer,codec)
        except BaseException as secondary:
            result['passed']=False
            result['secondary_errors'].append('phase_result_save:'+repr(secondary))
            print('NONZERO_WITNESS_PHASE_RESULT_SAVE_GAP:'+repr(result),flush=True)
    return result
