from pathlib import Path
import hashlib,importlib.util,json,os,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):
 v=json.loads(Path(p).read_text())
 if Path(p).name=='SOURCE_FREEZE.json'and'inherit_freeze_path'in v:
  p=R/v['inherit_freeze_path'];assert sha(p)==v['inherit_freeze_sha256'];parent=read(p)['files'];assert all(n not in parent or parent[n]==h for n,h in v['files'].items());v=dict(v,files=dict(parent,**v['files']))
 return v
def put(p,v):
 raw=(json.dumps(v,indent=2,allow_nan=False)+'\n').encode();assert len(raw)<=1024**2
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes(raw);tmp.replace(p)
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def authority(cpu,kind):
 assert os.sched_getaffinity(0)=={cpu};a=read(S/'COMPONENT_ADMISSION.json')
 assert a['scope']=='EXPLICIT_NON_PHASE_IMPLEMENTATION_COMPONENTS'and a['models_authorized']is False
 assert a['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')and a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert time.time()<a['absolute_end_unix']and time.monotonic()<a['hard_stop_monotonic']
 assert read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
 out=S/kind;assert not(out/'ONCE.json').exists();put(out/'ONCE.json',dict(pid=os.getpid(),cpu=cpu,models=0,unix=time.time()));return a,files,out
