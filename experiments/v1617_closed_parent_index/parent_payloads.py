"""Exact original lossless metadata indexing body; new closed-field scope."""
import copy
import hashlib
import json
FIELDS=('latest_zero200_closure_qualification', 'latest_baseline_disposition_and_PRIEST_preparation', 'latest_actual_zero200_closure_qualification', 'latest_PRIEST_saved_thread_failure', 'latest_PRIEST_numeric_result', 'latest_PRIEST_response_once_preparation', 'latest_live_first_event_runtime_closed', 'latest_PRIEST_response_refusal_V1518', 'latest_PRIEST_origin_provenance_qualification', 'latest_initializer_guard_failure')
PAYLOAD_PATH='runs/v1617_closed_parent_index/source_target/PARENT_PAYLOADS.json'
def encoded(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def digest(v):
    return hashlib.sha256(encoded(v)).hexdigest()

def plan(parent, *, fields=FIELDS):
    assert tuple(fields) == FIELDS, 'PARENT_PAYLOAD_FIELD_SCOPE_CHANGED'
    assert parent['active_round'] is None and parent.get('active_math_round') is None and (not parent['models_now_authorized'])
    assert all((isinstance(parent[k], dict) and 'payload_reference' not in parent[k] for k in fields))
    payload = dict(format='CLOSED_PREPARATION_PAYLOADS_V1542', values={k: copy.deepcopy(parent[k]) for k in fields})
    candidate = copy.deepcopy(parent)
    identity = digest(payload)
    for key in fields:
        candidate[key] = dict(payload_reference=dict(path=PAYLOAD_PATH, sha256=identity, key=key))
    assert hydrate(candidate, payload) == parent, 'PARENT_LOSSLESS_RECONSTRUCTION_FAILED'
    return (payload, candidate)

def hydrate(candidate, payload):
    assert payload['format'] == 'CLOSED_PREPARATION_PAYLOADS_V1542' and set(payload['values']) == set(FIELDS)
    identity = digest(payload)
    parent = copy.deepcopy(candidate)
    for key in FIELDS:
        reference = parent[key]['payload_reference']
        assert reference == dict(path=PAYLOAD_PATH, sha256=identity, key=key), 'PARENT_PAYLOAD_REFERENCE_CHANGED'
        parent[key] = copy.deepcopy(payload['values'][key])
    return parent
