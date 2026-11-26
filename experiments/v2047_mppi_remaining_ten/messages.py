"""Bounded lossless transport; never changes numerical data or accepts stale input."""
import base64,hashlib,json,zlib
def encode(value):
 raw=json.dumps(value,separators=(',',':'),allow_nan=False).encode();assert len(raw)<=1024**2
 return json.dumps(dict(schema='RPP_FILE_FRAME_V1',sha256=hashlib.sha256(raw).hexdigest(),payload=base64.b64encode(zlib.compress(raw,3)).decode()),separators=(',',':'))+'\n'
def decode(line):
 assert len(line)<=1024**2;frame=json.loads(line);assert set(frame)=={'schema','sha256','payload'}and frame['schema']=='RPP_FILE_FRAME_V1'
 packed=base64.b64decode(frame['payload'],validate=True);decoder=zlib.decompressobj();raw=decoder.decompress(packed,1024**2+1);assert len(raw)<=1024**2 and not decoder.unconsumed_tail and decoder.eof and not decoder.unused_data,'RPP_FRAME_BOUND';assert hashlib.sha256(raw).hexdigest()==frame['sha256'],'RPP_FRAME_SHA';return json.loads(raw)
