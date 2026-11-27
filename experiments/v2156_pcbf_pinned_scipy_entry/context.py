from pathlib import Path
import hashlib,json,os,time,sys,importlib.util
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;ROOT=R/'runs'/C.name;O=ROOT/'components/MATH';P=R/'runs/v2154_pcbf_coordinate_conditioning'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=Path(p);v=json.loads(p.read_bytes())
 if p.name=='SOURCE_FREEZE.json'and'inherit_freeze_path'in v:
  q=R/v['inherit_freeze_path'];assert sha(q)==v['inherit_freeze_sha256'];old=read(q)['files'];assert all(n not in old or old[n]==h for n,h in v['files'].items());v=dict(v,files=dict(old,**v['files']))
 return v
def put(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.tolist()).encode()+b'\n';assert len(raw)<=256*1024;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def authority():
 assert os.sched_getaffinity(0)=={3}and os.environ.get('PHASE_REPO')==str(R)and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 a=read(O/'NUMERICAL_ADMISSION.json');assert a['scope']=='FINITE_IDEAL_PCBF_COORDINATE_TRANSFORM_ONLY'and a['numerical_authorized']and not a['models_authorized']and a['worker_sha256']==sha(C/'worker.py')and a['source_freeze_sha256']==sha(ROOT/'SOURCE_FREEZE.json')and time.time()<a['absolute_end_unix']and time.monotonic()<a['hard_stop_monotonic']and a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert read(ROOT/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];files=read(ROOT/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,files
