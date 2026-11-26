from pathlib import Path
import hashlib,importlib.util,json,os,sys,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;O=S/'native_output'
def read(p):
 p=Path(p);v=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and 'inherit_freeze_path'in v:
  q=R/v['inherit_freeze_path'];assert sha(q)==v['inherit_freeze_sha256'];base=read(q)['files'];assert all(n not in base or base[n]==h for n,h in v['files'].items());v=dict(v,files=dict(base,**v['files']))
 return v
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 p=Path(p);raw=json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=1024**2;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def authority():
 assert os.sched_getaffinity(0)=={7};a=read(S/'ADMISSION.json');rec=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert a['no_physics']and a['constructor_cap']==a['query_cap']==1 and rec['passed']and rec['all_frozen_members_remote_chain_covered'];assert a['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')and a['recovery_sha256']==sha(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
 assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and time.time()<a['deadline_unix']and time.monotonic()<a['deadline_monotonic'];frozen=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items());return a,frozen
