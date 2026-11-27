"""One immutable FILTER component source, distinct original task once/owner outputs."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs'/C.name
STUDY=SOURCE
METHOD=os.environ.get('PHASE_FILTER_METHOD','PSF');assert METHOD in{'PSF','PCBF'}
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
 prior=R/'runs/v2128_filter_segment_wire';d=read(prior/'DISPATCH_RESULT.json');assert d['closed']and not d['finite_queue_completed']and len(d['components'])==1
 o=prior/'components/PSF';m=read(o/'COMPLETION.json');audit=m['independent_audit']
 assert m['closed']and not m['passed']and m['all_source_SHA_after_child']and m['actual_native']==m['own_replay_native']==210 and audit['passed']
 assert audit['normal_native_with_current_admission']==10 and audit['compact_query_audit']['query_records']==2
 assert 'FILTER_NATIVE_PEER_ERROR'in m['machine_first_error']['error']and len(m['machine_secondary_errors'])==1 and 'FILTER_NATIVE_EOF_BEFORE_REPLY'in m['machine_secondary_errors'][0]['error']
 wire=read(o/'actual/FILTER_QUERY_002_INPUT.json');assert wire['current']['sim_time']==.09999999999999999 and wire['request']['case']['sim_time']==.1
 assert read(o/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']
 for path in[o/'OWNED_CHILD.json',prior/'workers/PSF_owner.IDENTITY.json',prior/'LAUNCH_IDENTITY.json',o/'actual/FILTER_NATIVE_PEER_IDENTITY.json']:
  i=read(path);p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks'],'PRIOR_FILTER_IDENTITY_LIVE'
 assert not(prior/'components/PCBF/PILOT_ONCE_CLAIM.json').exists()
 return True
def admission(task):
 a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and a['assignment']==task and a['independent_parallel_owner']
 assert a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and remaining(w)>60 and(O/'PILOT_ONCE_CLAIM.json').is_file()
 assert task['component_not_navigation']is True and task['maximum_control_native']==100 and task['stop_native']==2200 and task['task_id']==RID
 assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)
 assert read(SOURCE/'SOURCE_QUALIFICATION.json')['passed']and read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files
def native_authority():
 assert os.sched_getaffinity(0)=={6};a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and remaining(w)>60 and a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')
 assert read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,files
