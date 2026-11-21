"""Exact word-XOR temporal differencing and byteplane shuffle; no model calls.

Original float64/int64 value bytes are restored before any consumer sees arrays.
No quantization, dropped rows, control replay or numerical state reset.
"""
import hashlib
import io
import lzma

NAME='XOR_ROW_BYTEPLANES_LZMA_V1'
MAX_RAW=13600*384+216+16384
MAX_PAYLOAD=8*1024**2
KEYS={'states','ctrl','memory','modes','gear','encoders','parked','native','sim_time','raw_rows','requested_body','applied_body','gear_proof'}
WIDTHS=dict(states=8,ctrl=4,memory=5,modes=3,gear=3,encoders=4,parked=2,raw_rows=3,requested_body=2,applied_body=2,gear_proof=10)
INTS={'modes','gear','native'}
ACTION={'ctrl','raw_rows','requested_body','applied_body','gear_proof'}
sha=lambda data:hashlib.sha256(data).hexdigest()


def dimensions(native):
    assert type(native)is int and 0<=native<=13600
    return {key:((native+1,)if key in {'native','sim_time'}else(native if key in ACTION else native+1,WIDTHS[key]))for key in KEYS}


def encode(arrays):
    import numpy as np
    assert set(arrays)==KEYS
    native=len(arrays['ctrl']);shapes=dimensions(native)
    planes={};description={}
    for key in sorted(KEYS):
        value=arrays[key];dtype=np.dtype('int64'if key in INTS else'float64')
        assert value.dtype==dtype and value.shape==shapes[key]
        width=1 if value.ndim==1 else value.shape[1]
        words=np.ascontiguousarray(value).view(np.uint64).reshape(len(value),width)
        delta=words.copy()
        if len(value)>1:delta[1:]=np.bitwise_xor(words[1:],words[:-1])
        planes[key]=delta.reshape(-1).view(np.uint8).reshape(-1,8).T.copy()
        description[key]=dict(shape=list(value.shape),dtype=str(dtype),byte_sha256=sha(value.tobytes(order='C')))
    buffer=io.BytesIO();np.savez(buffer,**planes);raw=buffer.getvalue()
    assert len(raw)<=MAX_RAW,'RAW_NPZ_SCHEMA_HEADER_BOUND'
    payload=lzma.compress(raw,preset=3)
    assert len(payload)<=MAX_PAYLOAD,'COMPLETE_BRANCH_PAYLOAD_EXCEEDS_EMERGENCY_SLOT'
    restored=decode(payload,description)
    assert all(restored[k].dtype==v.dtype and restored[k].shape==v.shape and restored[k].tobytes()==v.tobytes(order='C')for k,v in arrays.items())
    return payload,description,native


def decode(payload,description):
    import numpy as np
    assert len(payload)<=MAX_PAYLOAD and set(description)==KEYS
    n=description['ctrl']['shape'][0];shapes=dimensions(n)
    result={}
    decompressor=lzma.LZMADecompressor(memlimit=64*1024**2)
    raw=decompressor.decompress(payload,max_length=MAX_RAW+1)
    assert decompressor.eof and not decompressor.unused_data and len(raw)<=MAX_RAW,'LZMA_RAW_LENGTH_OR_TERMINATION_BOUND'
    with np.load(io.BytesIO(raw),allow_pickle=False)as stored:
        assert set(stored.files)==KEYS
        for key in sorted(KEYS):
            desc=description[key];dtype=np.dtype('int64'if key in INTS else'float64');shape=shapes[key]
            assert desc['shape']==list(shape)and desc['dtype']==str(dtype)
            rows=shape[0];width=1 if len(shape)==1 else shape[1]
            plane=stored[key]
            assert plane.dtype==np.uint8 and plane.shape==(8,rows*width)
            words=plane.T.copy().reshape(-1).view(np.uint64).reshape(rows,width)
            if rows:np.bitwise_xor.accumulate(words,axis=0,out=words)
            value=words.view(dtype).reshape(shape).copy()
            assert sha(value.tobytes())==desc['byte_sha256'],'RESTORED_ARRAY_BYTE_SHA_CHANGED'
            result[key]=value
    return result
