"""Once-only raw FFI-return preservation before enclosing stream failure save.

This is distinct from reconstructed13array receipts: acknowledged model work
can exceed reconstructable or durable rows. No malformed result becomes PASS.
"""
import hashlib
import io

MAX_RAW_RETURN=512*1024


def preserve(carrier,*,save_bytes,save_proof,accounting):
    pending=carrier.batch_return
    if pending is None:return None
    assert not pending.get('save_attempted',False),'CPP_RAW_RETURN_SAVE_NOT_RETRIED'
    pending['save_attempted']=True
    proof={k:v for k,v in pending.items()if k!='returned'}
    proof.update(complete_certificate=False,model_counts=accounting,
        arrays_durable=False,first_error=None,secondary_errors=[],physical_native=0,
        reconstructed_rows_are_not_total_model_work=True)
    try:
        import numpy as np
        returned=pending['returned']
        assert isinstance(returned,tuple)and len(returned)==3,'CPP_RAW_RETURN_TUPLE'
        assert all(isinstance(v,np.ndarray)and not v.dtype.hasobject for v in returned)
        assert sum(v.nbytes for v in returned)+16384<=MAX_RAW_RETURN,'CPP_RAW_RETURN_BYTE_BOUND'
        buf=io.BytesIO();np.savez(buf,states=returned[0],ctrl=returned[1],memory=returned[2])
        payload=buf.getvalue();assert len(payload)<=MAX_RAW_RETURN
        proof['arrays']={name:dict(shape=list(v.shape),dtype=str(v.dtype),byte_sha256=hashlib.sha256(v.tobytes()).hexdigest())
            for name,v in zip(('states','ctrl','memory'),returned)}
        save_bytes('BATCH_RETURN_RAW.npz',payload)
        proof.update(arrays_durable=True,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
    except BaseException as error:
        proof['first_error']=repr(error)
    try:save_proof('BATCH_RETURN_RAW.json',proof)
    except BaseException as error:proof['secondary_errors'].append(repr(error))
    # Preserve the enclosing reconstruction/FFI first exception. The caller
    # reports this save gap as secondary; it must not replace the first error.
    return proof
