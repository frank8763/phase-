"""Once lossless parent metadata indirection, before actual owner activation.

No scientific value/counter is discarded. The exact original full parent is
already remotely restored in V1589; only obsolete descriptive snapshots gain
path/SHA references so original128KiB control cap and8KiB close headroom hold.
"""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2];O=R/'runs/v1590_runtime_control'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
encoded=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()+b'\n'


def main():
    assert sorted(os.sched_getaffinity(0))==[5] and time.time()<1795395600
    O.mkdir(exist_ok=False);path=R/'runs/v1382_weekend_campaign/LEDGER.json'
    raw=path.read_bytes();parent=json.loads(raw)
    assert parent['active_round']is parent['active_math_round']is None and not parent['models_now_authorized']
    with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    backup=R/'runs/v1589_complete_source_recovery';proof=json.loads((backup/'FULL_REMOTE_VERIFIED.json').read_text())
    assert proof['passed']and proof['every_member_SHA_and_link_text']and proof['whole_archive_SHA']
    index=json.loads((backup/'ARCHIVE_INDEX.json').read_text())
    member=next(v for v in index['files']if v['path']==str(path.relative_to(R)))
    assert member['sha256']==hashlib.sha256(raw).hexdigest()and member['bytes']==len(raw)
    snapshot=O/'PARENT_ORIGINAL.json';snapshot.write_bytes(raw)
    assert snapshot.read_bytes()==raw
    changed=copy.deepcopy(parent)
    keys=['latest_PRIEST_origin_provenance_preparation','latest_PRIEST_saved_input_numeric_result',
          'latest_MPPI_preparation','latest_PRIEST_response_evidence_qualification','latest_PRIEST_saved_input_proposal_preparation']
    for key in keys:
        assert key in changed and isinstance(changed[key],dict)
        changed[key]=dict(preserved_full_value_record=str(snapshot.relative_to(R)),record_sha256=sha(snapshot),
            field=key,original_remote_index=str((backup/'ARCHIVE_INDEX.json').relative_to(R)),
            original_remote_proof_sha256=sha(backup/'FULL_REMOTE_VERIFIED.json'))
    assert all(parent[k]==changed[k]for k in parent if k not in keys)
    for key in keys:assert json.loads(snapshot.read_text())[key]==parent[key]
    round_probe=copy.deepcopy(changed);round_probe['rounds'].append(dict(id='v1588_signed_policy_source',science=12,status='CLOSED_REFUSED_OR_FAILED',result='runs/v1588_signed_policy_source/first_event/COMPLETION.json'))
    assert len(encoded(round_probe))+8192<131072
    receipt=dict(passed=True,models=0,physical_native=0,original_sha256=sha(snapshot),
        original_bytes=len(raw),new_bytes=len(encoded(changed)),keys=keys,all_original_values_retained=True,
        exact_original_remote_verified=True,original_index_sha256=sha(backup/'ARCHIVE_INDEX.json'),
        original_remote_proof_sha256=sha(backup/'FULL_REMOTE_VERIFIED.json'),control_cap_bytes=131072,
        close_headroom_bytes=8192,probe_bytes=len(encoded(round_probe)),unix=time.time())
    (O/'PREPARED_RECEIPT.json').write_bytes(encoded(receipt))
    assert path.read_bytes()==raw
    temporary=path.with_suffix('.json.tmp');temporary.write_bytes(encoded(changed));temporary.replace(path)
    assert json.loads(path.read_text())==changed
    (O/'COMPACTED.json').write_bytes(encoded(dict(receipt,result_sha256=sha(path))))
    print(json.dumps(receipt))


if __name__=='__main__':main()
