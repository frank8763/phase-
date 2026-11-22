"""One policy timing proposal's durable blocks before tracker publication.

Same original13array schema/codec and real WriterBudget. New record framing
binds the decision and native block; it is not a model or physical certificate.
"""
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def load(name,path,source):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class ProposalSink:
    def __init__(self,*,folder,writer,boundary,method,source,setup,geometry):
        self.module=load('v1596_proposal_storage',C/'stream.py',source);self.codec=self.module.codec()
        self.folder=self.codec.metered(folder,writer,boundary);assert writer.maximum==32*1024**2
        self.schema=load('v1596_original_proposal13arrays',R/'experiments/v1552_complete_canonical_witness/evidence.py',source)
        self.writer=writer;self.method=method;self.setup=setup;self.geometry=geometry
        self.path=self.folder/'PROPOSAL.bin';self.handle=self.path.open('xb')
        self.bytes=0;self.rows=0;self.blocks=0;self.chain='0'*64;self.closed=False;self.inflight=False
        self.failed=False;self.partial_attempted=False;self.result_attempted=False

    def arrays(self,rows):
        assert rows and len(rows)<=5
        branch=self.schema.Branch(SimpleNamespace(snapshot=lambda:rows[0]['before']))
        branch.rows=rows
        return branch.arrays()

    def block(self,decision,rows):
        assert not self.closed and not self.failed and len(rows)==5
        expected=self.method['base_method']['fixed_origin_native']+self.rows
        assert all(row['before']['native']==expected+i and row['after']['native']==expected+i+1 for i,row in enumerate(rows))
        try:
            arrays=self.arrays(rows);payload,description,native=self.module.encode_arrays(arrays);assert native==5
            meta=self.codec.encoded(dict(kind='DATA',index=self.blocks,previous_sha256=self.chain,decision=decision,
                response_method_sha256=self.method['response_method_sha256'],native_start=expected,
                arrays=description,payload_sha256=hashlib.sha256(payload).hexdigest(),saved_before_policy_commit=True))
            assert len(meta)<=self.module.MAX_METADATA
            self.append(meta,payload)
            # Arrays are already durable when any numerical safety gate or
            # its proof is evaluated. This uses the same fixed current-clock
            # TIME field, never a full-period replacement or moving clock.
            import numpy as np
            s=arrays['states'];u=arrays['ctrl'];m=arrays['memory']
            lower=float(self.geometry.tube(s,expected));limits=np.asarray(self.setup['limits'])
            rates=.01*np.asarray(self.setup['slew_per_second'])
            checks=dict(finite=all(bool(np.isfinite(a).all())for a in arrays.values()),
                full_footprint_tube=lower>=.22-1e-8,
                ctrl_bounds=bool((u>=limits[:,0]-1e-8).all()and(u<=limits[:,1]+1e-8).all()),
                ctrl_slew=bool((abs(np.diff(np.vstack([m[0,:4],u]),axis=0))<=rates+1e-8).all()),
                body_caps=bool((abs(s[:,3:6])<=np.array([.13,.03,.16])+1e-8).all()),
                complete_clock=bool(np.max(abs(arrays['sim_time']-(self.method['base_method']['fixed_origin_sim_time']+
                    .01*(arrays['native']-self.method['base_method']['fixed_origin_native']))))<=1e-8))
            proof=self.codec.encoded(dict(passed=all(checks.values()),checks=checks,causal_tube_lower_m=lower,
                arrays_saved_before_gate=True,not_complete_stopping_witness=True))
            meta=self.codec.encoded(dict(kind='PROOF',index=self.blocks,previous_sha256=self.chain,
                payload_sha256=hashlib.sha256(proof).hexdigest()))
            self.append(meta,proof);self.blocks+=1;self.rows+=5
            assert all(checks.values()),'GOAL_BOUND_PROPOSAL_SAFETY_REFUSED'
            return self.chain
        except BaseException:
            self.failed=True;raise

    def append(self,meta,payload):
        assert len(meta)<=self.module.MAX_METADATA and len(payload)<=self.module.MAX_PAYLOAD
        record=self.module.HEADER.pack(b'WE12PR01',len(meta),len(payload))+meta+payload
        assert self.bytes+len(record)<=self.module.MAX_STREAM,'GOAL_BOUND_PROPOSAL_STREAM_CAP'
        self.inflight=True;assert self.handle.write(record)==len(record);self.handle.flush();self.codec.sync_readonly(self.path)
        self.inflight=False;self.chain=hashlib.sha256(self.chain.encode()+meta+payload).hexdigest();self.bytes+=len(record)

    def partial(self,rows,*,first_error,model_counts):
        assert not self.partial_attempted;self.partial_attempted=True
        payload,description,native=self.module.encode_arrays(self.arrays(rows))
        self.codec.write_atomic(self.folder/'PROPOSAL_PARTIAL.npz',payload,self.writer)
        self.codec.write_atomic(self.folder/'PROPOSAL_PARTIAL.json',self.codec.encoded(dict(
            arrays=description,acknowledged_native=native,first_error=first_error,model_counts=model_counts,
            payload_sha256=hashlib.sha256(payload).hexdigest(),not_complete_witness=True)),self.writer)

    def result(self,value):
        assert not self.result_attempted;self.result_attempted=True
        if not self.closed:
            self.handle.flush();self.codec.sync_readonly(self.path);self.handle.close();self.closed=True
        receipt=dict(complete=bool(value['passed']and not self.failed and not self.inflight),
            durable_native=self.rows,durable_blocks=self.blocks,acknowledged_bytes=self.bytes,
            actual_bytes=self.path.stat().st_size,write_inflight_unknown=self.inflight,
            last_chain_sha256=self.chain,whole_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest(),
            model_or_physical_certificate=False)
        if value['passed']:
            assert receipt['complete']and self.rows==value['nominal_native']and receipt['actual_bytes']==self.bytes
        self.codec.write_atomic(self.folder/'PROPOSAL_STORAGE.json',self.codec.encoded(receipt),self.writer)
        self.codec.write_atomic(self.folder/'PROPOSAL.json',self.codec.encoded(value),self.writer)


