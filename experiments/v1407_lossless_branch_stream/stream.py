"""Exact float64 branch frames, XOR over prior frame, one shared gzip stream."""
import gzip
import copy
import hashlib
import json
from pathlib import Path
import struct
import zlib

MAGIC=b'PHASEB01'
STATE_VALUES=201*8
CTRL_VALUES=200*4
FRAME_BYTES=(STATE_VALUES+CTRL_VALUES)*8
HEADER=struct.Struct('<QI32s')


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
    return digest.hexdigest()


class BranchStore:
    def __init__(self,folder,*,input_sha256,np,atomic,maximum_branches=60000):
        self.folder=Path(folder);self.folder.mkdir(exist_ok=False);self.identity=input_sha256;self.np=np;self.atomic=atomic
        assert type(maximum_branches)is int and 0<maximum_branches<=60000
        self.maximum=maximum_branches;self.rows=[];self.closed=False;self.previous=np.zeros(STATE_VALUES+CTRL_VALUES,dtype='<u8')
        self.path=self.folder/'branches.xor.gz';self.output=self.path.open('xb');self.zip=zlib.compressobj(level=3,wbits=31)
        self.output.write(self.zip.compress(MAGIC));self.journal=(self.folder/'ROWS.jsonl').open('x',buffering=1)

    def append(self,proof,states,ctrl):
        np=self.np
        assert not self.closed and len(self.rows)<self.maximum and proof['input_sha256']==self.identity and proof['complete_native']==200
        assert states.shape==(201,8)and ctrl.shape==(200,4)and states.dtype==ctrl.dtype==np.dtype('float64')and np.isfinite(states).all()and np.isfinite(ctrl).all(), 'BRANCH_SHAPE_TYPE_OR_VALUE'
        assert type(proof['before_native'])is int and(not self.rows or proof['before_native']==self.rows[-1]['proof']['before_native']+1), 'BRANCH_ORIGIN_GAP'
        raw=states.astype('<f8',copy=False).tobytes(order='C')+ctrl.astype('<f8',copy=False).tobytes(order='C')
        assert len(raw)==FRAME_BYTES
        bits=np.frombuffer(raw,dtype='<u8');encoded=np.bitwise_xor(bits,self.previous).tobytes();digest=hashlib.sha256(raw).hexdigest();index=len(self.rows)
        self.output.write(self.zip.compress(HEADER.pack(index,FRAME_BYTES,bytes.fromhex(digest))+encoded));self.output.write(self.zip.flush(zlib.Z_SYNC_FLUSH));self.output.flush()
        row=dict(index=index,frame_bytes=FRAME_BYTES,raw_sha256=digest,proof=copy.deepcopy(proof))
        self.journal.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n');self.journal.flush()
        self.previous=bits.copy();self.rows.append(row)
        self.atomic(self.folder/'PROGRESS.json',dict(input_sha256=self.identity,closed=False,complete_branches=len(self.rows),complete_branch_native_saved=len(self.rows)*200,last_raw_sha256=digest,model_total_not_inferred=True))

    def close(self):
        if self.closed:return
        self.output.write(self.zip.flush(zlib.Z_FINISH));self.output.close();self.journal.close();self.closed=True
        self.atomic(self.folder/'INDEX.json',dict(schema='PHASE_BRANCH_XOR64_GZIP_V1',input_sha256=self.identity,closed=True,
            frame_file=self.path.name,frame_file_bytes=self.path.stat().st_size,frame_file_sha256=sha(self.path),branches=self.rows,
            complete_branch_native_saved=len(self.rows)*200,model_total_not_inferred=True))


class BranchReader:
    def __init__(self,folder,index,np):
        self.folder=Path(folder);self.index=index;self.np=np;self.cursor=0;self.previous=np.zeros(STATE_VALUES+CTRL_VALUES,dtype='<u8')
        assert index['closed']is True and index['schema']=='PHASE_BRANCH_XOR64_GZIP_V1'
        name=index['frame_file'];assert Path(name).name==name
        path=self.folder/name;assert not path.is_symlink()and path.stat().st_size==index['frame_file_bytes']and sha(path)==index['frame_file_sha256'], 'BRANCH_STREAM_CHANGED'
        self.stream=gzip.open(path,'rb');assert self.stream.read(len(MAGIC))==MAGIC, 'BRANCH_STREAM_SCHEMA'

    def read(self,row):
        assert row==self.index['branches'][self.cursor]and row['index']==self.cursor, 'BRANCH_READER_ORDER'
        header=self.stream.read(HEADER.size);assert len(header)==HEADER.size, 'BRANCH_STREAM_TRUNCATED_HEADER'
        index,size,digest=HEADER.unpack(header);assert index==self.cursor and size==row['frame_bytes']==FRAME_BYTES and digest.hex()==row['raw_sha256'], 'BRANCH_FRAME_IDENTITY'
        data=self.stream.read(size);assert len(data)==size, 'BRANCH_STREAM_TRUNCATED_FRAME'
        bits=self.np.bitwise_xor(self.np.frombuffer(data,dtype='<u8'),self.previous);raw=bits.tobytes()
        assert hashlib.sha256(raw).hexdigest()==row['raw_sha256'], 'BRANCH_RAW_SHA'
        values=self.np.frombuffer(raw,dtype='<f8');states=values[:STATE_VALUES].reshape(201,8);ctrl=values[STATE_VALUES:].reshape(200,4)
        assert self.np.isfinite(values).all()
        self.previous=bits.copy();self.cursor+=1
        return states,ctrl

    def finish(self):
        assert self.cursor==len(self.index['branches'])and self.stream.read(1)==b'', 'BRANCH_STREAM_TRAILING_OR_MISSING_FRAMES'
        self.stream.close()
