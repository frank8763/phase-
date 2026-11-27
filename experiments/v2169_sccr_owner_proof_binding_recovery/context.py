"""One immutable FILTER component source, distinct original task once/owner outputs."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs'/C.name
STUDY=SOURCE
METHOD=os.environ.get('PHASE_FILTER_METHOD','SCCR');assert METHOD=='SCCR'
RID=METHOD.lower()+'_current_vehicle_component';O=SOURCE/'components'/METHOD;OLD=R/'experiments/v1281_partial_reconnection_fixed24'
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
 prior=R/'runs/v2168_sccr_live_union';o=prior/'components/SCCR'
 assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
 assert read(o/'COMPLETION.json')['closed']and not read(o/'COMPLETION.json')['passed']and read(o/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']
 assert read(o/'RUNTIME_CLOSED_REVIEW.json')['machine_counts_remain_null']and read(o/'RUNTIME_CLOSED_REVIEW.json')['source_derived_counts_separate']['factory_attempts']==0
 assert all(not(o/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','actual'])
 i=read(prior/'LAUNCH_IDENTITY.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 return True
def admission(task):
 a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and a['assignment']==task and a['independent_parallel_owner']
 assert a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and remaining(w)>60 and(O/'PILOT_ONCE_CLAIM.json').is_file()
 assert task['component_not_navigation']is True and task['maximum_control_native']==10 and task['stop_native']==2200 and task['task_id']==RID
 assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)
 assert read(SOURCE/'SOURCE_QUALIFICATION.json')['passed']and read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files
def native_authority():
 assert os.sched_getaffinity(0)=={6};a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and remaining(w)>60 and a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')
 assert read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,files