def verify(folder,*,method,source,check):
    """Read every proposal block and proof before freezing its stop timing."""
    import json
    folder=Path(folder);module=load('v1596_proposal_readback',C/'stream.py',source)
    receipt=json.loads((folder/'PROPOSAL_STORAGE.json').read_text());path=folder/'PROPOSAL.bin'
    assert receipt['complete']and not receipt['write_inflight_unknown']
    assert receipt['actual_bytes']==receipt['acknowledged_bytes']==path.stat().st_size<=module.MAX_STREAM
    assert hashlib.sha256(path.read_bytes()).hexdigest()==receipt['whole_sha256']
    chain='0'*64;blocks=0;rows=0;pending=False
    with path.open('rb')as stream:
        while True:
            check();header=stream.read(module.HEADER.size)
            if not header:break
            assert len(header)==module.HEADER.size
            magic,mlen,plen=module.HEADER.unpack(header)
            assert magic==b'WE12PR01'and mlen<=module.MAX_METADATA and plen<=module.MAX_PAYLOAD
            meta=stream.read(mlen);payload=stream.read(plen);assert len(meta)==mlen and len(payload)==plen
            value=json.loads(meta);assert value['previous_sha256']==chain and value['index']==blocks
            assert value['payload_sha256']==hashlib.sha256(payload).hexdigest()
            if value['kind']=='DATA':
                assert not pending;pending=True
                assert value['response_method_sha256']==method['response_method_sha256']
                assert value['native_start']==method['base_method']['fixed_origin_native']+rows
                arrays=module.record_codec().decode(payload,value['arrays'])
                assert len(arrays['ctrl'])==5 and arrays['native'].tolist()==list(range(value['native_start'],value['native_start']+6))
                rows+=5
            else:
                assert value['kind']=='PROOF'and pending and json.loads(payload)['passed']
                pending=False;blocks+=1
            chain=hashlib.sha256(chain.encode()+meta+payload).hexdigest()
    assert not pending and blocks==receipt['durable_blocks']and rows==receipt['durable_native']
    assert chain==receipt['last_chain_sha256']
    return receipt
