"""Current origin -> complete13array DATA -> proof -> before/applied receipts.

One22MiB lossless current stream and8MiB emergency within a32MiB writer. Every
native current branch is retained; no downsampling, cache reuse or cap refill.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def exact(name,path,source):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class ActualSink:
    def __init__(self,*,folder,writer,boundary,scope,source,method,native):
        self.stream_module=exact('v1612_actual_exact_codec',C/'stream.py',source)
        self.codec=self.stream_module.codec();self.folder=self.codec.metered(folder,writer,boundary)
        assert writer.maximum==32*1024**2
        self.scope=scope;self.writer=writer;self.boundary_type=type(boundary);self.source=source;self.method=copy.deepcopy(method);self.native=native
        self.handle=(self.folder/'CURRENT.bin').open('xb');self.journal=(self.folder/'APPLIED_JOURNAL.jsonl').open('x',buffering=1)
        self.size=0;self.chain='0'*64;self.digest=hashlib.sha256();self.calls=0;self.applied=0
        self.pending_origin=None;self.pending_data=None;self.admitted=None;self.pending_row=None
        self.inflight=False;self.failed=False;self.closed=False;self.emergency_attempted=False;self.emergency_data_attempted=False
        self.last_applied_receipt=None

    def append(self,kind,payload,extra):
        assert not self.closed and not self.failed
        meta=self.codec.encoded(dict(kind=kind,call_index=self.calls,previous_chain_sha256=self.chain,
            response_method_sha256=self.method['response_method_sha256'],payload_sha256=hashlib.sha256(payload).hexdigest(),**extra))
        assert len(meta)<=16384 and len(payload)<=8*1024**2
        block=self.stream_module.HEADER.pack(b'WE12AC01',len(meta),len(payload))+meta+payload
        assert self.size+len(block)<=22*1024**2,'CURRENT_2200_COMPLETE_STREAM_BYTE_CAP'
        self.inflight=True
        try:
            assert self.handle.write(block)==len(block);self.handle.flush();self.codec.sync_readonly(self.folder/'CURRENT.bin')
            self.digest.update(block);self.chain=hashlib.sha256(self.chain.encode()+meta+payload).hexdigest();self.size+=len(block);self.inflight=False
        except BaseException:self.failed=True;raise
        return self.chain

    def origin(self,value):
        assert self.pending_origin is None and self.pending_data is None and self.pending_row is None
        assert value['source_packet']['native_tick']==self.native.applied
        payload=self.codec.encoded(value);assert len(payload)<=128*1024
        chain=self.append('ORIGIN',payload,{})
        self.pending_origin=dict(source_packet_sha256=value['source_packet_sha256'],native=self.native.applied,chain_sha256=chain)

    def complete(self,arrays,value):
        assert self.pending_origin is not None and self.pending_data is None
        assert value['source_packet_sha256']==self.pending_origin['source_packet_sha256']
        payload,description,n=self.stream_module.encode_arrays(arrays);assert n==2200
        assert int(arrays['native'][0])==self.pending_origin['native']
        try:
            chain=self.append('DATA',payload,dict(arrays=description,source_packet_sha256=value['source_packet_sha256'],
                model_counts=value['model_counts'],complete_native=2200,stored_before_gate=True))
        except BaseException as first:
            # Distinct pre-reserved emergency file, never a retry/overwrite of
            # a failed stream record. Completion/gate authority stays false.
            assert not self.emergency_data_attempted;self.emergency_data_attempted=True
            try:
                self.put('CURRENT_REJECTED_FULL.npz',payload)
                self.put('CURRENT_REJECTED_FULL.json',self.codec.encoded(dict(first_error=repr(first),arrays=description,
                    source_packet_sha256=value['source_packet_sha256'],model_counts=value['model_counts'],
                    saved_actions=n,payload_sha256=hashlib.sha256(payload).hexdigest(),complete_certificate=False,
                    stream_write_inflight_unknown=self.inflight,distinct_emergency_not_stream_retry=True)))
            except BaseException as secondary:first.secondary_emergency_save=repr(secondary)
            raise
        self.pending_data=dict(all13arrays_durable=True,stream_chain_sha256=chain,
            source_packet_sha256=value['source_packet_sha256'],native=self.pending_origin['native'])
        return copy.deepcopy(self.pending_data)

    def after_gate(self,proof,saved):
        assert saved==self.pending_data and proof['source_packet_sha256']==saved['source_packet_sha256']
        self.append('PROOF',self.codec.encoded(proof),{})
        self.admitted=dict(proof=copy.deepcopy(proof),saved=copy.deepcopy(saved))
        self.pending_origin=None;self.pending_data=None;self.calls+=1

    def before(self,row,proof,states,ctrl):
        assert self.pending_row is None and self.admitted is not None
        assert self.admitted['proof']==proof and proof['passed']and proof['complete_native']==2200
        assert states.shape==(2201,8)and ctrl.shape==(2200,4)
        assert proof['source_packet_sha256']==row['source_packet_sha256']and row['before_native']==self.native.vehicle.count
        assert row['applied']is False
        value=copy.deepcopy(row);identity=hashlib.sha256(self.codec.encoded(value)).hexdigest()
        self.journal.write(self.codec.encoded(dict(kind='BEFORE_NATIVE',row=value,source_row_sha256=identity,
            reserve_data_chain_sha256=self.admitted['saved']['stream_chain_sha256'])).decode()+'\n')
        self.journal.flush();self.codec.sync_readonly(self.folder/'APPLIED_JOURNAL.jsonl')
        self.pending_row=(value,identity)

    def after(self,row):
        assert self.pending_row is not None and row['applied']is True
        before,identity=self.pending_row
        assert all(row[k]==v for k,v in before.items()if k!='applied')
        v=self.native.vehicle
        full=dict(time=float(v.d.time),**{k:getattr(v.d,k).tolist()for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')})
        receipt=dict(kind='AFTER_NATIVE',row=copy.deepcopy(row),source_row_sha256=identity,
            after_native=v.count,after_full_state_sha256=hashlib.sha256(self.codec.encoded(full)).hexdigest(),
            root_native_count=v.audit.native_count,contact_records=len(v.contacts))
        self.journal.write(self.codec.encoded(receipt).decode()+'\n');self.journal.flush();self.codec.sync_readonly(self.folder/'APPLIED_JOURNAL.jsonl')
        receipt['durable_receipt_sha256']=hashlib.sha256(self.codec.encoded(receipt)).hexdigest()
        self.last_applied_receipt=receipt;self.pending_row=None;self.admitted=None;self.applied+=1

    def partial(self,failure,arrays):
        assert not self.emergency_attempted;self.emergency_attempted=True
        if arrays is not None:
            payload,description,n=self.stream_module.encode_arrays(arrays)
            self.put('CURRENT_PARTIAL.npz',payload)
            failure=dict(failure,partial_arrays=description,saved_prefix_native=n,payload_sha256=hashlib.sha256(payload).hexdigest())
        self.put('CURRENT_REFUSAL.json',self.codec.encoded(failure))
        self.failed=True

    def raw_bytes(self,name,payload):
        assert name=='BATCH_RETURN_RAW.npz'and len(payload)<=512*1024
        self.put(name,payload)

    def raw_proof(self,name,value):
        assert name=='BATCH_RETURN_RAW.json';self.put(name,self.codec.encoded(value))

    def put(self,name,payload):
        assert Path(name).name==name
        with self.scope.activate():
            self.codec.write_atomic(self.folder/name,payload,self.writer)

    def close(self,accounting):
        if self.closed:return
        self.handle.flush();self.codec.sync_readonly(self.folder/'CURRENT.bin');self.handle.close();self.journal.close();self.closed=True
        value=dict(closed=True,stream_bytes=self.size,actual_stream_bytes=(self.folder/'CURRENT.bin').stat().st_size,
            last_chain_sha256=self.chain,whole_stream_sha256=self.digest.hexdigest(),current_branches=self.calls,applied_receipts=self.applied,
            stream_write_inflight_unknown=self.inflight,pending_origin=self.pending_origin,pending_data=self.pending_data,
            pending_actual_row=None if self.pending_row is None else self.pending_row[0]['before_native'],
            failed=self.failed,accounting=accounting,scientific_pass_not_inferred=True,
            journal_sha256=hashlib.sha256((self.folder/'APPLIED_JOURNAL.jsonl').read_bytes()).hexdigest())
        self.put('CURRENT_CLOSED.json',self.codec.encoded(value))

# Every persistent-handle callback reenters its owned original boundary.
_spec=importlib.util.spec_from_file_location('v1612_sink_scope_calls',C/'scoped_output.py')
_scope_module=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_scope_module)
for _name in ('append','origin','complete','after_gate','before','after','partial','raw_bytes','raw_proof','put','close'):
    setattr(ActualSink,_name,_scope_module.scoped(getattr(ActualSink,_name)))
