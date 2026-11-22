"""New append/source target: SOFTWARE and exposed saved bytes, no estimators."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace as NS

def source_reuse(c):
    base=c.R/'experiments/v1599_readonly_context_durability'
    changed={'entry.py','common.py','source_owner_entry.py','writer_coverage.py',
        'source_owner.py','canonical_owner.py','route_ros.py','legacy_actual_audit.py'}
    reused=[]
    for p in base.glob('*.py'):
        if p.name in changed:continue
        text=(c.C/p.name).read_text().replace('v1602_append_causal_receipts','v1599_readonly_context_durability').replace('v1602','v1599')
        assert ast.dump(ast.parse(p.read_text()))==ast.dump(ast.parse(text)),p.name
        reused.append(dict(path=p.name,prior_sha256=c.sha(p),current_sha256=c.sha(c.C/p.name)))
    old=c.R/'experiments/v1574_current_owner_capture'
    for name in ('source_io.py','event_session.py'):
        assert (old/name).read_bytes()==(c.C/name).read_bytes();reused.append(dict(path=name,prior_sha256=c.sha(old/name)))
    text=(old/'capture.py').read_text().replace("R/'experiments/v1574_current_owner_capture/causal_provider.py'","Path(__file__).with_name('causal_provider.py')")
    assert ast.dump(ast.parse(text))==ast.dump(ast.parse((c.C/'capture.py').read_text()))
    text=(old/'canonical_owner.py').read_text().replace('live_components_installed=False,','live_components_installed=bool(self.native.bridge_started),\n            bridge_object_present=self.bridge is not None,')
    assert ast.dump(ast.parse(text))==ast.dump(ast.parse((c.C/'capture_owner.py').read_text()))
    for name in ('source_owner.py','canonical_owner.py'):
        text=(base/name).read_text()
        if name=='source_owner.py':
            text=text.replace('R=Path(__file__).resolve().parents[2]','R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent')
            text=text.replace("R/'experiments/v1574_current_owner_capture/capture.py'","C/'capture.py'")
        else:text=text.replace("R/'experiments/v1574_current_owner_capture/canonical_owner.py'","C/'capture_owner.py'")
        text=text.replace('v1599_append_causal_receipts','v1602_append_causal_receipts').replace('v1599','v1602')
        assert ast.dump(ast.parse(text))==ast.dump(ast.parse((c.C/name).read_text())),name
    text=(c.C/'legacy_actual_audit.py').read_text().replace('v1602','v1599')
    text=text.replace("    measurements=exact('v1599_actual_measurement_sources',C/'measurement_source.py',source)\n",'')
    start=text.index('        def state_at(tick):',text.index('def integrated('))
    end=text.index("        elif event['kind']=='RECEIVED_ACTUAL_ROUTE'",start)
    text=text[:start]+"""        if event['kind']=='PUBLISHED_ACTUAL_ENVELOPE':
            e=event['envelope'];wire=e['wire'];frames.validate_wire(wire)
            assert wire['sequence']not in sent and wire['run_id']==task['run_id'];sent[wire['sequence']]=wire
            tick=wire['native_tick'];state={k:full[k][tick].tolist()if hasattr(full[k][tick],'tolist')else full[k][tick]for k in ('time','qpos','qvel','ctrl','mocap_pos','mocap_quat')}
            assert scalar.recorded.digest(state)==e['evidence_state_sha256']
