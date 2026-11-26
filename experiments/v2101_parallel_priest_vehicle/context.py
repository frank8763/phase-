"""One immutable PRIEST component source, distinct original task once/owner outputs."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs'/C.name
STUDY=SOURCE
RID='priest_current_vehicle_component';O=SOURCE/'vehicle';OLD=R/'experiments/v1281_partial_reconnection_fixed24'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):
 p=Path(p);v=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and'inherit_freeze_path'in v:
  parent=R/v['inherit_freeze_path'];assert sha(parent)==v['inherit_freeze_sha256'];base=read(parent)['files'];assert all(n not in base or base[n]==h for n,h in v['files'].items());v=dict(v,files=dict(base,**v['files']))
 return v
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def put(p,x):
 p=Path(p);raw=json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False,default=lambda a:a.tolist()).encode()+b'\n';assert len(raw)<=4*1024**2;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def remaining(w):
 assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip();return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def predecessors_closed():
 p=R/'runs/v2095_svg_common_full_route/rounds/common_02__SVGMPPI';assert read(p/'COMPLETION.json')['closed']and read(p/'POST_ROUND_STORAGE_BARRIER.json')['passed']
 for root,name in [(p,'OWNED_CHILD.json'),(R/'runs/v2100_svg_second_formal_dispatch','LAUNCH_IDENTITY.json')]:
  i=read(root/name);proc=Path('/proc',str(i['pid']),'stat');assert not proc.exists()or proc.read_text().split(') ',1)[1].split()[19]!=i['start_ticks'],'PRIOR_NUMERICAL_OWNER_LIVE'
 return True
def admission(task):
 a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='PRIEST_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and a['assignment']==task and a['independent_parallel_owner']
 assert a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and remaining(w)>60 and(O/'PILOT_ONCE_CLAIM.json').is_file()
 assert task['component_not_navigation']is True and task['maximum_control_native']==5 and task['stop_native']==2200 and task['task_id']==RID
 assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)
 assert read(SOURCE/'SOURCE_QUALIFICATION.json')['passed']and read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files
def native_authority():
 assert os.sched_getaffinity(0)=={6};a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='PRIEST_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and remaining(w)>60 and a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')
 assert read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,files
