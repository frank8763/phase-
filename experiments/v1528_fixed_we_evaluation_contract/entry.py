"""Once new saved-content interface target. Zero model/dynamics/optimizer calls."""
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    assert sorted(os.sched_getaffinity(0)) == [4] and os.environ.get('PHASE_REPO') == str(R)
    start = time.monotonic()
    assert time.time() + 120 < 1795395600
    os.environ['MUJOCO_GL'] = 'osmesa'
    with (O / 'ENTRY_ONCE_CLAIM.json').open('x') as stream:
        json.dump(dict(unix=time.time(),models=0,scope='SAVED_CONTENT_INTERFACE_ONLY'), stream)

    class NoModels(importlib.abc.MetaPathFinder):
        def find_spec(self, name, *args):
            if name.split('.')[0] in {'jax', 'jaxlib', 'mujoco', 'torch', 'rclpy', 'vehicle', 'factory'}:
                raise AssertionError('SAVED_CONTENT_TARGET_NO_MODELS:' + name)

    finder = NoModels()
    sys.meta_path.insert(0, finder)

    def profile(frame, event, arg):
        if event == 'call' and frame.f_code.co_name in {'__init__', 'step', 'compute', 'predict'}:
            if Path(frame.f_code.co_filename).name in {'prediction.py', 'coupled_model.py', 'model.py', 'coupled_control.py', 'vehicle_control.py', 'kernel.py', 'engine.py'}:
                raise AssertionError('SAVED_CONTENT_TARGET_NO_MODEL_OR_ALLOCATOR_CALL')
        if time.monotonic() - start >= 120:
            raise AssertionError('SAVED_CONTENT_TARGET_MONOTONIC_LIMIT')

    sys.setprofile(profile)
    common = load('v1528_original_guard_only', R / 'experiments/v1504_priest_namespace_worker/common.py')
    common.guard(O)
    result = dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,
                  Allocator_recomputations=0,replay_native=0,optimizer_calls=0,
                  scope='NEW_SAVED_CONTENT_AND_COORDINATE_INTERFACE_ONLY',actual_capture_qualified=False,
                  method_epoch_qualified=False,model_or_physical_admission=False)
    try:
        with (R / 'runs/v648_static_unknown/execution.lock').open() as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            parent = common.read(R / 'runs/v1382_weekend_campaign/LEDGER.json')
            assert parent['active_round'] is None and parent.get('active_math_round') is None and not parent['models_now_authorized']
            prior = common.read(R / 'runs/v1518_compact_parent_control/SOURCE_FREEZE.json')
            assert common.sha(R / prior['base_manifest']) == prior['base_manifest_sha256']
            sources = common.read(R / prior['base_manifest'])['files'].copy()
            sources.update(prior['files'])
            assert len(sources) == 11496
            assert all(common.sha(R / name) == identity for name, identity in sources.items())
            additions = common.read(O / 'ENTRY_FIXED_SOURCE_ADDITIONS.json')
            assert all(common.sha(R/name) == identity for name, identity in additions['files'].items())
            source_index = common.read(R/additions['qualification_member_remote_index'])
            source_remote = common.read(R/additions['qualification_member_remote_proof'])
            assert source_remote['passed'] is True
            assert additions['index_row'] in source_index['files']
            assert additions['files'][additions['index_row']['path']] == additions['index_row']['sha256']
            sources.update(additions['files'])
            sources[str((O/'ENTRY_FIXED_SOURCE_ADDITIONS.json').relative_to(R))] = common.sha(O/'ENTRY_FIXED_SOURCE_ADDITIONS.json')
            for name, identity in common.read(O / 'CLOSED_METADATA_SOURCE_INDEX.json').items():
                assert common.sha(R / name) == identity
            for path in C.iterdir():
                if path.is_file():
                    sources[str(path.relative_to(R))] = common.sha(path)
            original_root = 'runs/v1479_retirement_scope_binding/'
            files = dict(event_input=original_root+'first_event/bridge_events/event0000/CURRENT_INPUT.json',
                         setup=original_root+'first_event/bridge_events/event0000/SETUP.json',
                         states=original_root+'first_event/FULL_STATE_NPLUS1.npz',
                         journal=original_root+'first_event/ACTUAL_OWNER_JOURNAL.jsonl',
                         remote_index=original_root+'actual_runtime_delivery/ARCHIVE_INDEX.json',
                         remote_proof=original_root+'actual_runtime_delivery/FULL_REMOTE_VERIFIED.json',
                         binding_proof='runs/v1497_priest_complete_response/ENTRY_QUALIFICATION.json',
                         public_map='experiments/v855_renewal_worker/KNOWN_FIELD.json')
            assert all(name in sources for name in files.values())
            import numpy as np
            original = common.read(R / files['event_input'])
            n = original['origin']['native_tick']
            with np.load(R / files['states'], allow_pickle=False) as arrays:
                fullstate = {k:(float(arrays[k][n]) if k == 'time' else arrays[k][n].tolist())
                             for k in ['time','qpos','qvel','ctrl','mocap_pos','mocap_quat']}
            contract = load('v1528_new_input_contract', C / 'input_contract.py')
            graph_sha = common.sha(O / 'SOURCE_GRAPH.json')
            raw = dict(schema=1,case_id='WEST_EAST',seed=10060001,phase=1.5107128341898335,
                       run_id='V1528_RECORDED_SOURCE_INTERFACE_ONLY',source_role='SAVED_ACTUAL_MODEL_ONLY',
                       source_graph_sha256=graph_sha,model_variant='V1114_COUPLED_SCALAR_FEEDBACK',
                       packet=copy.deepcopy(original['origin']),fullstate=fullstate,
                       fullstate_sha256=common.digest(fullstate),
                       mode_history=copy.deepcopy(original['mode_history']),gear_memory=copy.deepcopy(original['gear_memory']),
                       causal_snapshot=copy.deepcopy(original['causal_snapshot']),causal_snapshot_sha256=original['causal_snapshot_sha256'],
                       method_memory=dict(kind='EXPLICIT_METHOD_STATE_SEPARATE_FROM_PHYSICAL_PACKET',actual_sensor_claim=False,
                                          steering_load_episode=None,epoch_native=None,epoch_policy_id='NOT_APPLICABLE_TO_PLAIN_V1114'),
                       provenance=dict(canonical_origin_native=0,applied_actions=n,state_rows=n+1,contact_rows=n+1,
                                       root_guard_native=n,unrecorded_actual_gap=0,not_fresh_wire=True,
                                       state_packet_binding_proof_sha256=sources[files['binding_proof']],
                                       applied_journal_sha256=sources[files['journal']],
                                       causal_source_receipt_sha256=sources[files['event_input']],
                                       model_setup_sha256=sources[files['setup']],public_map_sha256=sources[files['public_map']]),
                       physical_permission=False,models_authorized=False)

            def identify(value):
                value.pop('input_sha256',None)
                value['input_sha256'] = contract.digest(value)
                return value

            identify(raw)
            task = O / 'source_content_target'
            task.mkdir()
            budget_module = load('v1528_original_writer', R / 'experiments/v1436_pathlib_control_rename/writer_budget.py')
            boundary_module = load('v1528_original_boundary', R / 'experiments/v1436_pathlib_control_rename/bounded_io.py')
            codec = load('v1528_original_qualified_codec', R / 'experiments/v1507_priest_response_evidence/branch_store.py')
            writer = budget_module.WriterBudget(task,role='PLANNER',maximum_bytes=2*1024**2,source_identity=common.digest(sources))
            cases = []
            with boundary_module.OutputBoundary(task, writer.reserve):
                def run(label, value, expected, prepared=sources):
                    saved = []
                    path = task / (label+'.json')
                    def save(proof):
                        codec.write_atomic(path, codec.encoded(proof), writer)
                        saved.append(proof)
                    first = None
                    try:
                        answer = contract.validate_saved(value,source_graph_sha256=graph_sha,files=files,
                                                         prepared_sources=prepared,save_proof=save)
                    except contract.SourceRefusal as error:
                        first = str(error)
                        assert error.save_error is None
                        answer = error.proof
                    assert len(saved) == 1 and common.read(path) == saved[0] == answer
                    assert answer['source_and_saved_content_passed'] is expected
                    assert (first is None) is expected
                    assert not answer['models_authorized'] and not answer['physical_permission'] and not answer['actual_capture_qualified']
                    cases.append(dict(name=label,passed=expected,first_error=first,proof_sha256=common.sha(path),
                                      diagnostic_saved_before_refusal=True,content_failed_stage=(answer['saved_content'] or {}).get('failed_stage')))
                    return answer
                positive = run('saved_original_content_only',raw,True)
                assert positive['saved_content']['source_receipts_actual_content_verified']
                assert positive['saved_content']['coordinate_projection']['passed']
                codec.write_atomic(task/'SOURCE_ENVELOPE.json',codec.encoded(raw),writer)
                # Mutations are negative software inputs. They neither replace
                # immutable actual data nor generate a response-model sample.
                changed=copy.deepcopy(raw);changed['packet']['body'][0]+=.000001
                run('changed_body',identify(changed),False)
                changed=copy.deepcopy(raw);changed['packet']['steering']['native_tick']+=1
                run('wrong_measurement_native',identify(changed),False)
                changed=copy.deepcopy(raw);changed['packet']['steering']['measured_at']+=.001
                run('wrong_measurement_timestamp',identify(changed),False)
                changed=copy.deepcopy(raw);changed['fullstate']['qpos'][0]+=.000001;changed['fullstate_sha256']=common.digest(changed['fullstate'])
                run('changed_fullstate',identify(changed),False)
                changed=copy.deepcopy(raw);changed['provenance']['applied_journal_sha256']='0'*64
                run('wrong_journal_descriptor',identify(changed),False)
                changed=copy.deepcopy(raw);changed['source_role']='FRESH_ACTUAL_CURRENT'
                run('fresh_capture_unqualified',identify(changed),False)
                changed=copy.deepcopy(raw);changed['model_variant']='V1159_BOUNDED_STEERING_LOAD_OVER_V1114'
                run('unknown_V1159_load_epoch',identify(changed),False)
                changed=copy.deepcopy(raw);del changed['packet']['steering']['measured_at']
                run('missing_provenance',identify(changed),False)
                changed_sources=dict(sources);changed_sources[str((C/'content_binding.py').relative_to(R))]='0'*64
                run('changed_content_reader_source',raw,False,changed_sources)
                # The source checker must preserve the original source refusal
                # together with a secondary proof-save error.
                changed=copy.deepcopy(raw);changed['source_role']='FRESH_ACTUAL_CURRENT';identify(changed)
                def failed_save(proof):
                    assert proof['first_failed_check']=='fresh_current_capture_qualified'
                    raise OSError('V1528_SOFTWARE_SECONDARY_SAVE_ERROR')
                try:
                    contract.validate_saved(changed,source_graph_sha256=graph_sha,files=files,
                                            prepared_sources=sources,save_proof=failed_save)
                except contract.SourceRefusal as error:
                    assert 'CURRENT_WE_EVALUATION_SOURCE_REFUSED' in str(error)
                    assert 'V1528_SOFTWARE_SECONDARY_SAVE_ERROR' in error.save_error
                    secondary=dict(first_error=str(error),secondary_save_error=error.save_error,
                                   original_proof_retained=error.proof,software_injection=True)
                    codec.write_atomic(task/'SECONDARY_SAVE_ERROR.json',codec.encoded(secondary),writer)
                else:
                    raise AssertionError('SECONDARY_SAVE_FAILURE_ACCEPTED')
            assert all(common.sha(R / name) == identity for name, identity in sources.items())
            common.put(O/'SOURCE_CONTENT_QUALIFICATION.json',dict(passed=True,closed=True,cases=cases,
                       actual_saved_coordinate_projection=True,source_receipt_content_bound=True,
                       method_memory_or_model_origin_conversion_qualified=False,
                       actual_current_capture=False,old_source_graph_and_load_diagnosis_not_rerun=True,
                       prior_V1497_proof_reused=sources[files['binding_proof']],
                       writer=writer._read(),models=0,physical_native=0))
            common.put(O/'SOURCE_FREEZE.json',dict(files=sources,source_and_content_only_qualified=True,
                       method_epoch_qualified=False,model_response_or_actual_admission=False))
            result.update(passed=True,source_frozen=True,new_negative_cases=len(cases)-1,
                          saved_actual_content_bound=True,models_authorized=False)
    except BaseException as error:
        result.update(first_error=repr(error),traceback=traceback.format_exc())
    finally:
        sys.setprofile(None)
        result.update(closed=True,wall_s=time.monotonic()-start)
        common.put(O/'ENTRY_QUALIFICATION.json',result)
        sys.meta_path.remove(finder)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
