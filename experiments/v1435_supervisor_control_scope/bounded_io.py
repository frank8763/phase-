"""Scoped write admission for Python I/O and finite subprocess log pipes.

Read operations and physical/model calculations are delegated unchanged. Raw
writable descriptors are not exposed to unknown native writers; supported
MuJoCo save APIs have explicit byte admission supplied by the actual caller.
"""
import builtins
from contextlib import contextmanager
import io
import os
from pathlib import Path
import subprocess
import time

class WriteProxy:
 def __init__(self,stream,path,boundary):self.stream=stream;self.path=path;self.boundary=boundary
 def write(self,value):
  size=len(value.encode(self.stream.encoding or 'utf-8'))if isinstance(value,str)else len(value)
  self.boundary.charge(self.path,size);return self.stream.write(value)
 def writelines(self,values):
  for value in values:self.write(value)
 def truncate(self,size=None):
  target=self.stream.tell()if size is None else size
  self.boundary.charge(self.path,max(0,target-os.fstat(self.stream.fileno()).st_size));return self.stream.truncate(size)
 def fileno(self):raise OSError('WRITABLE_RAW_DESCRIPTOR_REQUIRES_BOUNDED_PIPE_OR_EXPLICIT_NATIVE_SAVE')
 def __enter__(self):return self
 def __exit__(self,*args):return self.stream.__exit__(*args)
 def __iter__(self):return iter(self.stream)
 def __getattr__(self,name):return getattr(self.stream,name)

class OutputBoundary:
 def __init__(self,output,reserve,*,control_paths=(),control_renames=()):
  self.control_paths=frozenset(Path(p).absolute()for p in control_paths);self.control_renames=frozenset((Path(a).absolute(),Path(b).absolute())for a,b in control_renames)
  self.output=Path(output).resolve();self.reserve=reserve;self.busy=False;self.saved=None
 def path(self,value):
  if isinstance(value,int):return None
  try:p=Path(value).absolute()
  except TypeError:return None
  assert not p.is_symlink(),'BOUNDED_OUTPUT_SYMLINK'
  assert p in self.control_paths or(p.is_relative_to(self.output)and p.parent.resolve().is_relative_to(self.output)),'BOUNDED_OUTPUT_PATH_ESCAPE'
  return p
 def charge(self,path,size):
  if self.busy:return
  self.busy=True
  try:self.reserve(Path(path),int(size))
  finally:self.busy=False
 def __enter__(self):
  assert self.saved is None
  original_replace=os.replace;original_rename=os.rename;original_path_open=Path.open;original_open=builtins.open;original_io=io.open;original_os_open=os.open;original_write=os.write;original_popen=subprocess.Popen
  self.saved=(original_open,original_io,original_os_open,original_write,original_popen,original_path_open,original_replace,original_rename)
  boundary=self
  def opener(original,file,mode='r',*args,**kwargs):
   writable=(isinstance(mode,str)and any(x in mode for x in 'wax+'))or(isinstance(mode,int)and mode&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if boundary.busy or not writable:return original(file,mode,*args,**kwargs)
   path=boundary.path(file);assert path is not None,'UNBOUND_WRITABLE_DESCRIPTOR'
   boundary.charge(path,8192)
   boundary.busy=True
   try:stream=original(file,mode,*args,**kwargs)
   finally:boundary.busy=False
   return WriteProxy(stream,path,boundary)
  def raw_open(path,flags,*args,**kwargs):
   if not boundary.busy and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):boundary.charge(boundary.path(path),8192)
   return original_os_open(path,flags,*args,**kwargs)
  def raw_write(fd,value):
   if not boundary.busy and fd not in {1,2}:
    target=Path(os.readlink('/proc/self/fd/'+str(fd)));boundary.charge(boundary.path(target),len(value))
   return original_write(fd,value)
  class LogPopen(original_popen):
   def __init__(self,*args,**kwargs):
    target=kwargs.get('stdout');self.bounded_target=target if isinstance(target,WriteProxy)else None
    if self.bounded_target is not None:kwargs['stdout']=subprocess.PIPE
    super().__init__(*args,**kwargs)
    if self.bounded_target is not None:os.set_blocking(self.stdout.fileno(),False)
   def drain(self):
    if self.bounded_target is None or self.stdout is None:return
    for _ in range(64):
     try:block=os.read(self.stdout.fileno(),16384)
     except BlockingIOError:break
     if not block:break
     target=self.bounded_target
     target.write(block.decode('utf-8',errors='replace')if isinstance(target.stream,io.TextIOBase)else block);target.flush()
   def poll(self):
    self.drain();return super().poll()
   def wait(self,timeout=None):
    if self.bounded_target is None:return super().wait(timeout=timeout)
    end=None if timeout is None else time.monotonic()+timeout
    while True:
     code=self.poll()
     if code is not None:self.drain();return code
     if end is not None and time.monotonic()>=end:raise subprocess.TimeoutExpired(self.args,timeout)
     time.sleep(.005)
  Path.open=lambda file,mode='r',*a,**kw:opener(original_path_open,file,mode,*a,**kw)
  def rename(original,src,dst,*args,**kwargs):
   if not boundary.busy:
    assert not args and not any(value is not None for value in kwargs.values()),'UNKNOWN_OUTPUT_RENAME_DIRFD'
    a=Path(src).absolute();b=Path(dst).absolute()
    inside=a.is_relative_to(boundary.output)and b.is_relative_to(boundary.output)
    assert inside or(a,b)in boundary.control_renames,'BOUNDED_OUTPUT_RENAME_ESCAPE'
    boundary.path(a);boundary.path(b)
   return original(src,dst,*args,**kwargs)
  os.replace=lambda a,b,*args,**kwargs:rename(original_replace,a,b,*args,**kwargs)
  os.rename=lambda a,b,*args,**kwargs:rename(original_rename,a,b,*args,**kwargs)
  builtins.open=lambda file,mode='r',*a,**kw:opener(original_open,file,mode,*a,**kw)
  io.open=lambda file,mode='r',*a,**kw:opener(original_io,file,mode,*a,**kw)
  os.open=raw_open;os.write=raw_write;subprocess.Popen=LogPopen
  return self
 def __exit__(self,*args):
  builtins.open,io.open,os.open,os.write,subprocess.Popen,Path.open,os.replace,os.rename=self.saved;self.saved=None

@contextmanager
def native_model_saves(mj,reserve):
 original=mj.mj_saveModel
 def save_model(model,path,buffer=None):
  assert path is not None and buffer is None,'UNREGISTERED_NATIVE_MODEL_SAVE_TARGET'
  size=int(mj.mj_sizeModel(model));reserve(Path(path),size+8192)
  return original(model,path,buffer)
 mj.mj_saveModel=save_model
 try:yield
 finally:mj.mj_saveModel=original
