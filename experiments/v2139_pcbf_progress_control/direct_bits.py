"""Vectorized reversible uint64 XOR/byte planes, no floating point prediction."""
import hashlib,zlib
import numpy as np
MODES=('raw','xor','delta','delta2')
def encode(array):
 x=np.ascontiguousarray(array);assert x.dtype.str=='<f8'and x.ndim==2 and 2<=len(x)<=60001 and 1<=x.shape[1]<=32
 words=x.view(np.uint64);payload=[];modes=[]
 for col in range(x.shape[1]):
  u=words[:,col].copy();xor=u.copy();xor[1:]=u[1:]^u[:-1]
  delta=u.copy();delta[1:]=u[1:]-u[:-1]
  delta2=delta.copy();delta2[2:]=delta[2:]-delta[1:-1]
  def zigzag(a,start):
   b=a.copy();z=b[start:];b[start:]=(z<<np.uint64(1))^(np.uint64(0)-(z>>np.uint64(63)));return b
  choices=[]
  for mode,a in [('raw',u),('xor',xor),('delta',zigzag(delta,1)),('delta2',zigzag(delta2,2))]:
   raw=a.view(np.uint8).reshape(len(x),8).T.tobytes();choices.append((len(zlib.compress(raw,1)),mode,raw))
  _,mode,raw=min(choices,key=lambda t:(t[0],MODES.index(t[1])));modes.append(mode);payload.append(raw)
 return dict(dtype=x.dtype.str,shape=list(x.shape),modes=modes,raw_sha256=hashlib.sha256(x.tobytes()).hexdigest()),b''.join(payload)
def decode(header,payload):
 assert header['dtype']=='<f8';n,cols=header['shape'];assert type(n)is int and 2<=n<=60001 and type(cols)is int and 1<=cols<=32
 assert len(payload)==n*cols*8 and len(header['modes'])==cols
 words=np.empty((n,cols),dtype=np.uint64)
 for col,mode in enumerate(header['modes']):
  assert mode in MODES;data=np.frombuffer(payload[col*n*8:(col+1)*n*8],dtype=np.uint8).reshape(8,n).T.copy().view(np.uint64).reshape(n)
  if mode=='raw':words[:,col]=data
  elif mode=='xor':words[:,col]=np.bitwise_xor.accumulate(data)
  else:
   start=1 if mode=='delta'else 2;z=data[start:].copy();data[start:]=(z>>np.uint64(1))^(np.uint64(0)-(z&np.uint64(1)))
   if mode=='delta2':data[1:]=np.cumsum(data[1:],dtype=np.uint64)
   words[:,col]=np.cumsum(data,dtype=np.uint64)
 result=words.view(np.float64);assert hashlib.sha256(result.tobytes()).hexdigest()==header['raw_sha256'],'LOSSLESS_DECODE_SHA_MISMATCH';return result
