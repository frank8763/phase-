"""Canonical compact continuous-cell outer state; no simulator or actor access."""
import base64,functools,hashlib,zlib
import numpy as np
import cv2
from recursive_domain import RecursiveDomain,AXIS,GRID,canonical_distance
cv2.setNumThreads(1)
def encode(domain):
    bits=np.packbits(domain.possible.reshape(-1),bitorder='little').tobytes()
    assert domain.history_height.shape==domain.possible.shape and domain.history_height.dtype==np.dtype('<u4')
    height=domain.history_height.tobytes(order='C')
    return dict(schema='V789_PERSISTENT_NORM_01',time=domain.time,origin_xy=domain.origin.tolist(),grid_m=GRID,shape=list(domain.possible.shape),
                possible_bits_sha256=hashlib.sha256(bits).hexdigest(),possible_bits_zlib_b64=base64.b64encode(zlib.compress(bits,6)).decode(),
                conservative_axis_speed_bound=.12,conservative_norm_speed_bound=.08,complete_cells_retained=True,metadata=domain.last,history_schema='V789_ABSOLUTE_DISTANCE_HEIGHT_UM_01',history_height_sha256=hashlib.sha256(height).hexdigest(),history_height_zlib_b64=base64.b64encode(zlib.compress(height,6)).decode())

@functools.lru_cache(maxsize=4)
def _decode(payload,sha,time,origin,height_payload,height_sha):
    bits=zlib.decompress(base64.b64decode(payload,validate=True));assert hashlib.sha256(bits).hexdigest()==sha,'POSSIBLE_DOMAIN_HASH_CHANGED'
    n=len(AXIS);assert len(bits)==(n*n+7)//8
    possible=np.unpackbits(np.frombuffer(bits,dtype=np.uint8),bitorder='little')[:n*n].reshape(n,n).astype(bool)
    assert np.all(possible[[0,-1],:])and np.all(possible[:,[0,-1]])
    d=RecursiveDomain(origin);d.possible=possible;d.time=time;d.distance=canonical_distance(possible)
    height=zlib.decompress(base64.b64decode(height_payload,validate=True));assert len(height)==n*n*4 and hashlib.sha256(height).hexdigest()==height_sha,'HISTORY_HEIGHT_HASH_CHANGED'
    d.history_height=np.frombuffer(height,dtype='<u4').reshape(n,n).copy()
    return d
def decode(state):
    assert state['schema']=='V789_PERSISTENT_NORM_01' and state['grid_m']==GRID and state['shape']==[len(AXIS)]*2
    assert state['conservative_axis_speed_bound']==.12 and state['conservative_norm_speed_bound']==.08 and state['complete_cells_retained']is True
    assert state['history_schema']=='V789_ABSOLUTE_DISTANCE_HEIGHT_UM_01'
    return _decode(state['possible_bits_zlib_b64'],state['possible_bits_sha256'],float(state['time']),tuple(state['origin_xy']),state['history_height_zlib_b64'],state['history_height_sha256'])
