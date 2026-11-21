"""Fixed-cap lossless13array stream; scientific admission is never inferred.

No models or constructors on import. Explicit original writer/boundary only.
"""
import hashlib
import importlib.util
import io
import json
import struct
from pathlib import Path

R=Path(__file__).resolve().parents[2]
MAGIC=b'WE13XL01'
HEADER=struct.Struct('>8sII')
MAX_STREAM=22*1024**2
MAX_PAYLOAD=8*1024**2
MAX_METADATA=16384
MAX_BRANCHES=563
KEYS={'states','ctrl','memory','modes','gear','encoders','parked','native','sim_time','raw_rows','requested_body','applied_body','gear_proof'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def codec():
    path=R/'experiments/v1507_priest_response_evidence/branch_store.py'
    spec=importlib.util.spec_from_file_location('v1554_original_exactcodec',path)
    value=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def record_codec():
    path=Path(__file__).resolve().parent/'record_codec.py'
    spec=importlib.util.spec_from_file_location('v1562_exact_xor_codec',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def encode_arrays(arrays):
    return record_codec().encode(arrays)


class Stream:
    def __init__(self,folder,*,writer,boundary,binding,ordered_names):
        self.codec=codec()
        self.folder=self.codec.metered(folder,writer,boundary)
        assert writer.maximum==32*1024**2
        assert binding['scientific_integration_revision']==10 and binding['geometry_kind']=='FULL_PERIOD_DISK'
        assert type(binding['response_method_sha256'])is str and len(binding['response_method_sha256'])==64
        self.binding=self.codec.normalized(binding)
        self.binding_sha=sha(self.codec.encoded(binding))
        assert len(ordered_names)==len(set(ordered_names))==MAX_BRANCHES
        assert sha(self.codec.encoded(list(ordered_names)))==binding['ordered_names_sha256']
        self.ordered_names=list(ordered_names)
        self.writer=writer
        self.path=self.folder/'WITNESSES.bin'
        self.handle=self.path.open('xb')
        self.digest=hashlib.sha256()
        self.chain='0'*64
        self.size=0
        self.data_count=0
        self.proof_count=0
        self.pending=None
        self.pending_complete=None
        self.closed=False
        self.write_inflight=False
        self.emergency_attempted=False

    def append(self,kind,name,payload,extra):
        assert kind in {'DATA','PROOF'}and not self.closed
        assert self.pending is None if kind=='DATA'else self.pending==name
        metadata=self.codec.encoded(dict(kind=kind,name=name,index=self.data_count if kind=='DATA'else self.proof_count,
            binding_sha256=self.binding_sha,previous_chain_sha256=self.chain,payload_sha256=sha(payload),**extra))
        assert len(metadata)<=MAX_METADATA and len(payload)<=MAX_PAYLOAD
        record=HEADER.pack(MAGIC,len(metadata),len(payload))+metadata+payload
        assert self.size+len(record)<=MAX_STREAM,'LOSSLESS_WITNESS_STREAM_CAP_REFUSED'
        self.write_inflight=True
        assert self.handle.write(record)==len(record)
        self.handle.flush()
        self.codec.sync_readonly(self.path)
        self.write_inflight=False
        self.digest.update(record)
        self.chain=sha(self.chain.encode()+metadata+payload)
        self.size+=len(record)

    def save_data(self,name,arrays,*,accounting,complete,first_error=None):
        assert self.data_count<MAX_BRANCHES and Path(name).name==name
        assert name==self.ordered_names[self.data_count]
        payload,description,native=encode_arrays(arrays)
        self.append('DATA',name,payload,dict(arrays=description,acknowledged_native=native,
            model_counts=accounting,complete=bool(complete and first_error is None),first_error=first_error,
            stored_before_safety_or_comparison_gate=True))
        self.pending=name
        self.pending_complete=bool(complete and first_error is None)
        self.data_count+=1

    def save_proof(self,name,proof):
        assert self.pending==name
        payload=self.codec.encoded(proof)
        assert len(payload)<=MAX_METADATA
        self.append('PROOF',name,payload,{})
        self.pending=None
        self.pending_complete=None
        self.proof_count+=1

    def emergency(self,name,arrays,*,first_error,accounting,nominal_prefix=None):
        assert not self.emergency_attempted
        self.emergency_attempted=True
        payload,description,native=encode_arrays(arrays)
        nominal=None
        if nominal_prefix is not None:
            nominal,nominal_description,nominal_native=encode_arrays(nominal_prefix)
            assert len(payload)+len(nominal)<=MAX_PAYLOAD,'EMERGENCY_BRANCH_PLUS_NOMINAL_SLOT_CAP'
        path=self.folder/'LAST_REJECTED_BRANCH.npz'
        self.codec.write_atomic(path,payload,self.writer)
        proof=dict(name=name,complete=False,first_error=first_error,model_counts=accounting,
             acknowledged_saved_native=native,binding=self.binding,arrays=description,
             payload_sha256=sha(payload),payload_bytes=len(payload),write_retry_permitted=False,representation='XOR_ROW_BYTEPLANES_LZMA_V1')
        if nominal is not None:
            self.codec.write_atomic(self.folder/'NOMINAL_PREFIX.npz',nominal,self.writer)
            proof['nominal_prefix']=dict(acknowledged_native=nominal_native,arrays=nominal_description,
                payload_bytes=len(nominal),payload_sha256=sha(nominal))
        self.codec.write_atomic(self.folder/'LAST_REJECTED_BRANCH.json',self.codec.encoded(proof),self.writer)
        return proof

    def abort(self,*,first_error,accounting):
        secondary=[]
        if not self.closed:
            try:
                self.handle.flush();self.codec.sync_readonly(self.path)
            except BaseException as error:
                secondary.append('stream_flush:'+repr(error))
            try:self.handle.close()
            except BaseException as error:secondary.append('stream_close:'+repr(error))
            self.closed=True
        result=dict(first_error=first_error,model_counts=accounting,secondary_errors=secondary,
            binding=self.binding,acknowledged_data=self.data_count,acknowledged_proofs=self.proof_count,
            pending_data_name=self.pending,acknowledged_stream_bytes=self.size,
            pending_complete=self.pending_complete,
            actual_stream_bytes=self.path.stat().st_size,stream_write_inflight_unknown=self.write_inflight,
            complete=False,emergency_attempted=self.emergency_attempted)
        self.codec.write_atomic(self.folder/'STREAM_ABORT.json',self.codec.encoded(result),self.writer)
        return result

    def seal(self,*,generation_result_sha256):
        assert not self.closed and self.pending is None and self.data_count==self.proof_count==MAX_BRANCHES
        assert not self.write_inflight and not self.emergency_attempted
        self.handle.flush();self.codec.sync_readonly(self.path);self.handle.close();self.closed=True
        assert self.path.stat().st_size==self.size
        digest=hashlib.sha256()
        with self.path.open('rb')as stream:
            for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
        assert digest.hexdigest()==self.digest.hexdigest()
        seal=dict(binding=self.binding,binding_sha256=self.binding_sha,stream_bytes=self.size,
            stream_sha256=digest.hexdigest(),data_records=self.data_count,proof_records=self.proof_count,
            last_chain_sha256=self.chain,generation_result_sha256=generation_result_sha256,
            storage_complete=True,scientific_pass_not_inferred=True)
        self.codec.write_atomic(self.folder/'STREAM_SEAL.json',self.codec.encoded(seal),self.writer)
        return seal


class Reader:
    def __init__(self,folder,*,expected_binding,expected_result_sha256,ordered_names,check=lambda:None):
        self.folder=Path(folder)
        self.codec=codec()
        self.binding=self.codec.normalized(expected_binding)
        assert len(ordered_names)==len(set(ordered_names))==MAX_BRANCHES
        assert sha(self.codec.encoded(list(ordered_names)))==expected_binding['ordered_names_sha256']
        self.ordered_names=list(ordered_names)
        self.seal=json.loads((self.folder/'STREAM_SEAL.json').read_text())
        assert self.seal['binding']==self.binding
        assert self.seal['binding_sha256']==sha(self.codec.encoded(self.binding))
        assert self.seal['generation_result_sha256']==expected_result_sha256
        assert self.seal['data_records']==self.seal['proof_records']==MAX_BRANCHES
        assert self.seal['storage_complete']and self.seal['stream_bytes']<=MAX_STREAM
        self.path=self.folder/'WITNESSES.bin'
        assert self.path.stat().st_size==self.seal['stream_bytes']
        self.offsets={}
        self.check=check
        self.verify()

    def verify(self):
        import numpy as np
        digest=hashlib.sha256();chain='0'*64;pending=None;data_count=proof_count=0
        with self.path.open('rb')as stream:
            while True:
                self.check()
                header=stream.read(HEADER.size)
                if not header:break
                assert len(header)==HEADER.size
                magic,metadata_size,payload_size=HEADER.unpack(header)
                assert magic==MAGIC and metadata_size<=MAX_METADATA and payload_size<=MAX_PAYLOAD
                meta=stream.read(metadata_size);offset=stream.tell();payload=stream.read(payload_size)
                assert len(meta)==metadata_size and len(payload)==payload_size
                value=json.loads(meta)
                assert value['binding_sha256']==self.seal['binding_sha256']and value['previous_chain_sha256']==chain
                assert value['payload_sha256']==sha(payload)
                name=value['name']
                if value['kind']=='DATA':
                    assert pending is None and value['index']==data_count and name not in self.offsets
                    assert name==self.ordered_names[data_count]
                    assert value['complete']is True and value['first_error']is None
                    arrays=record_codec().decode(payload,value['arrays'])
                    assert set(arrays)==KEYS
                    self.offsets[name]=(offset,payload_size,value['payload_sha256'],value['arrays'])
                    pending=name;data_count+=1
                else:
                    assert value['kind']=='PROOF'and pending==name and value['index']==proof_count
                    proof=json.loads(payload)
                    assert proof['safety']['passed']and (proof['comparison']is None or proof['comparison']['passed'])
                    pending=None;proof_count+=1
                digest.update(header+meta+payload)
                chain=sha(chain.encode()+meta+payload)
        assert pending is None and data_count==proof_count==MAX_BRANCHES
        assert digest.hexdigest()==self.seal['stream_sha256']and chain==self.seal['last_chain_sha256']

    def arrays(self,name):
        import numpy as np
        offset,size,expected,description=self.offsets[name]
        with self.path.open('rb')as stream:stream.seek(offset);payload=stream.read(size)
        assert sha(payload)==expected
        return record_codec().decode(payload,description)
