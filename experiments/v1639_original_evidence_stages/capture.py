"""Original capture contents; bounded UTF8 batching before gzip only."""
from contextlib import contextmanager
import gzip
from pathlib import Path
from context import R,load
base=load('v1639_original_capture_holds',R/'experiments/v1439_actual_ros_startup_close/capture_budget.py')

class TextChunks:
 def __init__(self,stream):self.stream=stream;self.pending=bytearray();self.failed=False
 def write(self,text):
  assert isinstance(text,str)and not self.failed
  data=text.encode('utf-8')
  for start in range(0,len(data),65536):
   self.pending.extend(data[start:start+65536])
   if len(self.pending)>=65536:self.flush()
  return len(text)
 def flush(self):
  assert not self.failed,'FAILED_BUFFER_NO_RETRY'
  if self.pending:
   try:self.stream.write(bytes(self.pending))
   except BaseException:self.failed=True;raise
   self.pending.clear()
 def fileno(self):raise OSError('WRITABLE_RAW_DESCRIPTOR_REMAINS_FORBIDDEN')

@contextmanager
def exact_compressed_paths(output,secondary):
 targets={Path(output).resolve()/n for n in ['CONTACTS.json.gz','SENSORS.json.gz']};opened=set();original=gzip.open
 @contextmanager
 def adapted(filename,mode='rb',*args,**kwargs):
  path=Path(filename).absolute();assert path in targets and mode=='xt'and not args and not kwargs
  assert path not in opened,'CAPTURE_TARGET_NO_RETRY';opened.add(path)
  first=None
  with path.open('xb')as raw:
   compressed=gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0);text=TextChunks(compressed)
   try:yield text
   except BaseException as error:first=error
   for name,action in [('UTF8_BUFFER_FLUSH',text.flush),('GZIP_CLOSE',compressed.close)]:
    try:action()
    except BaseException as error:
     if first is None:first=error
     else:secondary.append(dict(stage=name,error=repr(error)))
   if first is not None:raise first
 gzip.open=adapted
 try:yield
 finally:gzip.open=original

class CaptureBudget(base.CaptureBudget):
 def __init__(self,quota):super().__init__(quota);self.finish_attempted=False;self.secondary_close_errors=[]
 def finish(self,vehicle):
  assert not self.finish_attempted,'FAILED_PREFIX_SAVE_MUST_NOT_BE_RETRIED';self.finish_attempted=True
  with exact_compressed_paths(vehicle.out,self.secondary_close_errors):return super().finish(vehicle)
