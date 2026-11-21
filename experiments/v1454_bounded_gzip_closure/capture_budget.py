"""Keep the original finish data, charge compressed bytes without any raw fd."""
from contextlib import contextmanager
import gzip
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1454_original_capture_budget',R/'experiments/v1439_actual_ros_startup_close/capture_budget.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)

class CompressedText:
 def __init__(self,compressed):self.compressed=compressed
 def write(self,text):
  assert isinstance(text,str),'GZIP_TEXT_ONLY'
  self.compressed.write(text.encode('utf-8'));return len(text)
 def flush(self):self.compressed.flush()
 def fileno(self):raise OSError('WRITABLE_RAW_DESCRIPTOR_REMAINS_FORBIDDEN')

@contextmanager
def original_finish_compressed_paths(output):
 """Only the two exact original gzip.open('xt') targets are adapted."""
 output=Path(output).resolve();targets={output/'CONTACTS.json.gz',output/'SENSORS.json.gz'};original=gzip.open;opened=set()
 @contextmanager
 def adapted(filename,mode='rb',*args,**kwargs):
  path=Path(filename).absolute();assert path in targets and mode=='xt'and not args and not kwargs,'UNDECLARED_COMPRESSED_FINISH_WRITE'
  assert path not in opened,'DUPLICATE_COMPRESSED_FINISH_TARGET';opened.add(path)
  # Path.open remains the qualified OutputBoundary WriteProxy. Every emitted
  # gzip header, compressed block and trailer is charged there. No fileno is
  # requested; binary-only compression avoids TextIOWrapper's descriptor probe.
  with path.open('xb')as raw:
   with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0)as compressed:yield CompressedText(compressed)
 gzip.open=adapted
 try:yield opened
 finally:gzip.open=original

class CaptureBudget(base.CaptureBudget):
 def __init__(self,quota):super().__init__(quota);self.finish_attempted=False
 def finish(self,vehicle):
  assert not self.finish_attempted,'FAILED_PREFIX_SAVE_MUST_NOT_BE_RETRIED'
  self.finish_attempted=True
  with original_finish_compressed_paths(vehicle.out):return super().finish(vehicle)
