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
        text=(c.C/p.name).read_text().replace('v1608_reuse_manifest_target','v1603_capture_close_source').replace('v1608','v1603')
        assert ast.dump(ast.parse(text))==ast.dump(ast.parse(p.read_text())),p.name
        proof.append(dict(path=p.name,prior_SHA=c.sha(p),current_SHA=c.sha(c.C/p.name)))
    # These numerical/physical/control implementations were not changed or run.
    for name in ('source_owner.py','current_input.py','carrier.py','nominal.py','witness.py','gates.py','current_reserve.py','physical_guard.py','execution.py','live_guard.py'):
        assert any(row['path']==name for row in proof)
    return proof

def run(c,source,target,save,refused):
    old=c.R/'runs/v1606_stopped_source_preparation/source_target'
    reused={}
    for name in ('SOFTWARE_HISTORY_PREPARED.json','SOFTWARE_CURRENT_CAPTURE.json','LATE_SOURCE_PROOF.json','CLOSE_RESOURCE_ORDER.json'):
        path=old/name;assert c.sha(path)==c.read(c.C/'REUSE_INPUTS.json')[str(path.relative_to(c.R))]
        reused[name]=c.read(path)
    assert reused['SOFTWARE_HISTORY_PREPARED.json']['passed']
    assert reused['SOFTWARE_CURRENT_CAPTURE.json']['passed'] and reused['SOFTWARE_CURRENT_CAPTURE.json']['software_only']
    assert reused['LATE_SOURCE_PROOF.json']['passed'] is False
    assert reused['CLOSE_RESOURCE_ORDER.json']['passed']
    save(target/'SAVED_PREFIX_REUSE.json',dict(passed=True,old_failed_target_passed=False,
        prefix_SOFTWARE_only=True,proof_SHA={name:c.sha(old/name)for name in reused},models=0,physical_native=0))
    n=NS(run_id='SOFTWARE_STOPPED_SOURCE_TRANSACTION',vehicle=NS(count=0))
    # Only the newly added pending branch of the actual Unix datagram pump.
    # The SOFTWARE callback installs a sentinel, never a live bridge or model.
    import time
    pump_module=c.load('v1608_real_pending_source_pump',c.C/'pump.py')
    pumpfolder=target/'pending_socket';pumpfolder.mkdir();receipts=[]
    owner=NS(native=n,output=pumpfolder,bridge=None)
    def final_callback(value):
        assert value['kind']=='CURRENT_SOURCE_REFRESH_REQUEST_FILE'
        owner.bridge=NS(software_sentinel=True)
    owner.on_cusp=final_callback
    import os
    prior_cwd=Path.cwd();os.chdir(c.R)
    pump=pump_module.Pump(owner,check_budget=lambda stage,count:None,append=receipts.append)
    peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    try:
        peer.bind(pump.peer);pump.awaiting_source_refresh=True;pump.source_refresh_started=time.monotonic()
        peer.sendto(json.dumps(dict(kind='CURRENT_SOURCE_REFRESH_REQUEST_FILE',run_id=n.run_id)).encode(),pump.address)
        pump.iteration();assert owner.bridge.software_sentinel and not pump.awaiting_source_refresh and n.vehicle.count==0
        save(target/'PENDING_SOCKET_BRANCH.json',dict(passed=True,SOFTWARE_final_callback_only=True,
            actual_steps=0,models=0,receipt_kinds=[r['kind']for r in receipts]))
    finally:peer.close();pump.socket.close();os.chdir(prior_cwd)
    session=c.load('v1608_current_notice_storage',c.C/'event_session.py')
    noticefolder=target/'saved_notice_api';(noticefolder/'cusp_requests').mkdir(parents=True)
    original=c.R/'runs/v1603_capture_close_source/first_event/cusp_requests/event0000.json'
    archived=c.read(c.R/'runs/v1605_capture_runtime_recovery/ARCHIVE_INDEX.json')
    assert next(row for row in archived['files']if row['path']==str(original.relative_to(c.R)))['sha256']==c.sha(original)
    file=noticefolder/'cusp_requests/event0000.current.json';c.put(file,c.read(original),maximum=4*1024**2)
    saved=c.read(file);notice=dict(kind='CURRENT_SOURCE_REFRESH_REQUEST_FILE',run_id=saved['request']['run_id'],event_index=0,
        path=str(file.relative_to(c.R)),file_sha256=c.sha(file),request_sha256=saved['request']['request_sha256'])
    assert session.current_notice(notice,output=noticefolder,run_id=notice['run_id'],last_event_index=-1)==saved
    bad=dict(notice,file_sha256='0'*64)
    refused('final_notice_content_SHA',lambda:session.current_notice(bad,output=noticefolder,run_id=notice['run_id'],last_event_index=-1))
    save(target/'FINAL_NOTICE_STORAGE_PROOF.json',dict(passed=True,scope='EXPOSED_SAVED_REQUEST_STORAGE_ONLY_NOT_FRESH_INPUT',
        original_saved_path=str(original.relative_to(c.R)),original_SHA=c.sha(original),new_current_filename_binding=True,
        saved_packet_not_live_permission=True,models=0,physical_native=0))
    save(target/'SOURCE_TRANSACTION_PROOF.json',dict(passed=True,scope='SOFTWARE_SCHEMA_AND_SOURCE_TRANSACTION_ONLY',
        original_NativeStep_packet_function_called=True,original_NativeStep_constructor_called=False,
        actual_capture_qualified=False,new_original_tracker_updates=0,software_updates_this_target=0,prior_software_prefix_reused=True,
        original_state_and_control_memory_unchanged=True,numerical_permission=False,physical_permission=False))
    return dict(source_transaction=True,software_capture_only=True,actual_capture_qualified=False,models=0,physical_native=0)
