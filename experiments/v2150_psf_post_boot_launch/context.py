"""One immutable FILTER component source, distinct original task once/owner outputs."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs'/C.name
STUDY=SOURCE
METHOD=os.environ.get('PHASE_FILTER_METHOD','PSF');assert METHOD=='PSF'
RID='psf_full_route_development';O=SOURCE/'components'/METHOD;OLD=R/'experiments/v1281_partial_reconnection_fixed24'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def metadata():
 m=sys.modules.get('fullroute_metadata_reader')
 if m is None:m=load('fullroute_metadata_reader',C/'metadata_pack.py')
 assert Path(m.__file__).resolve()==C/'metadata_pack.py'
 return m
def read(p):
 p=Path(p);v=json.loads(metadata().read_bytes(p) if p.is_file()and p.stat().st_size==0 and p.suffix=='.json'else p.read_bytes())
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
 assert not(R/'runs/v2147_psf_full_route/components/PSF/PILOT_ONCE_CLAIM.json').exists()and read(R/'runs/v2149_psf_runtime_index_scope/ADAPTER_CLOSED.json')['closed']
 i=read(R/'runs/v2149_psf_runtime_index_scope/LAUNCH_IDENTITY.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 prior=R/'runs/v2137_psf_progress_control';assert read(prior/'DISPATCH_RESULT.json')['finite_queue_completed']
 for root,method in [('v2137_psf_progress_control','PSF'),('v2144_sccr_depth_resource_units','SCCR')]:
  o=R/'runs'/root/'components'/method;m=read(o/'COMPLETION.json');assert m['closed']and m['passed']and m['all_source_SHA_after_child']and m['independent_audit']['passed']and read(o/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']
  for f in [o/'OWNED_CHILD.json',R/'runs'/root/'LAUNCH_IDENTITY.json']:
   i=read(f);p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 recovery=R/'runs/v2145_verified_whole_transport_recovery';v=read(recovery/'RESULT.json');assert v['passed']and v['closed']and v['freed_allocated_bytes']==121692160
 i=read(recovery/'LAUNCH_IDENTITY.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 return True
def admission(task):
 a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and a['assignment']==task and a['independent_parallel_owner']
 assert a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and remaining(w)>60 and(O/'PILOT_ONCE_CLAIM.json').is_file()
 assert task['component_not_navigation']is False and task['exposed_full_route_development']and task['maximum_control_native']==12500 and task['stop_native']==2200 and task['task_id']==RID
 assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)
 assert read(SOURCE/'SOURCE_QUALIFICATION.json')['passed']and read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files
def native_authority():
 assert os.sched_getaffinity(0)=={6};a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and remaining(w)>60 and a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')
 assert read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,files
