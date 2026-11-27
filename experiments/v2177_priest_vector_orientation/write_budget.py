"""Cumulative exact Python output admission for a <=1MiB ideal-math worker."""
from pathlib import Path
class Budget:
 def __init__(self,output,limit=1024**2):self.output=Path(output).resolve();self.limit=limit;self.charged=0;self.calls=0
 def reserve(self,path,size):
  p=Path(path).absolute();assert p.is_relative_to(self.output)and p.parent.resolve().is_relative_to(self.output)and not p.is_symlink(),'MATH_WRITER_ESCAPE'
  assert type(size)is int and size>=0
  assert self.charged+size<=self.limit,'MATH_CUMULATIVE_1MIB_WRITE_GRANT'
  self.charged+=size;self.calls+=1
