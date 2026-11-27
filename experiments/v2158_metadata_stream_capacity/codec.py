"""Raw-deflate record stream; dictionary reset128, exact raw SHA per record."""
import hashlib,json,zlib
INTERVAL=128;MAX_RAW=4*1024**2
def h(b):return hashlib.sha256(b).hexdigest()
class Encoder:
 def __init__(self):self.compressor=zlib.compressobj(1,zlib.DEFLATED,-15);self.data=bytearray();self.rows=[];self.names=set();self.chain='0'*64
 def append(self,name,raw):
  assert name not in self.names and isinstance(raw,bytes)and 0<len(raw)<=MAX_RAW
  self.names.add(name);k=len(self.rows);frame=self.compressor.compress(raw)+self.compressor.flush(zlib.Z_FULL_FLUSH if (k+1)%INTERVAL==0 else zlib.Z_SYNC_FLUSH)
  row=dict(name=name,sequence=k,offset=len(self.data),bytes=len(frame),raw_bytes=len(raw),raw_sha256=h(raw),compressed_sha256=h(frame),previous=self.chain)
  row['chain']=h(json.dumps(row,sort_keys=True,separators=(',',':')).encode());self.chain=row['chain'];self.rows.append(row);self.data.extend(frame)
def record(data,rows,k):
 assert type(k)is int and 0<=k<len(rows);start=k//INTERVAL*INTERVAL;decoder=zlib.decompressobj(-15)
 for i in range(start,k+1):
  r=rows[i];assert r['sequence']==i and (i==0 or r['offset']==rows[i-1]['offset']+rows[i-1]['bytes'])
  frame=bytes(data[r['offset']:r['offset']+r['bytes']]);assert h(frame)==r['compressed_sha256']
  raw=decoder.decompress(frame,MAX_RAW+1);assert not decoder.unconsumed_tail and not decoder.unused_data and len(raw)==r['raw_bytes']and h(raw)==r['raw_sha256']
 return raw
def verify(data,rows):
 assert rows and rows[-1]['offset']+rows[-1]['bytes']==len(data)
 chain='0'*64;seen=set();decoder=None
 for i,r in enumerate(rows):
  assert r['sequence']==i and r['name']not in seen and r['previous']==chain
  clean={k:v for k,v in r.items()if k!='chain'};assert r['chain']==h(json.dumps(clean,sort_keys=True,separators=(',',':')).encode());chain=r['chain'];seen.add(r['name'])
  if i%INTERVAL==0:decoder=zlib.decompressobj(-15)
  frame=bytes(data[r['offset']:r['offset']+r['bytes']]);assert h(frame)==r['compressed_sha256'];raw=decoder.decompress(frame,MAX_RAW+1)
  assert len(raw)==r['raw_bytes']and h(raw)==r['raw_sha256']and not decoder.unconsumed_tail and not decoder.unused_data
 return len(rows)
