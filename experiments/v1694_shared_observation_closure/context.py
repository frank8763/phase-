"""Source-only shared contract scope; grants no model authority."""
import hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,value):
 raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=4*1024**2
 p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
