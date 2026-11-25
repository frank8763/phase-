"""Two explicitly authorized, isolated native-math CPU lanes; no plant."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;ROOT=R/'runs'/C.name;LANE=os.environ.get('PHASE_ALGORITHM_LANE','');LANES={'MPPI':6};assert not LANE or LANE in LANES,'UNDECLARED_PARALLEL_LANE';O=ROOT/'lanes'/LANE if LANE else ROOT
def read(p):
 p=Path(p);v=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and 'inherit_freeze_path'in v:
  parent=R/v['inherit_freeze_path'];assert hashlib.sha256(parent.read_bytes()).hexdigest()==v['inherit_freeze_sha256'],'PARENT_FREEZE_SHA_CHANGED'
  inherited=read(parent)['files'];delta=v['files'];assert all(n not in inherited or inherited[n]==h for n,h in delta.items()),'FROZEN_PARENT_OVERRIDE'
  v=dict(v,files=dict(inherited,**delta))
 return v
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def put(p,v):
 raw=json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n';assert len(raw)<=2*1024**2,'PARALLEL_METADATA_2MIB_CAP';p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes(raw);tmp.replace(p)
def authority():
 assert LANE in LANES and os.sched_getaffinity(0)=={LANES[LANE]},'PARALLEL_LANE_AFFINITY'
 a=read(O/'ADMISSION.json');w=read(ROOT/'SOURCE_FREEZE.json');rec=read(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert a['lane']==LANE and a['cpu']==LANES[LANE]and a['no_physics']and a['constructor_cap']==a['query_cap']==1
 assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==a['boot_id']and time.time()<a['deadline_unix']and time.monotonic()<a['deadline_monotonic']
 assert a['source_freeze_sha256']==sha(ROOT/'SOURCE_FREEZE.json')and a['input_sha256']==sha(O/'INPUT.json')and a['recovery_sha256']==sha(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
 assert rec['passed']and rec['all_frozen_members_remote_chain_covered']and all(sha(R/n)==h for n,h in w['files'].items());return a,w
