"""One immutable FILTER component source, distinct original task once/owner outputs."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs'/C.name
STUDY=SOURCE
METHOD=os.environ.get('PHASE_FILTER_METHOD','PCBF');assert METHOD=='PCBF'
RID=METHOD.lower()+'_current_vehicle_component';O=SOURCE/'components'/METHOD;OLD=R/'experiments/v1281_partial_reconnection_fixed24'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def metadata():
 m=sys.modules.get('v2162_exact_metadata')
 if m is None:m=load('v2162_exact_metadata',C/'metadata_pack.py')
 assert Path(m.__file__).resolve()==C/'metadata_pack.py'
 return m
def read(p):
 p=Path(p);v=json.loads(metadata().read_bytes(p)if p.is_file()and p.stat().st_size==0 and p.suffix=='.json'else p.read_bytes())
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
 psf=R/'runs/v2151_psf_wrapper_identity_binding';o=psf/'components/PSF';m=read(o/'COMPLETION.json')
 assert m['closed']and m['actual_native']==m['own_replay_native']==5195 and m['independent_audit']['passed']and read(o/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']
 math=R/'runs/v2156_pcbf_pinned_scipy_entry';assert read(math/'components/MATH/POST_MATH_STORAGE_BARRIER.json')['passed']
 a=read(R/'runs/v2161_pcbf_conditioning_numeric_audit/RESULT.json');assert a['passed']and a['saved_NLP_returns_verified']==12 and a['five_positive_inputs_passed']and a['occupied_negative_refused_by_unchanged_hard_geometry']and not a['vehicle_or_wholegoal_qualified']
 for f in[o/'OWNED_CHILD.json',psf/'LAUNCH_IDENTITY.json',R/'runs/v2160_math_shared_metadata_recovery/LAUNCH_IDENTITY.json']:
  i=read(f);p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 return True
def admission(task):
 a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and a['assignment']==task and a['independent_parallel_owner']
 assert a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and remaining(w)>60 and(O/'PILOT_ONCE_CLAIM.json').is_file()
 assert task['component_not_navigation']is True and task['maximum_control_native']==500 and task['stop_native']==2200 and task['task_id']==RID
 assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)
 assert read(SOURCE/'SOURCE_QUALIFICATION.json')['passed']and read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files
def native_authority():
 assert os.sched_getaffinity(0)=={6};a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'and a['models_authorized']and remaining(w)>60 and a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')
 assert read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,files
