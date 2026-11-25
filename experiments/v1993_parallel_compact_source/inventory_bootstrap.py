"""Standard interpreter ELF inventory only; no algorithm DLL or constructor."""
from pathlib import Path
import ctypes,fcntl,hashlib,importlib.abc,json,os,resource,time,traceback
out={}
for line in Path('/proc/self/maps').read_text().splitlines():
 cols=line.split(None,5)
 if len(cols)==6 and cols[5].startswith('/'):
  p=Path(cols[5])
  if p.is_file():
   with p.open('rb')as f:magic=f.read(4)
   if magic==b'\x7fELF':out[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
print(json.dumps(dict(standard_interpreter_only=True,algorithm_DLL_loads=0,controller_queries=0,files=out)))
