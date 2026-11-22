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
        text=(c.C/p.name).read_text().replace('v1606_stopped_source_preparation','v1603_capture_close_source').replace('v1606','v1603')
        assert ast.dump(ast.parse(text))==ast.dump(ast.parse(p.read_text())),p.name
        proof.append(dict(path=p.name,prior_SHA=c.sha(p),current_SHA=c.sha(c.C/p.name)))
    # These numerical/physical/control implementations were not changed or run.
    for name in ('source_owner.py','current_input.py','carrier.py','nominal.py','witness.py','gates.py','current_reserve.py','physical_guard.py','execution.py','live_guard.py'):
        assert any(row['path']==name for row in proof)
    return proof

def run(c,source,target,save,refused):
    history=c.load('v1606_software_history_api',c.C/'history.py')
    refresh=c.load('v1606_software_refresh_api',c.C/'refresh.py')
    capture=c.load('v1606_software_prepared_capture',c.C/'capture.py')
    provider=c.load('v1606_software_provider',c.C/'causal_provider.py')
    native_module=c.load('v1606_original_packet_definition_only',c.R/'experiments/v1567_epoch_scope_target/native_step.py')
    close=c.load('v1606_source_close_resource_api',c.C/'closure_resources.py')
    class Array(list):
        def tolist(self):return list(self)
    q=Array([0.]*20);q[0]=.3;q[3]=1.
    data=NS(time=0.,qpos=q,qvel=Array([0.]*19),ctrl=Array([0.]*11),mocap_pos=Array([]),mocap_quat=Array([]))
    adapter=NS(last=Array([0.]*4),integral=0.,_steering_motion_active=False,parked_target=None)
    modes=dict(canonical_origin_native=0,covered_native=0,coupled_episode=False,steering_motion_active=False,parked_target=None)
    vehicle=NS(count=0,d=data,commands=[],rows=[],contacts=[[]],audit=NS(native_count=0),bad=0,adapter=adapter,
        body=lambda:[.3,0.,0.,0.,0.],steering_sample=lambda:Array([0.]*4))
    n=object.__new__(native_module.NativeStep);n.vehicle=vehicle;n.run_id='SOFTWARE_STOPPED_SOURCE_TRANSACTION'
    n.applied=0;n.events=[];n.in_step=False;n.bridge_started=False;n.sent={};n.gear=NS(gear=1,last_tick=-1,brake_start=None)
    n.mode_memory=NS(snapshot=lambda tick:copy.deepcopy(modes))
    folder=target/'software_event';folder.mkdir()
    (folder/'ACTUAL_OWNER_JOURNAL.jsonl').write_text('')
    state=capture.fullstate(vehicle)
    save(folder/'SOURCE_T0_IDENTITY.json',dict(run_id=n.run_id,canonical_native=0,fullstate=state,fullstate_sha256=c.digest(state)))
    snapshot=c.read(c.R/'runs/v1574_current_owner_capture/SOURCE_INPUT.json')['causal_snapshot']
    snapshot=copy.deepcopy(snapshot);snapshot['periodic']['source_tick']=0
    # Explicit schema-only estimator adapter. No original tracker constructor,
    # update, forecast, model, Gear, or physics code is called.
    class SoftwareTracker:
        def __init__(self):self.records=[];self.last_tick=-1;self.calls=[]
        def snapshot(self):return copy.deepcopy(snapshot)
        def update(self,**kw):self.calls.append(copy.deepcopy(kw));self.last_tick=kw['native_tick'];return False
    a=object.__new__(provider.ObservedTracker);a._tracker=SoftwareTracker();a.run_id=n.run_id;a.output=folder
    a.receipts=[];a.head=None;a.last_sequence=-1;a.poisoned=False;a.journal=None;a.save=save
    def envelope(sequence,sampled):
        wire=dict(schema=1,run_id=n.run_id,sequence=sequence,sampled_at=sampled,native_tick=0,sim_time=0.,
            body=vehicle.body(),ranges_m=[3.]*32,sensor_frame=dict(native_tick=0,time=0.,xy=[.3,0.],yaw=0.,sampled_at=sampled))
        n.sent[sequence]=copy.deepcopy(wire)
        return dict(kind='ROUTE_ACTUAL_FRAME',wire=wire,evidence_state_sha256=c.digest(state),
            feedback=dict(native_tick=0,sim_time=0.,body=vehicle.body(),encoders=[0.]*4,last_ctrl=[0.]*4,integral=0.,
                parked_target=None,steering_motion_active=False,gear_memory=dict(gear=1,last_tick=-1,brake_start=None)))
    def packet(e):
        request=dict(run_id=n.run_id,event_index=0,brake_start=-250,next_segment=dict(gear=1,poses=[[0.,0.,0.],[1.,0.,0.]]),
            event=dict(kind='CUSP_NEXT_SEGMENT_CHECK',gear=1,body=vehicle.body(),source=dict(coefficient_tick=0)),
            actual=copy.deepcopy(e),causal_forecast=dict(coefficient_snapshot_sha256=c.digest(snapshot)))
        request['request_sha256']=c.digest(request)
        source=a.event_source(e,request)
        return dict(request=request,current_causal_source=source,causal_snapshot=copy.deepcopy(snapshot))
    first=envelope(0,10.);a.observe(first['wire']);initial=packet(first)
    prepared=history.PreparedHistory(native=n,output=folder,packet=initial,source=source,
        save=lambda p:save(target/'SOFTWARE_HISTORY_PREPARED.json',dict(p,software_only=True)))
    assert not prepared.proof['current_capture_passed']and not prepared.proof['physical_permission']
    transaction=refresh.Refresh(prepared,initial_notice=dict(kind='SOFTWARE_INITIAL_NOTICE'),prepared_monotonic=10.5)
    current=envelope(1,11.);token=transaction.bind_one_fresh_envelope(current)
    refused('second_real_wire_forbidden',lambda:transaction.bind_one_fresh_envelope(current))
    # A rejected branch poisons its own transaction; the original unfailed
    # transaction below is an independent SOFTWARE case, never a runtime retry.
    transaction=refresh.Refresh(prepared,initial_notice=dict(kind='SOFTWARE_INITIAL_NOTICE'),prepared_monotonic=10.5)
    token=transaction.bind_one_fresh_envelope(current)
    a.observe(current['wire']);final=packet(current);final['source_preparation_token']=token
    def software_prepare(e,segment,geometry,tracker,**kw):
        assert e==current and segment==initial['request']['next_segment']and tracker is a
        assert kw==dict(run_id=n.run_id,event_index=0,brake_start=-250,now=11.05)
        answer=copy.deepcopy(final);answer.pop('source_preparation_token');return answer
    refreshed=refresh.refreshed_packet(initial,token,current,tracker=a,geometry={},prepare_request=software_prepare,now=11.05)
    assert refreshed==final
    refused('ROS_refresh201ms',lambda:refresh.refreshed_packet(initial,token,current,tracker=a,geometry={},prepare_request=software_prepare,now=11.201))
    notice=dict(kind='CURRENT_SOURCE_REFRESH_REQUEST_FILE',source_preparation_token_sha256=c.digest(token))
    for name,mutate in [('next_segment',lambda p:p['request']['next_segment']['poses'][-1].__setitem__(0,2.)),
        ('fullstate',lambda p:p['request']['actual'].__setitem__('evidence_state_sha256','0'*64)),
        ('token',lambda p:p['source_preparation_token'].__setitem__('history_proof_sha256','0'*64))]:
        trial=copy.copy(transaction);bad=copy.deepcopy(final);mutate(bad)
        refused('refresh_'+name,lambda trial=trial,bad=bad:trial.accept_final(bad,notice))
    assert transaction.accept_final(final,notice)
    refused('second_final_notice',lambda:transaction.accept_final(final,notice))
    before=copy.deepcopy(state);saved=[]
    answer=capture.capture(n,current['wire'],run_id=n.run_id,prepared_sources=source,
        causal_source=final['current_causal_source'],request=final['request'],output=folder,
        setup=dict(dt=.01,steering_qpos_addresses=[7,9],steering_qvel_addresses=[6,8],actuator_ids=[0,1,2,3]),
        save_proof=lambda p:(saved.append(copy.deepcopy(p)),save(target/'SOFTWARE_CURRENT_CAPTURE.json',dict(p,software_only=True))),
        prepared_history=prepared,clock=lambda:11.05)
    assert saved[-1]['passed']and answer['fullstate']==before==capture.fullstate(vehicle)
    assert saved[-1]['causal_content']['prepared_inputs']==1 and saved[-1]['causal_content']['new_inputs']==1
    assert answer['physical_permission']is answer['numerical_permission']is False
    for name,key,value in [('prior_prefix','prefix_sha256','0'*64),('new_count','records',1)]:
        h=copy.copy(prepared);h.poisoned=False;bad=copy.deepcopy(final['current_causal_source']);bad['observation_journal'][key]=value
        refused(name,lambda h=h,bad=bad:h.extended_causal_content(bad,current['wire'],final['request']))
        assert h.poisoned
    h=copy.copy(prepared);h.poisoned=False
    def late():
        return capture.capture(n,current['wire'],run_id=n.run_id,prepared_sources=source,causal_source=final['current_causal_source'],
            request=final['request'],output=folder,setup={},save_proof=lambda p:save(target/'LATE_SOURCE_PROOF.json',p),prepared_history=h,clock=lambda:11.201)
    refused('source201ms_refused',late);assert c.read(target/'LATE_SOURCE_PROOF.json')['passed']is False
    class ResourceQuota:
        def __init__(self):self.grant='EXPIRED_SOFTWARE';self.external_writers=[];self.order=[]
        def retire_grant(self):self.order.append('retire');old=self.grant;self.grant=None;return old
        def prepare_grant(self,size,**kw):
            assert self.grant is None and size==32*1024**2
            assert kw['phase']=='COMPLETE_ZERO_TAIL_OR_CLOSURE'and kw['valid_for_s']==300
            self.order.append('prepare');self.grant=kw;return kw
    resource=ResourceQuota();proof=close.prepare(resource);assert resource.order==['retire','prepare']and not proof['action_or_source_authority_granted']
    save(target/'CLOSE_RESOURCE_ORDER.json',dict(passed=True,scope='SOFTWARE_CALLBACK_ORDER_NOT_REAL_RESOURCE_GRANT',proof=proof))
    assert a.close()['passed']
    # Only the newly added pending branch of the actual Unix datagram pump.
    # The SOFTWARE callback installs a sentinel, never a live bridge or model.
    import time
    pump_module=c.load('v1606_real_pending_source_pump',c.C/'pump.py')
    pumpfolder=target/'pending_socket';pumpfolder.mkdir();receipts=[]
    owner=NS(native=n,output=pumpfolder,bridge=None)
    def final_callback(value):
        assert value['kind']=='CURRENT_SOURCE_REFRESH_REQUEST_FILE'
        owner.bridge=NS(software_sentinel=True)
    owner.on_cusp=final_callback
    pump=pump_module.Pump(owner,check_budget=lambda stage,count:None,append=receipts.append)
    peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
    try:
        peer.bind(pump.peer);pump.awaiting_source_refresh=True;pump.source_refresh_started=time.monotonic()
        peer.sendto(json.dumps(dict(kind='CURRENT_SOURCE_REFRESH_REQUEST_FILE',run_id=n.run_id)).encode(),pump.address)
        pump.iteration();assert owner.bridge.software_sentinel and not pump.awaiting_source_refresh and n.vehicle.count==0
        save(target/'PENDING_SOCKET_BRANCH.json',dict(passed=True,SOFTWARE_final_callback_only=True,
            actual_steps=0,models=0,receipt_kinds=[r['kind']for r in receipts]))
    finally:peer.close();pump.socket.close()
    session=c.load('v1606_current_notice_storage',c.C/'event_session.py')
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
        actual_capture_qualified=False,new_original_tracker_updates=0,software_updates=len(a._tracker.calls),
        original_state_and_control_memory_unchanged=True,numerical_permission=False,physical_permission=False))
    return dict(source_transaction=True,software_capture_only=True,actual_capture_qualified=False,models=0,physical_native=0)
