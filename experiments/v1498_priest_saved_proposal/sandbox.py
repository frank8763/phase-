"""Read-only nested Phase worker with a finite native scratch filesystem."""
import base64
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import tarfile
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def command(task,*,mode,scratch_bytes):
 assert mode in {'IO_TARGET','OPTIMIZER'}and scratch_bytes==(65536 if mode=='IO_TARGET'else 2*1024**2)
 volatile=task/'volatile';volatile.mkdir()
 return ['bwrap','--die-with-parent','--new-session','--unshare-all','--ro-bind','/','/','--ro-bind','/tmp','/tmp','--ro-bind','/dev/shm','/dev/shm','--size',str(scratch_bytes),'--tmpfs',str(volatile),'--chdir',str(R),'--setenv','HOME',str(volatile),'--setenv','TMPDIR',str(volatile),'--setenv','MPLCONFIGDIR',str(volatile/'mpl'),'--setenv','XDG_CACHE_HOME',str(volatile/'cache'),'--setenv','JAX_ENABLE_COMPILATION_CACHE','false','--setenv','JAX_PLATFORMS','cpu','--setenv','JAX_ENABLE_X64','true','--setenv','XLA_FLAGS','--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1','--setenv','TF_NUM_INTRAOP_THREADS','1','--setenv','TF_NUM_INTEROP_THREADS','1','--setenv','OMP_NUM_THREADS','1','--setenv','OPENBLAS_NUM_THREADS','1','--setenv','MKL_NUM_THREADS','1','--setenv','CUDA_VISIBLE_DEVICES','','--setenv','PYTHONDONTWRITEBYTECODE','1','--setenv','PHASE_WORKER_TASK',str(task),'--setenv','PHASE_WORKER_MODE',mode,str(Path('/home/linghu/miniconda3/envs/mk_mujoco/bin/python')),'-B',str(C/'inner.py')]

def run(task,*,mode,writer,wall_s):
 assert task.is_relative_to(R/'runs')and sorted(os.sched_getaffinity(0))==[4]
 start=time.monotonic();cmd=command(task,mode=mode,scratch_bytes=65536 if mode=='IO_TARGET'else 2*1024**2)
 console=task/'WORKER_PIPE.jsonl';writer.reserve(console,8192)
 p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);os.set_blocking(p.stdout.fileno(),False)
 sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);count=0;first=None;maxthreads=0;rows=[]
 try:
  with console.open('xb')as out:
   while sel.get_map():
    assert time.monotonic()-start<wall_s,'WORKER_OUTER_WALL_EXPIRED'
    for key,_ in sel.select(.1):
     block=os.read(key.fileobj.fileno(),65536)
     if not block:sel.unregister(key.fileobj);continue
     assert count+len(block)<=8*1024**2,'WORKER_PARENT_PIPE_CAP'
     writer.reserve(console,len(block));out.write(block);out.flush();count+=len(block)
    if p.poll()is not None and not sel.get_map():break
  code=p.wait(timeout=2)
 except BaseException as e:
  first=repr(e)
  if p.poll()is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=2)
  code=p.returncode
 finally:sel.close();p.stdout.close()
 # Last signed source-bound terminal record; earlier native stderr is retained.
 record=None
 for line in console.read_text(errors='replace').splitlines():
  try:value=json.loads(line)
  except (ValueError,TypeError):continue
  if isinstance(value,dict)and value.get('kind')=='PHASE_BOUNDED_WORKER_TERMINAL':assert record is None;record=value
 assert first is None,first
 assert record is not None,'WORKER_TERMINAL_EVIDENCE_MISSING'
 raw=base64.b64decode(record['volatile_archive_base64'],validate=True);assert len(raw)<=4*1024**2 and hashlib.sha256(raw).hexdigest()==record['volatile_archive_sha256']
 archive=task/'VOLATILE_ARCHIVE.tar.gz';writer.reserve(archive,len(raw)+8192);archive.write_bytes(raw)
 seen={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz')as t:
  for member in t:
   assert member.isfile()and member.name not in seen and not Path(member.name).is_absolute()and '..'not in Path(member.name).parts
   stream=t.extractfile(member);data=stream.read(2*1024**2+1);assert len(data)==member.size<=2*1024**2
   seen[member.name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 assert seen==record['volatile_members'],'WORKER_TERMINAL_ARCHIVE_MEMBERS_CHANGED'
 return dict(returncode=code,terminal=record,pipe_bytes=count,outer_wall_s=time.monotonic()-start,archive_SHA_verified=True,models=0)
