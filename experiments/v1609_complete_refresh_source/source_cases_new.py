"""New stopped preparation/one-refresh source transaction, SOFTWARE only."""
import ast
import copy
import json
import socket
from pathlib import Path
from types import SimpleNamespace as NS

def reuse(c):
    base=c.R/'experiments/v1603_capture_close_source'
    changed={'common.py','entry.py','source_target.py','receipt_cases.py','writer_coverage.py',
        'native_driver.py','capture.py','capture_owner.py','event_session.py','pump.py','route_ros.py'}
    proof=[]
    for p in base.glob('*.py'):
        if p.name in changed:continue
        text=(c.C/p.name).read_text().replace('v1609_complete_refresh_source','v1603_capture_close_source').replace('v1609','v1603')
        assert ast.dump(ast.parse(text))==ast.dump(ast.parse(p.read_text())),p.name
        proof.append(dict(path=p.name,prior_SHA=c.sha(p),current_SHA=c.sha(c.C/p.name)))
    # These numerical/physical/control implementations were not changed or run.
    for name in ('source_owner.py','current_input.py','carrier.py','nominal.py','witness.py','gates.py','current_reserve.py','physical_guard.py','execution.py','live_guard.py'):
        assert any(row['path']==name for row in proof)
    return proof

def run(c,source,target,save,refused):
    paths=[
        'runs/v1606_stopped_source_preparation/source_target/SOFTWARE_HISTORY_PREPARED.json',
        'runs/v1606_stopped_source_preparation/source_target/SOFTWARE_CURRENT_CAPTURE.json',
        'runs/v1606_stopped_source_preparation/source_target/LATE_SOURCE_PROOF.json',
        'runs/v1606_stopped_source_preparation/source_target/CLOSE_RESOURCE_ORDER.json',
        'runs/v1608_reuse_manifest_target/source_target/SAVED_PREFIX_REUSE.json',
        'runs/v1608_reuse_manifest_target/source_target/PENDING_SOCKET_BRANCH.json',
        'runs/v1608_reuse_manifest_target/source_target/FINAL_NOTICE_STORAGE_PROOF.json',
        'runs/v1608_reuse_manifest_target/source_target/SOURCE_TRANSACTION_PROOF.json',
        'runs/v1607_canonical_socket_source/SOFTWARE_RAW_EXACT_RESTORATION.json']
    binding=c.read(c.C/'REUSE_INPUTS.json');proof={}
    for name in paths:
        assert c.sha(c.R/name)==binding[name]
        proof[name]=c.read(c.R/name)
    assert proof[paths[0]]['passed'] and proof[paths[1]]['passed']
    assert proof[paths[2]]['passed'] is False and proof[paths[3]]['passed']
    assert all(proof[name]['passed'] for name in paths[4:8])
    assert proof[paths[8]]['original_individual_file_and_semantic_and_whole_SHA_all_matched']
    assert proof[paths[7]]['actual_capture_qualified'] is False
    save(target/'SOURCE_PREFIX_REUSE.json',dict(passed=True,source_only=True,
        reused_prefix_path_SHA={name:binding[name]for name in paths},old_failed_target_still_failed=True,
        new_software_transactions_executed=0,old_qualifiers_or_workers_rerun=False,
        original_models_Gear_FFI_Allocator_tracker_updates=0,actual_capture_qualified=False))
    return dict(source_transaction_prefix_by_exact_SHA=True,prior_failed_targets_preserved=True,
        actual_capture_qualified=False,models=0,physical_native=0,new_source_cases_only_metadata=True)
