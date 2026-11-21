"""Bind a draft envelope to exact saved files and recorded receipt contents.

Only explicit immutable inputs are read. Callers must supply the independently
prepared path->SHA map; values in an untrusted envelope never pin themselves.
No new method-state epoch or current/fresh capture is accepted here.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inspect(raw, *, files, prepared_sources):
    """Return diagnostics; the outer contract must save them before refusing.

    No writer callback executes until this complete proof has been assembled.
    File and envelope failures retain the first failed stage and exact error.
    """
    proof = dict(passed=False, scope='SAVED_CONTENT_BINDING_ONLY', checked_files=[],
                 source_receipts_actual_content_verified=False,
                 model_projection_binding_verified=False,
                 mode_history_numerical_recompute_verified=False,
                 method_state_receipt_content_verified=False,
                 steering_load_state_qualified=False, actual_capture_qualified=False,
                 models_authorized=False, physical_permission=False,
                 coordinate_projection=None, stage='source_role')
    try:
        assert raw['source_role'] == 'SAVED_ACTUAL_MODEL_ONLY', 'FRESH_CAPTURE_UNIMPLEMENTED'
        assert set(files) == {'event_input', 'setup', 'states', 'journal', 'remote_index', 'remote_proof',
                              'binding_proof', 'public_map'}
        paths = {}
        limits = dict(event_input=1024**2, setup=1024**2, states=8*1024**2,
                      journal=32*1024**2, remote_index=8*1024**2, remote_proof=2*1024**2,
                      binding_proof=1024**2, public_map=1024**2)
        proof['stage'] = 'immutable_saved_files'
        for key, name in files.items():
            assert isinstance(name, str) and not Path(name).is_absolute()
            p = R / name
            assert '..' not in Path(name).parts and p.resolve().is_relative_to(R)
            assert key == 'public_map' or p.resolve().is_relative_to(R / 'runs')
            assert p.is_file() and not any(x.is_symlink() for x in [p, *p.parents])
            assert 0 < p.stat().st_size <= limits[key], 'SAVED_FILE_SIZE'
            identity = sha(p)
            assert prepared_sources[name] == identity, 'SAVED_FILE_NOT_IN_IMMUTABLE_CHAIN'
            paths[key] = p
            proof['checked_files'].append(dict(role=key, path=name, bytes=p.stat().st_size, sha256=identity))
        read = lambda key: json.loads(paths[key].read_text())
        remote = read('remote_proof')
        assert all(remote[k] is True for k in ['passed', 'every_member_SHA_and_link_text', 'recovery_index_download_SHA'])
        members = {row['path']: row for row in read('remote_index')['files']}
        for key in ['event_input', 'setup', 'states', 'journal']:
            row = members[files[key]]
            assert row['bytes'] == paths[key].stat().st_size and row['sha256'] == prepared_sources[files[key]]
        proof['stage'] = 'unchanged_original_event'
        original = read('event_input')
        clean = dict(original)
        identity = clean.pop('input_sha256')
        assert digest(clean) == identity
        assert raw['packet'] == original['origin'], 'MEASURED_PACKET_CHANGED'
        assert raw['fullstate_sha256'] == original['full_state_sha256'] == digest(raw['fullstate'])
        assert raw['mode_history'] == original['mode_history']
        assert raw['gear_memory'] == original['gear_memory']
        assert raw['causal_snapshot'] == original['causal_snapshot']
        assert raw['causal_snapshot_sha256'] == original['causal_snapshot_sha256'] == digest(raw['causal_snapshot'])
        n = raw['packet']['native_tick']
        assert type(n) is int and 0 <= n <= 40000
        proof['stage'] = 'recorded_fullstate_content'
        # This is an array reader and coordinate calculation, never a model.
        import numpy as np
        with np.load(paths['states'], allow_pickle=False) as arrays:
            assert all(k in arrays.files and len(arrays[k]) > n for k in raw['fullstate'])
            current = {k: (float(arrays[k][n]) if k == 'time' else arrays[k][n].tolist())
                       for k in raw['fullstate']}
        assert current == raw['fullstate'] and digest(current) == original['full_state_sha256']
        proof['stage'] = 'projection_content'
        projection_path = Path(__file__).with_name('origin_binding.py')
        assert prepared_sources[str(projection_path.relative_to(R))] == sha(projection_path)
        projection_spec = importlib.util.spec_from_file_location('v1528_pinned_origin_binding', projection_path)
        projection_module = importlib.util.module_from_spec(projection_spec)
        projection_spec.loader.exec_module(projection_module)
        projected = projection_module.compare(current, raw['packet'], read('setup'))
        proof['coordinate_projection'] = projected
        proof['projection_source_sha256'] = sha(projection_path)
        assert projected['passed'], 'RECORDED_COORDINATE_PROJECTION_REFUSED'
        proof['model_projection_binding_verified'] = True
        proof['stage'] = 'actual_receipt_content'
        normalizer = R / 'experiments/v1423_integrated_route_audit/recorded.py'
        assert prepared_sources[str(normalizer.relative_to(R))] == sha(normalizer)
        spec = importlib.util.spec_from_file_location('v1528_pinned_recorded_receipts', normalizer)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with paths['journal'].open() as stream:
            events = [json.loads(line) for line in stream if line.strip()]
        rows = module.receipts(events, before_kind='BEFORE_ORIGINAL_PREFIX_NATIVE',
                              after_kind='AFTER_ORIGINAL_PREFIX_NATIVE', bound_hash=False)
        assert len(rows) > n and [r['before_native'] for r in rows] == list(range(len(rows)))
        row = rows[n]
        assert row['source_full_state_sha256'] == raw['fullstate_sha256']
        assert row['body'] == raw['packet']['body']
        assert row['encoders'] == [*raw['packet']['steering']['position'], *raw['packet']['steering']['velocity']]
        assert row['last_ctrl'] == raw['packet']['controller_memory']['last_ctrl']
        assert row['integral'] == raw['packet']['controller_memory']['integral']
        assert all(r['applied'] is True for r in rows[:n])
        proof.update(source_receipts_actual_content_verified=True,
                     recorded_receipt_rows=len(rows), applied_prefix_native=n,
                     source_normalizer_sha256=sha(normalizer), original_event_input_sha256=identity)
        proof['stage'] = 'provenance_descriptor_binding'
        provenance = raw['provenance']
        assert provenance['applied_journal_sha256'] == prepared_sources[files['journal']]
        assert provenance['model_setup_sha256'] == prepared_sources[files['setup']]
        assert provenance['state_packet_binding_proof_sha256'] == prepared_sources[files['binding_proof']]
        assert provenance['causal_source_receipt_sha256'] == prepared_sources[files['event_input']]
        assert provenance['public_map_sha256'] == prepared_sources[files['public_map']]
        assert read('setup')['known'] == read('public_map')
        prior = read('binding_proof')
        assert prior['passed'] is True and prior['closed'] is True and prior['source_rows_covered'] == n
        assert prior['scope'] == 'SAVED_ACTUAL_INPUT_NEW_METHOD_SOURCE_ONLY'
        proof['prior_saved_projection_source_proof_reused_sha256'] = prepared_sources[files['binding_proof']]
        assert provenance['canonical_origin_native'] == 0 and provenance['applied_actions'] == n
        assert provenance['state_rows'] == provenance['contact_rows'] == n + 1
        assert provenance['root_guard_native'] == n and provenance['unrecorded_actual_gap'] == 0
        # Counts are descriptor bindings. Complete N+1/contact/root coverage and
        # continuous mode/gear execution are NOT independently audited here.
        proof.update(passed=True, stage='content_bound_no_authority',
                     complete_contact_root_coverage_independently_verified=False,
                     allstate_projection_independently_audited=False)
    except Exception as error:
        proof.update(first_error=repr(error), failed_stage=proof['stage'])
    return proof