"""+text[end:]
    assert ast.dump(ast.parse(text))==ast.dump(ast.parse((base/'legacy_actual_audit.py').read_text()))
    return reused

def run(c,source,target,save,refused):
    journal=c.load('v1602_target_journal',c.C/'observation_journal.py')
    provider=c.load('v1602_target_provider',c.C/'causal_provider.py')
    close=c.load('v1602_target_close',c.C/'provider_close.py')
    frames=c.load('v1602_target_frame_schema',c.R/'experiments/v1396_rpp_rpc_retirement/frames.py')
    measurement=c.load('v1602_target_measurements',c.C/'measurement_source.py')
    oldpath=c.R/'experiments/v1574_current_owner_capture/causal_provider.py'
    def method(path,name):
        cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef)and n.name=='ObservedTracker')
        return next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name==name)
    calls=[]
    for path in (oldpath,c.C/'causal_provider.py'):
        calls.append([ast.dump(n)for n in ast.walk(method(path,'observe'))if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='update'])
    assert calls[0]==calls[1]and len(calls[0])==1
    for name in ('snapshot','occupied_ball','raster'):
        assert ast.dump(method(oldpath,name))==ast.dump(method(c.C/'causal_provider.py',name))
    before=method(oldpath,'__init__');after=copy.deepcopy(method(c.C/'causal_provider.py','__init__'))
    # Original last statement is poisoned=False, followed by one journal=None.
    assert ast.unparse(after.body[-1])=='self.journal = None'
    after.body.pop();assert ast.dump(before)==ast.dump(after)
    folder=target/'saved_semantics';folder.mkdir()
    stream=journal.ObservationJournal(folder);refs=[];manifest=c.read(c.O/'SAVED_ROWS_INPUT.json')
    head=None;total=0
    for i,item in enumerate(manifest['rows']):
        path=c.R/item['path'];assert c.sha(path)==item['sha256']and path.stat().st_size==item['bytes']
        row=c.read(path);assert row['index']==i and row['previous_sha256']==head
        ref=stream.append(row);assert ref['semantic_sha256']==c.digest(row)
        refs.append(ref);head=ref['semantic_sha256'];total+=ref['file_size']
    prefix=stream.prefix();raw=journal.read_prefix(folder,prefix);offset=0
    for ref,item in zip(refs,manifest['rows']):
        row,offset=journal.row_at(raw,ref,path=prefix['path'],offset=offset)
        assert row==c.read(c.R/item['path'])
    assert offset==total==len(raw)
    extra=dict(c.read(c.R/manifest['rows'][-1]['path']),index=len(refs),previous_sha256=head)
    stream.append(extra);assert journal.read_prefix(folder,prefix)==raw
    closed=stream.close();assert closed['passed']and stream.close()['passed']
    save(target/'SAVED_SEMANTICS.json',dict(passed=True,rows=len(refs),all_saved_rows_semantically_identical=True,
        input_manifest_sha256=c.sha(c.O/'SAVED_ROWS_INPUT.json'),input_remote_proof=manifest['full_remote_proof'],
        fixed_prefix_sha256=prefix['prefix_sha256'],prefix_bytes=len(raw),journal_close=closed,
        old_tracker_updates=0,new_integrations=0,not_actual_runtime=True))
    def newjournal(name):
        folder=target/name;folder.mkdir();return journal.ObservationJournal(folder)
    row=dict(index=0,scope='SOFTWARE_FAULT_ONLY',value='complete')
    for name,bad in [('rowcap',dict(row,value='x'*journal.MAX_ROW)),('nonfinite',dict(row,value=float('nan'))),('index',dict(row,index=1))]:
        j=newjournal(name);refused(name,lambda j=j,bad=bad:j.append(bad))
        assert j.failed and not j.records;refused(name+'_no_retry',lambda j=j:j.append(row));assert not j.close()['passed']
    j=newjournal('partial_write');real=j.handle
    class Partial:
        def write(self,data):real.write(data[:7]);real.flush();raise OSError('SOFTWARE_PARTIAL_7_BYTES')
        def __getattr__(self,key):return getattr(real,key)
    j.handle=Partial();refused('partial_write',lambda:j.append(row));proof=j.close()
    assert proof['actual_bytes']==7 and proof['acknowledged_bytes']==0 and proof['inflight_append_unknown']and not proof['passed']
    save(target/'PARTIAL_UNKNOWN.json',proof)
    j=newjournal('sync_failure');real_sync=journal.sync_readonly
    def denied(*args):raise OSError('SOFTWARE_READONLY_FSYNC_FAILURE')
    journal.sync_readonly=denied
    try:
        refused('sync_failure',lambda:j.append(row));p=j.close()
        assert not p['passed']and p['errors']and p['inflight_append_unknown']
    finally:journal.sync_readonly=real_sync
    assert not j.close()['passed']and j.close()['errors']==p['errors'];save(target/'CLOSE_LATCHED.json',p)
    j=newjournal('close_after_ack');j.append(row);journal.sync_readonly=denied
    try:p=j.close()
    finally:journal.sync_readonly=real_sync
    assert p['descriptor_close_verified']and not p['passed']and not j.close()['passed'];save(target/'CLOSE_AFTER_ACK_FAILED.json',p)
    bad=dict(prefix,prefix_sha256='0'*64);refused('prefix_SHA',lambda:journal.read_prefix(target/'saved_semantics',bad))
    for key,value in [('offset',1),('file_size',1),('file_sha256','0'*64),('semantic_sha256','0'*64),('path','runs/wrong')]:
        ref=dict(refs[0]);ref[key]=value
        refused('slice_'+key,lambda ref=ref:journal.row_at(raw,ref,path=prefix['path'],offset=0))
    fixed=c.read(c.R/'runs/v1574_current_owner_capture/SOURCE_INPUT.json')
    request=fixed['request'];wire=request['actual']['wire'];snapshot=fixed['causal_snapshot']
    class SoftwareTracker:
        def __init__(self):self.records=[];self.last_tick=-1;self.calls=[]
        def snapshot(self):return copy.deepcopy(snapshot)
        def update(self,**kwargs):self.calls.append(copy.deepcopy(kwargs));self.last_tick=kwargs['native_tick'];return False
    def adapter(folder):
        a=object.__new__(provider.ObservedTracker);a._tracker=SoftwareTracker();a.run_id=wire['run_id'];a.output=folder
        a.save=save;a.receipts=[];a.head=None;a.last_sequence=-1;a.poisoned=False;a.journal=None;return a
    folder=target/'provider';folder.mkdir();a=adapter(folder);assert a.observe(wire)is False
    assert a._tracker.calls==[dict(native_tick=wire['native_tick'],sim_time=wire['sim_time'],center_body=wire['body'],ranges=wire['ranges_m'])]
    origin=a.event_source(request['actual'],request)
    native=NS(run_id=wire['run_id'],vehicle=NS(count=wire['native_tick']),sent={wire['sequence']:wire})
    check=lambda o,n=native:provider.verify(o,n,wire,request,prepared_sources=source,output=folder)
    evidence=check(origin);assert not evidence['provider_runtime_qualified']
    for key,value in [('covered_native',wire['native_tick']+1),('snapshot_sha256','0'*64),('all_published_scans_observed',True),('receipt_head_sha256','0'*64),('storage_provider_definition','wrong'),('journal_definition','wrong')]:
        bad=copy.deepcopy(origin);bad[key]=value;refused('provider_'+key,lambda bad=bad:check(bad))
    changed=NS(run_id=native.run_id,vehicle=native.vehicle,sent={wire['sequence']:dict(wire,body=[0]*5)})
    refused('provider_actualwire',lambda:check(origin,changed))
    refused('provider_duplicate',lambda:a.observe(wire));refused('provider_no_retry',lambda:a.observe(wire));assert not a.close()['passed']
    failedfolder=target/'provider_append_failure';failedfolder.mkdir();f=adapter(failedfolder)
    f.journal=provider.journal.ObservationJournal(failedfolder)
    def append_denied(row):raise OSError('SOFTWARE_APPEND_UNACKNOWLEDGED')
    f.journal.append=append_denied;refused('provider_append_failure',lambda:f.observe(wire))
    assert f.poisoned and not f.receipts and f.head is None and len(f._tracker.calls)==1
    refused('provider_append_failure_no_retry',lambda:f.observe(wire));assert not f.close()['passed']
    capture=c.load('v1602_target_capture',c.C/'capture.py');owner=c.load('v1602_target_capture_owner',c.C/'capture_owner.py')
    assert Path(capture.provider.__file__)==Path(provider.__file__)==Path(owner.capture_module.provider.__file__)
    assert owner.io.C==c.C and Path(owner.session.__file__)==c.C/'event_session.py'
    try:capture.capture(object(),wire,run_id=wire['run_id'],prepared_sources=source,causal_source=origin,
        request=request,output=folder,setup={},save_proof=denied)
    except capture.CaptureRefusal as error:
        assert error.proof['first_error']and 'SOFTWARE_READONLY_FSYNC_FAILURE'in error.secondary
        save(target/'CAPTURE_FIRST_SECONDARY.json',dict(first=str(error),secondary=error.secondary,proof=error.proof))
    else:raise AssertionError('CAPTURE_FIRST_ERROR_LOST')
    for failedsend,failedclose in [(False,False),(True,False),(False,True),(True,True)]:
        calls=[];result=dict(passed=True,error='ORIGINAL_SOFTWARE_FIRST')
        def stop():
            calls.append('stop')
            if failedsend:raise OSError('SOFTWARE_STOP_ERROR')
        def finish():
            calls.append('close')
            if failedclose:raise OSError('SOFTWARE_CLOSE_ERROR')
            return dict(passed=True,closed=True)
        proof=close.close(NS(close=finish),result,stop)
        assert calls==['stop','close']and result['error']=='ORIGINAL_SOFTWARE_FIRST'
        assert result['passed']==(not failedsend and not failedclose)
        assert len(result.get('causal_source_secondary_errors',[]))==failedsend+failedclose
        save(target/('PROVIDER_CLOSE_%s_%s.json'%(failedsend,failedclose)),dict(result=result,proof=proof))
    sent={};state=dict(time=0.,qpos=[1.],qvel=[0.],ctrl=[0.],mocap_pos=[],mocap_quat=[])
    for seq,kind in enumerate(('PUBLISHED_ACTUAL_ENVELOPE','CURRENT_SHARED_POLICY_DELIVERY')):
        w=dict(wire,sequence=seq);event=dict(kind=kind,envelope=dict(wire=w,evidence_state_sha256=c.digest(state)))
        evidence=measurement.bind(event,sent=sent,run_id=wire['run_id'],state_at=lambda tick:state,
            validate_wire=frames.validate_wire,state_digest=c.digest)
        assert evidence['transported_to_ROS']==(seq==0)
        refused('measurement_duplicate_'+str(seq),lambda:measurement.bind(event,sent=sent,run_id=wire['run_id'],state_at=lambda tick:state,validate_wire=frames.validate_wire,state_digest=c.digest))
        bad=copy.deepcopy(event);bad['envelope']['wire']['sequence']=seq+20;bad['envelope']['evidence_state_sha256']='0'*64
        refused('measurement_fullstate_'+str(seq),lambda:measurement.bind(bad,sent=sent,run_id=wire['run_id'],state_at=lambda tick:state,validate_wire=frames.validate_wire,state_digest=c.digest))
    save(target/'PROVIDER_BINDING.json',dict(passed=True,scope='SOFTWARE_ONLY_NOT_LIVE',proof=check(origin),
        shared_provider_path=str(Path(provider.__file__).relative_to(c.R)),original_tracker_update_calls=0,
        software_update_calls=1,actual_capture_qualified=False,both_measured_envelope_paths_bound=True,
        local_delivery_claimed_as_ROS_transport=False))
    return dict(saved_rows=len(refs),saved_row_bytes=total,original_tracker_update_call_AST_identical=True,
        models=0,actual_capture_qualified=False,append_fault_and_close_source_qualified=True)
