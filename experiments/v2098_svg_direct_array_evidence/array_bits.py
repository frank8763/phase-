"""Vectorized reversible uint64 XOR/byte planes, no floating point prediction."""
import hashlib,zlib
import numpy as np
MODES=('raw','xor')
def encode(array):
 x=np.ascontiguousarray(array);assert x.dtype.str=='<f8'and x.ndim==2 and 2<=len(x)<=60001 and 1<=x.shape[1]<=32
 words=x.view(np.uint64);payload=[];modes=[]
 for col in range(x.shape[1]):
  u=words[:,col].copy();delta=u.copy();delta[1:]=u[1:]^u[:-1]
  choices=[]
  for mode,a in [('raw',u),('xor',delta)]:
   raw=a.view(np.uint8).reshape(len(x),8).T.tobytes();choices.append((len(zlib.compress(raw,1)),mode,raw))
  _,mode,raw=min(choices,key=lambda t:(t[0],MODES.index(t[1])));modes.append(mode);payload.append(raw)
 return dict(dtype=x.dtype.str,shape=list(x.shape),modes=modes,raw_sha256=hashlib.sha256(x.tobytes()).hexdigest()),b''.join(payload)
def decode(header,payload):
 assert header['dtype']=='<f8';n,cols=header['shape'];assert type(n)is int and 2<=n<=60001 and type(cols)is int and 1<=cols<=32
 assert len(payload)==n*cols*8 and len(header['modes'])==cols
 words=np.empty((n,cols),dtype=np.uint64)
 for col,mode in enumerate(header['modes']):
  assert mode in MODES;data=np.frombuffer(payload[col*n*8:(col+1)*n*8],dtype=np.uint8).reshape(8,n).T.copy().view(np.uint64).reshape(n)
  words[:,col]=data if mode=='raw'else np.bitwise_xor.accumulate(data)
 result=words.view(np.float64);assert hashlib.sha256(result.tobytes()).hexdigest()==header['raw_sha256'],'LOSSLESS_DECODE_SHA_MISMATCH';return result
