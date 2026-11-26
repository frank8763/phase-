from pathlib import Path
import hashlib,importlib.util,json,os,sys,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):
 p=Path(p);x=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and'inherit_freeze_path'in x:
  q=R/x['inherit_freeze_path'];assert sha(q)==x['inherit_freeze_sha256'];f=read(q)['files'];assert all(n not in f or f[n]==h for n,h in x['files'].items());x=dict(x,files=dict(f,**x['files']))
 return x
def put(p,v):
 p=Path(p);raw=json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=2*1024**2;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def authority(method):
 a=read(S/(method+'_ADMISSION.json'));assert a['scope']=='PRIEST_OPTIMIZER_ONLY'if method=='PRIEST'else a['scope']=='PSF_PCBF_LINEAR_FORMULATION_ONLY'
 assert a['models_authorized']is False and a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and time.time()<a['absolute_deadline_unix']and time.monotonic()<a['hard_stop_monotonic'];assert os.sched_getaffinity(0)=={7 if method=='PRIEST'else 2};assert a['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')and read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,files
