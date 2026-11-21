"""One bounded, lossless complete200-branch stream; storage never admits models."""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import struct
R=Path(__file__).resolve().parents[2]
MAGIC=b'PHASEBR1';HEADER=struct.Struct('>8sII');MAX_META=2048;MAX_PAYLOAD=20480;MAX_RECORDS=1200;MAX_STREAM=28*1024**2
sha=lambda value:hashlib.sha256(value).hexdigest()

def normalized(value):
 if value is None or isinstance(value,(str,bool,int)):return value
 if isinstance(value,float):
  assert math.isfinite(value),'EVIDENCE_NONFINITE_JSON';return value
 if isinstance(value,(list,tuple)):return [normalized(x)for x in value]
 if isinstance(value,dict):
  assert all(isinstance(k,str)for k in value);return {k:normalized(v)for k,v in value.items()}
 import numpy as np
 if isinstance(value,np.generic):return normalized(value.item())
 if isinstance(value,np.ndarray):return normalized(value.tolist())
 raise TypeError('EVIDENCE_UNDECLARED_JSON_TYPE:'+str(type(value)))

def encoded(value):return json.dumps(normalized(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def metered(output,writer,boundary):
 output=Path(output).resolve();assert output.is_relative_to(R/'runs')and output==writer.output==boundary.output
 assert Path(writer.reserve.__func__.__code__.co_filename).resolve()==R/'experiments/v1436_pathlib_control_rename/writer_budget.py'
 assert Path(type(boundary).__enter__.__code__.co_filename).resolve()==R/'experiments/v1436_pathlib_control_rename/bounded_io.py'
 assert boundary.saved is not None and boundary.reserve.__self__ is writer and not boundary.control_paths and not boundary.control_renames
 assert writer.role=='PLANNER'and writer.maximum<=32*1024**2
 return output

def write_atomic(path,data,writer):
 temporary=path.with_suffix(path.suffix+'.tmp');writer.reserve(temporary,len(data)+4096)
 with temporary.open('xb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
 temporary.replace(path)

def binding_check(value):
 assert value['geometry_kind']=='FULL_PERIOD_DISK'and isinstance(value['origin_native'],int)
 for key in ['input_sha256','proposal_sha256','causal_snapshot_sha256','tested_source_manifest_sha256']:
  assert isinstance(value[key],str)and len(value[key])==64 and all(x in '0123456789abcdef'for x in value[key])
 return sha(encoded(value))

def proof_check(proof,binding,index):
 assert proof['before_native']==binding['origin_native']+index and proof['complete_native']==200
 assert proof['current_input_sha256']==binding['input_sha256']and proof['proposal_sha256']==binding['proposal_sha256']and proof['causal_snapshot_sha256']==binding['causal_snapshot_sha256']and proof['geometry_kind']==binding['geometry_kind']
 assert isinstance(proof['rest'],bool)and isinstance(proof['body_caps'],bool)and math.isfinite(proof['causal_tube_lower_m'])
 # Unsafe/refused proof values are retained before producer gating.

def arrays_check(states,ctrl):
 import numpy as np
 s=np.asarray(states);u=np.asarray(ctrl)
 assert s.shape==(201,8)and u.shape==(200,4)and s.dtype==u.dtype==np.dtype('float64')and np.isfinite(s).all()and np.isfinite(u).all()
 return s,u

class BranchStore:
 def __init__(self,output,*,writer,boundary,binding):
  self.output=metered(output,writer,boundary);self.writer=writer;self.binding=normalized(binding);self.binding_sha=binding_check(self.binding);self.path=self.output/'BRANCHES.bin';self.count=0;self.bytes=0;self.chain='0'*64;self.digest=hashlib.sha256();self.closed=False
  writer.reserve(self.path,4096);self.stream=self.path.open('xb')
 def save(self,proof,states,ctrl):
  import numpy as np
  assert not self.closed and self.count<MAX_RECORDS
  proof=normalized(proof);proof_check(proof,self.binding,self.count);states,ctrl=arrays_check(states,ctrl)
  buffer=io.BytesIO();np.savez_compressed(buffer,states=states,ctrl=ctrl);payload=buffer.getvalue();assert len(payload)<=MAX_PAYLOAD
  meta=encoded(dict(index=self.count,binding_sha256=self.binding_sha,previous_chain_sha256=self.chain,payload_sha256=sha(payload),proof=proof));assert len(meta)<=MAX_META
  block=HEADER.pack(MAGIC,len(meta),len(payload))+meta+payload;assert self.bytes+len(block)<=MAX_STREAM
  self.writer.reserve(self.path,len(block));written=self.stream.write(block);assert written==len(block);self.stream.flush();os.fsync(self.stream.fileno())
  self.digest.update(block);self.chain=sha(self.chain.encode()+meta+payload);self.bytes+=len(block);self.count+=1
  return dict(index=self.count-1,stream_bytes=self.bytes,chain_sha256=self.chain,complete_native=200,stored_before_safety_gate=True)
 def abort(self,*,first_error,generator_counts):
  errors=[]
  if not self.closed:
   try:self.stream.flush();os.fsync(self.stream.fileno())
   except BaseException as error:errors.append('flush:'+repr(error))
   try:self.stream.close()
   except BaseException as error:errors.append('close:'+repr(error))
   self.closed=True
  actual_bytes=None;digest=None
  try:actual_bytes=self.path.stat().st_size;digest=sha(self.path.read_bytes())
  except BaseException as error:errors.append('readback:'+repr(error))
  receipt=dict(first_error=first_error,generator_counts=generator_counts,acknowledged_complete_records=self.count,acknowledged_record_bytes=self.bytes,actual_saved_bytes=actual_bytes,actual_saved_sha256=digest,unacknowledged_tail_unknown=actual_bytes is None or actual_bytes!=self.bytes,secondary_errors=errors,complete_seal_absent=not(self.output/'BRANCH_SEAL.json').exists(),numeric_audit_admitted=False)
  try:write_atomic(self.output/'BRANCH_ABORT.json',encoded(receipt),self.writer)
  except BaseException as error:receipt['abort_receipt_save_error']=repr(error)
  return receipt
 def close(self,*,generation_result_sha256):
  assert not self.closed and len(generation_result_sha256)==64;self.stream.flush();os.fsync(self.stream.fileno());self.stream.close();self.closed=True
  actual=hashlib.sha256()
  with self.path.open('rb')as stream:
   for block in iter(lambda:stream.read(1024**2),b''):actual.update(block)
  assert actual.hexdigest()==self.digest.hexdigest()and self.path.stat().st_size==self.bytes
  seal=dict(schema=1,binding=self.binding,binding_sha256=self.binding_sha,records=self.count,stream_bytes=self.bytes,stream_sha256=actual.hexdigest(),last_chain_sha256=self.chain,generation_result_sha256=generation_result_sha256,storage_complete=True,scientific_pass_not_inferred=True)
  write_atomic(self.output/'BRANCH_SEAL.json',encoded(seal),self.writer);return seal

class BranchReader:
 def __init__(self,output,*,binding,generation_result_sha256):
  self.output=Path(output);self.path=self.output/'BRANCHES.bin';self.binding=normalized(binding);binding_sha=binding_check(binding);seal=json.loads((self.output/'BRANCH_SEAL.json').read_text())
  assert seal['binding']==self.binding and seal['binding_sha256']==binding_sha and seal['generation_result_sha256']==generation_result_sha256 and seal['storage_complete']is True
  assert self.path.stat().st_size==seal['stream_bytes']<=MAX_STREAM and 0<=seal['records']<=MAX_RECORDS
  self.rows=[];chain='0'*64;whole=hashlib.sha256()
  with self.path.open('rb')as stream:
   for index in range(seal['records']):
    offset=stream.tell();raw=stream.read(HEADER.size);assert len(raw)==HEADER.size;magic,mlen,plen=HEADER.unpack(raw);assert magic==MAGIC and mlen<=MAX_META and plen<=MAX_PAYLOAD
    meta=stream.read(mlen);payload=stream.read(plen);assert len(meta)==mlen and len(payload)==plen;value=json.loads(meta);assert value['index']==index and value['binding_sha256']==binding_sha and value['previous_chain_sha256']==chain and value['payload_sha256']==sha(payload)
    proof_check(value['proof'],self.binding,index);chain=sha(chain.encode()+meta+payload);whole.update(raw+meta+payload);self.rows.append(dict(offset=offset,meta_bytes=mlen,payload_bytes=plen,proof=value['proof'],payload_sha256=sha(payload)))
   assert not stream.read(1)
  assert chain==seal['last_chain_sha256']and whole.hexdigest()==seal['stream_sha256'];self.seal=seal
 def read(self,index):
  import numpy as np
  row=self.rows[index]
  with self.path.open('rb')as stream:stream.seek(row['offset']+HEADER.size+row['meta_bytes']);payload=stream.read(row['payload_bytes'])
  assert sha(payload)==row['payload_sha256']
  with np.load(io.BytesIO(payload),allow_pickle=False)as data:
   assert set(data.files)=={'states','ctrl'};s=data['states'].copy();u=data['ctrl'].copy()
  arrays_check(s,u);return row['proof'],s,u
