"""Registered response identity around immutable M8 input, not a state reset."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
BASE = 'runs/v1532_observer_epoch_origin/source_target/METHOD_INPUT.json'
BASE_FILE_SHA = '94567c40ba3fd924f00a8e6c3b15b4012cec5559d00756354e75c2f4066ab658'
BASE_SEMANTIC_SHA = 'be88e178a7d661d6d075d63193983d8086a63ee5311865fbac64cf9011d3e1d1'
REGISTRATION = 'runs/v1550_canonical_observer_policy/SCIENTIFIC_REVISION_REGISTRATION.json'
MODEL = 'experiments/v1159_bounded_steering_load/model.py'
ENGINE = 'experiments/v1159_bounded_steering_load/engine.py'
GEAR = 'experiments/v1396_rpp_rpc_retirement/gear_handoff.py'
FEEDBACK = 'experiments/v1409_scalar_steering_feedback/feedback.py'


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MethodRefusal(AssertionError):
    def __init__(self,first,proof,secondary=None):
        super().__init__(first)
        self.proof=proof
        self.secondary=secondary


def prepare(*,prepared_sources,registration_sha256,save_proof):
    proof=dict(passed=False,models=0,analytical_native=0,physical_native=0,
               freshwire=False,model_permission=False,search_permission=False,
               geometry_qualified=False,complete_response_qualified=False)
    first=None
    answer=None
    try:
        source={}
        for name in [BASE,MODEL,ENGINE,GEAR,FEEDBACK]:
            path=R/name
            assert path.resolve()==path and path.is_file() and not path.is_symlink()
            source[name]=sha(path)
            assert source[name]==prepared_sources[name], 'NONZERO_METHOD_SOURCE_CHANGED:'+name
        assert source[BASE]==BASE_FILE_SHA
        regpath=R/REGISTRATION
        assert sha(regpath)==registration_sha256, 'NONZERO_METHOD_REGISTRATION_CHANGED'
        reg=json.loads(regpath.read_text())
        assert reg['scientific_integration_revision']==10 and reg['previous_revision']==9
        assert reg['registered_before_method_implementation'] and reg['no_model_or_physical_admission']
        assert reg['immutable_base_method_file_sha256']==BASE_FILE_SHA
        assert reg['base_method_input_semantic_sha256']==BASE_SEMANTIC_SHA
        assert reg['catalogue']==dict(index=0,stage_native=0,source_cut=11400,raw_nominal_native=13600,complete_original_boundaries=281,final_zero_tail=2200)
        base=json.loads((R/BASE).read_text())
        clean=copy.deepcopy(base)
        identity=clean.pop('method_input_sha256')
        assert digest(clean)==identity==BASE_SEMANTIC_SHA
        assert base['scientific_integration_revision']==8 and base['not_fresh_wire']
        assert base['physical_permission'] is False
        assert base['method_memory']['steering_load_episode'] is False
        assert base['method_memory']['actual_sensor_claim'] is False
        assert base['method_memory']['epoch_policy']=='ORIGINAL_OBSERVER_ENTRY_LOAD_FALSE_ONLY_AT_DECLARED_EVENT'
        packet=base['physical_source']['packet']
        gear=base['physical_source']['gear_memory']
        assert gear==dict(gear=1,brake_start=None,last_tick=base['fixed_origin_native']-1)
        assert packet['coupled_episode'] is False and packet['steering_motion_active'] is False and packet['parked_target'] is None
        spec=importlib.util.spec_from_file_location('v1550_registered_request_definition',C/'schedule.py')
        schedule=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schedule)
        rows=schedule.raw_rows(prepared_sources)
        plan=schedule.metadata(prepared_sources)
        assert plan['total_native_per_phase']==1263600 and plan['witness_native']==1250000
        answer=dict(base_method=base,base_method_file_sha256=BASE_FILE_SHA,
                    base_method_semantic_sha256=BASE_SEMANTIC_SHA,scientific_integration_revision=10,
                    registration=dict(path=REGISTRATION,sha256=registration_sha256),
                    model_variant=base['model_variant'],geometry_kind='FULL_PERIOD_DISK',
                    causal_snapshot_sha256=base['causal_snapshot_sha256'],
                    raw_schedule=rows,raw_schedule_sha256=digest(rows),
                    fixed_boundaries=schedule.boundaries(rows),
                    fixed_source_clock=True,extra_gear_hold_ticks=0,
                    canonical_gear_per_native=True,encoder_policy='MEASURED_ORIGIN_THEN_CURRENT_SCALAR_V1409_BRANCH_OWNED',
                    current_and_prospective_stop_native=2200,minimum200_preserved=True,
                    raw_requests_are_not_applied_controls=True,original_selector_reproduced=False,
                    source_SHA=source,plan=plan,not_fresh_wire=True,
                    model_permission=False,physical_permission=False,replay_permission=False)
        answer['response_method_sha256']=digest(answer)
        proof.update(passed=True,response_method_sha256=answer['response_method_sha256'],
                     base_input_unchanged=True,base_method_semantic_sha256=BASE_SEMANTIC_SHA,
                     registration_sha256=registration_sha256,source_SHA=source,plan=plan,
                     explicit_interface_revision=True,gear_holds_consume_fixed_ticks=True,
                     old_cached_feedback_or_qgeometry_equivalence=False)
    except BaseException as error:
        first=repr(error)
        proof['first_error']=first
    secondary=None
    try:
        save_proof(proof)
    except BaseException as error:
        secondary=repr(error)
        proof['passed']=False
    if first or secondary:
        raise MethodRefusal(first or 'NONZERO_METHOD_PROOF_SAVE_FAILED',proof,secondary)
    return answer
