"""Disclosed method-state epoch over immutable saved data; no model calls.

Revision8 must precede this implementation. The physical packet and all its
recorded modes remain unchanged; load=False belongs only to the declared new
method epoch. It is neither a measured flag nor a reconstructed RPCCR prefix.
"""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path

R=Path(__file__).resolve().parents[2]
C=Path(__file__).resolve().parent
REG=R/'runs/v1532_observer_epoch_origin/SCIENTIFIC_REVISION_REGISTRATION.json'
ORIGINAL='experiments/v1281_partial_reconnection_fixed24/live_entry.py'
METHOD='ORIGINAL_BOUNDED_LOAD_PREDICTOR_WITH_DISCLOSED_OBSERVER_ENTRY_EPOCH_AT_CURRENT_REST'


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OriginSourceRefusal(AssertionError):
    def __init__(self,message,proof,secondary_save_error=None):
        super().__init__(message)
        self.proof=proof
        self.secondary_save_error=secondary_save_error


def prepare_saved_source(*,source_envelope,content_proof,remote_index,remote_proof,
                         prepared_sources,save_proof):
    """Future new source target may call this; no numerical authority is given.

    All four saved files and registration/source must be immutable manifest
    inputs. Existing V1528proof is reused by its actual V1529remote member SHA,
    without rerunning the old journal/projection or source qualification.
    """
    proof=dict(passed=False,kind='V1532_OBSERVER_EPOCH_SOURCE_PROOF',checks={},
               method_input=None,method_epoch_qualified=False,
               model_origin_conversion_qualified=False,models_authorized=False,
               physical_permission=False,actual_capture_qualified=False,
               original_RPP_prefix_not_RPCCR_navigation=True,stage='immutable_sources')
    first=None
    try:
        paths={}
        for key,name in [('source_envelope',source_envelope),('content_proof',content_proof),
                         ('remote_index',remote_index),('remote_proof',remote_proof),
                         ('registration',str(REG.relative_to(R))),('original_method_source',ORIGINAL)]:
            assert isinstance(name,str)and not Path(name).is_absolute()and '..'not in Path(name).parts
            path=R/name
            assert path.resolve().is_relative_to(R)and path.is_file()and not any(p.is_symlink()for p in [path,*path.parents])
            assert path.stat().st_size<=8*1024**2
            assert prepared_sources[name]==sha(path),('OBSERVER_EPOCH_SOURCE_NOT_PINNED',key)
            paths[key]=path
        read=lambda key:json.loads(paths[key].read_text())
        registration=read('registration')
        assert registration['scientific_integration_revision']==8
        assert registration['registered_before_method_implementation']is True
        assert registration['method']==METHOD
        assert registration['epoch_policy']=='ORIGINAL_OBSERVER_ENTRY_LOAD_FALSE_ONLY_AT_DECLARED_EVENT'
        assert registration['original_source_sha256']==sha(paths['original_method_source'])
        assert registration['actual_sensor_claim']is False and not registration['new_numerical_or_physical_admission']
        proof['checks']['revision8_preregistered']=True
        proof['stage']='original_method_assignment'
        tree=ast.parse(paths['original_method_source'].read_text())
        execute=next(node for node in tree.body if isinstance(node,ast.FunctionDef)and node.name=='execute')
        assignments=[node for node in execute.body if isinstance(node,ast.Assign)
                     and any(isinstance(target,ast.Attribute)and isinstance(target.value,ast.Name)
                             and target.value.id=='v'and target.attr=='_live_load'for target in node.targets)]
        assert len(assignments)==1 and isinstance(assignments[0].value,ast.Constant)and assignments[0].value.value is False
        proof['checks']['original_observer_entry_assignment_exact']=True
        proof['original_assignment']=dict(source=ORIGINAL,source_sha256=sha(paths['original_method_source']),
                                          function='execute',line=assignments[0].lineno,assigned_value=False,
                                          original_worker_executed=False)
        proof['stage']='remote_saved_source_proof'
        remote=read('remote_proof')
        assert all(remote[k]is True for k in ['passed','every_asset_actual_download_SHA',
                                             'every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])
        members={row['path']:row for row in read('remote_index')['files']}
        for key in ['source_envelope','content_proof']:
            name=str(paths[key].relative_to(R));row=members[name]
            assert row['sha256']==prepared_sources[name]and row['bytes']==paths[key].stat().st_size
        physical=read('source_envelope');bound=read('content_proof')
        clean=copy.deepcopy(physical);identity=clean.pop('input_sha256')
        assert digest(clean)==identity
        assert physical['source_role']=='SAVED_ACTUAL_MODEL_ONLY'
        assert physical['physical_permission']is False and physical['models_authorized']is False
        assert bound['source_and_saved_content_passed']is True
        assert bound['original_envelope']==physical
        assert bound['saved_content']['passed']is True
        assert bound['saved_content']['source_receipts_actual_content_verified']is True
        assert bound['saved_content']['coordinate_projection']['passed']is True
        proof['checks']['original_saved_source_proof_exact']=True
        proof['stage']='restricted_current_rest_and_mode'
        packet=physical['packet']
        assert (physical['case_id'],physical['seed'],physical['phase'])==('WEST_EAST',10060001,1.5107128341898335)
        assert packet['coupled_episode']is False and packet['steering_motion_active']is False and packet['parked_target']is None
        values=[*packet['body'],*packet['steering']['position'],*packet['steering']['velocity'],
                *packet['controller_memory']['last_ctrl'],packet['controller_memory']['integral']]
        assert all(type(v)in(int,float)and math.isfinite(v)for v in values)
        assert max(abs(v)for v in packet['body'][3:])<=.003
        assert max(abs(v)for v in packet['steering']['velocity'])<=.015
        assert max(abs(v)for v in packet['controller_memory']['last_ctrl'][2:])<=1e-10
        assert type(packet['native_tick'])is int and packet['native_tick']>=0
        assert abs(packet['sim_time']-.01*packet['native_tick'])<=1e-8
        assert physical['causal_snapshot']['periodic']is not None and physical['causal_snapshot']['online_actor_truth']is False
        assert digest(physical['causal_snapshot'])==physical['causal_snapshot_sha256']
        proof['checks']['current_physical_modes_unchanged_at_rest']=True
        model_sources={}
        for name in ['experiments/v1159_bounded_steering_load/model.py',
                     'experiments/v1159_bounded_steering_load/engine.py',
                     'experiments/v1159_bounded_steering_load/PARAMETERS.json',
                     'runs/v1159_bounded_steering_load/profile.so',
                     'experiments/v1118_coupled_live_qualification/runtime.py']:
            assert prepared_sources[name]==sha(R/name)
            model_sources[name]=prepared_sources[name]
        method_input=dict(kind='SAVED_CURRENT_ORIGIN_STOP_ONLY_METHOD_INPUT',schema=1,
                          scientific_integration_revision=8,method=METHOD,
                          model_variant='V1159_BOUNDED_STEERING_LOAD_OVER_V1114',
                          exact_original_model_sources=model_sources,
                          physical_source=copy.deepcopy(physical),physical_source_input_sha256=identity,
                          physical_source_model_label_is_historical_descriptor_only=True,
                          no_model_equivalence_to_physical_source_label_claimed=True,
                          method_memory=dict(kind='DECLARED_OBSERVER_ENTRY_METHOD_STATE',
                                             steering_load_episode=False,epoch_native=packet['native_tick'],
                                             epoch_sim_time=packet['sim_time'],
                                             epoch_policy=registration['epoch_policy'],actual_sensor_claim=False,
                                             original_source_sha256=sha(paths['original_method_source'])),
                          fixed_origin_native=packet['native_tick'],fixed_origin_sim_time=packet['sim_time'],
                          causal_snapshot_sha256=physical['causal_snapshot_sha256'],
                          source_content_proof_sha256=sha(paths['content_proof']),
                          registration_sha256=sha(paths['registration']),
                          physical_permission=False,models_authorized=False,
                          model_origin_conversion_qualified=False,not_fresh_wire=True,
                          original_RPP_prefix_not_RPCCR_navigation=True,optimizer_proposal_reused=False)
        method_input['method_input_sha256']=digest(method_input)
        proof.update(passed=True,stage='source_description_only',method_input=method_input,
                     inherited_physical_source_file_sha256=sha(paths['source_envelope']),
                     method_memory_separate_from_original_packet=True,
                     no_numerical_origin_or_model_created=True)
    except Exception as error:
        first='OBSERVER_EPOCH_SOURCE_REFUSED:'+repr(error)
        proof.update(first_error=first,failed_stage=proof['stage'])
    secondary=None
    try:save_proof(proof)
    except BaseException as error:secondary=repr(error)
    if first is not None or secondary is not None:
        raise OriginSourceRefusal(first or 'OBSERVER_EPOCH_SOURCE_PROOF_SAVE_FAILED',proof,secondary)
    return proof['method_input']


def numeric_origin(*args,**kwargs):
    raise AssertionError('V1532_NUMERICAL_ORIGIN_CONVERSION_AND_ONCE_OWNER_NOT_IMPLEMENTED_OR_ADMITTED')
