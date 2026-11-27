"""Fresh finite ideal-math authority; no plant/model/old runtime entry."""
from pathlib import Path
import hashlib,json,os,time,sys,importlib.util,math
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;ROOT=R/'runs'/C.name;O=ROOT/'components/MATH';P=R/'runs/v2176_sccr_common_plant_component'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):
 p=Path(p);v=json.loads(p.read_bytes())
 if p.name=='SOURCE_FREEZE.json'and'inherit_freeze_path'in v:
  q=R/v['inherit_freeze_path'];assert sha(q)==v['inherit_freeze_sha256'];old=read(q)['files'];assert all(n not in old or old[n]==h for n,h in v['files'].items());v=dict(v,files=dict(old,**v['files']))
 return v
def native(v):
 if hasattr(v,'tolist'):return v.tolist()
 if hasattr(v,'item'):return v.item()
 raise TypeError(type(v).__name__)
def put(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(v,indent=2,allow_nan=False,default=native).encode()+b'\n';assert len(raw)<=1024**2;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def remaining(a):
 assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip();return min(a['absolute_end_unix']-time.time(),a['hard_stop_monotonic']-time.monotonic())
def predecessor_closed():
 assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'components/SCCR/POST_COMPONENT_STORAGE_BARRIER.json')['passed']and read(P/'components/SCCR/COMPLETION.json')['closed']
 for n in ['LAUNCH_IDENTITY.json','components/SCCR/OWNED_CHILD.json']:
  i=read(P/n);p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 return True
def authority():
 a=read(O/'NUMERICAL_ADMISSION.json') # FIRST: no numerical imports before this call
 assert os.sched_getaffinity(0)=={3}and os.environ.get('PHASE_REPO')==str(R)and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 assert a['scope']=='FINITE_ORIENTATION_STATE_PROJECTION_ONLY'and a['numerical_authorized']and not a['models_authorized']and a['maximum_NLP_calls']==2
 assert a['worker_sha256']==sha(C/'worker.py')and a['source_freeze_sha256']==sha(ROOT/'SOURCE_FREEZE.json')and remaining(a)>1
 assert not(O/'COMPLETION.json').exists()and read(ROOT/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 assert read(ROOT/'SOURCE_QUALIFICATION.json')['passed'];files=read(ROOT/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,files
