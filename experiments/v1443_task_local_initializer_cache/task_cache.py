"""Relocate library scratch files inside one already admitted task directory."""
import os
from pathlib import Path
import tempfile

class TaskLocalCaches:
 def __init__(self,output):
  self.output=Path(output).resolve();self.previous=None
 def __enter__(self):
  assert self.previous is None and self.output.is_dir()
  root=Path(__file__).resolve().parents[2]/'runs'
  assert self.output.is_relative_to(root)and not self.output.is_symlink()
  tmp=self.output/'tmp';cache=self.output/'cache'
  mapping=dict(TMPDIR=tmp,TEMP=tmp,TMP=tmp,XDG_CACHE_HOME=cache,TORCHINDUCTOR_CACHE_DIR=cache/'torch_inductor',TORCH_EXTENSIONS_DIR=cache/'torch_extensions',TRITON_CACHE_DIR=cache/'triton',MPLCONFIGDIR=cache/'matplotlib')
  for path in set(mapping.values()):
   assert path.is_relative_to(self.output)and not path.is_symlink();path.mkdir(parents=True,exist_ok=True)
  self.previous={key:os.environ.get(key)for key in mapping};self.previous_tempdir=tempfile.tempdir
  os.environ.update({key:str(value)for key,value in mapping.items()});tempfile.tempdir=str(tmp)
  return self
 def __exit__(self,*_):
  tempfile.tempdir=self.previous_tempdir
  for key,value in self.previous.items():
   if value is None:os.environ.pop(key,None)
   else:os.environ[key]=value
  self.previous=None

