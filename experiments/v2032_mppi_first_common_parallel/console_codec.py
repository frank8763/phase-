"""Streaming lossless timestamp dictionary; immutable 4MiB disk cap."""
import hashlib,json,re,zlib
CAP=4*1024**2-64*1024
TF_SUFFIX=b'] [tf2_buffer]: Do not call canTransform or lookupTransform with a timeout unless you are using another thread for populating data. Without a dedicated thread it will always timeout.  If you have a separate thread servicing tf messages, call setUsingDedicatedThread(true) on your Buffer instance.\n'
PATTERN=re.compile(rb'\[ERROR\] \[([1-9][0-9]{0,10})\.([0-9]{9})'+re.escape(TF_SUFFIX))
def varint(n):
 assert type(n)is int and 0<=n<2**65
 b=bytearray()
 while n>=128:b.append((n&127)|128);n>>=7
 b.append(n);return bytes(b)
class Writer:
 def __init__(self,path,*,cap=CAP):
  self.path=path;self.cap=cap;self.file=path.open('xb');self.compressor=zlib.compressobj(3);self.pending=bytearray();self.encoded=bytearray(b'RPPLOG01');self.packed=0;self.lines=0;self.raw_bytes=0;self.raw_sha=hashlib.sha256();self.file_sha=hashlib.sha256();self.last=0;self.closed=False;self.poisoned=False
 def append(self,line):
  assert not self.closed and not self.poisoned and isinstance(line,bytes)and len(line)<=1024**2
  assert self.raw_bytes+len(line)<=1024**3,'RPP_CONSOLE_LOGICAL_1GIB_STOP'
  m=PATTERN.fullmatch(line)
  if m:
   ns=int(m[1])*10**9+int(m[2]);d=ns-self.last;self.last=ns;record=b'T'+varint(2*d if d>=0 else-2*d-1)
  else:record=b'R'+varint(len(line))+line
  self.raw_sha.update(line);self.raw_bytes+=len(line);self.lines+=1;self.encoded.extend(record)
  if len(self.encoded)>=65536:self.flush()
 def flush(self):
  self.pending.extend(self.compressor.compress(bytes(self.encoded)));self.encoded.clear();self._write(False)
 def _write(self,final):
  while len(self.pending)>=65536 or(final and self.pending):
   size=min(65536,len(self.pending));assert self.packed+size<=self.cap,'RPP_COMPRESSED_CONSOLE_4MIB_STOP'
   block=bytes(self.pending[:size]);self.file.write(block);self.file.flush();self.file_sha.update(block);self.packed+=size;del self.pending[:size]
 def finish(self):
  if self.closed:return self.receipt
  try:
   self.flush();self.pending.extend(self.compressor.flush());self._write(True);self.file.close();self.closed=True;self.receipt=dict(schema='RPP_LOSSLESS_CONSOLE_V1',path=self.path.name,packed_bytes=self.packed,packed_sha256=self.file_sha.hexdigest(),raw_bytes=self.raw_bytes,raw_SHA256=self.raw_sha.hexdigest(),line_count=self.lines,cap_bytes=self.cap,logical_cap_bytes=1024**3,all_nonreply_bytes_preserved=True,replies_saved_individually=True);return self.receipt
  except BaseException:self.poisoned=True;self.file.close();raise

def decoded_chunks(path,*,max_raw=1024**3):
 """Bounded streaming decoder; malformed records fail closed."""
 decoder=zlib.decompressobj();buf=bytearray();last=0;header=False;total=0
 def extract(final=False):
  nonlocal header,last,total
  if not header:
   if len(buf)<8:
    assert not final,'RPP_LOG_TRUNCATED_HEADER';return []
   assert bytes(buf[:8])==b'RPPLOG01';del buf[:8];header=True
  output=[]
  while buf:
   kind=buf[0];assert kind in [ord('R'),ord('T')],'RPP_LOG_UNKNOWN_RECORD';n=0;end=None
   for i in range(1,min(len(buf),11)):
    b=buf[i];n|=(b&127)<<(7*(i-1))
    if b<128:end=i+1;break
   if end is None:assert len(buf)<11 and not final,'RPP_LOG_BAD_VARINT';break
   if kind==ord('R'):
    assert n<=1024**2,'RPP_LOG_RECORD_BOUND'
    if len(buf)<end+n:assert not final,'RPP_LOG_TRUNCATED_RECORD';break
    value=bytes(buf[end:end+n]);del buf[:end+n]
   else:
    d=n//2 if n%2==0 else-(n//2)-1;last+=d;assert 0<=last<2**64;sec,ns=divmod(last,10**9);value=b'[ERROR] ['+str(sec).encode()+b'.'+f'{ns:09d}'.encode()+TF_SUFFIX;del buf[:end]
   total+=len(value);assert total<=max_raw,'RPP_LOG_DECODE_BOUND';output.append(value)
  if final:assert header and not buf
  return output
 with path.open('rb')as f:
  for packed in iter(lambda:f.read(65536),b''):
   while packed:
    data=decoder.decompress(packed,65536);packed=decoder.unconsumed_tail;buf.extend(data)
    for row in extract():yield row
  assert decoder.eof and not decoder.unused_data,'RPP_LOG_ZLIB_TRUNCATED_OR_TRAILING'
  for row in extract(True):yield row
