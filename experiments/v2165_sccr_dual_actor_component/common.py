from pathlib import Path
import hashlib,json,importlib.util,sys,os,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;O=S/'components/POLICY'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):
 p=Path(p);v=json.loads(p.read_bytes())
 if p.name=='SOURCE_FREEZE.json'and'inherit_freeze_path'in v:
  parent=R/v['inherit_freeze_path'];assert sha(parent)==v['inherit_freeze_sha256'];base=read(parent)['files'];assert all(n not in base or base[n]==h for n,h in v['files'].items());v=dict(v,files=dict(base,**v['files']))
 return v
def dump(p,v):
 p=Path(p);raw=json.dumps(v,allow_nan=False,default=lambda x:x.tolist(),separators=(',',':')).encode()+b'\n';assert len(raw)<512*1024;p.write_bytes(raw)
def load(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def authority():
 assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 p=O/'NUMERICAL_ADMISSION.json';assert p.is_file(),'SCCR_TWO_ACTORS_NOT_ADMITTED'
 a=read(p);assert a['scope']=='SCCR_TWO_FROZEN_ACTORS_SAVED_COMPONENT_ONLY'and a['models_authorized']and not a['physical_admission']and a['training_updates']==0 and a['maximum_direct_forward_calls_per_actor']==3 and a['maximum_reference_batch_forward_calls_per_actor']==1
 assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and time.time()<a['absolute_end_unix']and time.monotonic()<a['hard_stop_monotonic']
 assert a['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')and read(S/'SOURCE_QUALIFICATION.json')['passed']and read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());env=read(S/'ENVIRONMENT_READINESS.json')
 for group in ['loaded_python_file_sha256','loaded_native_library_sha256']:
  for n,h in env[group].items():assert sha(n)==h,'SCCR_ENVIRONMENT_DEPENDENCY_CHANGED'
 for n,h in read(S/'ENVIRONMENT_LAZY_DEPENDENCIES.json')['python_or_native_files'].items():assert sha(n)==h,'SCCR_LAZY_LIBRARY_DEPENDENCY_CHANGED'
 late=read(S/'LAZY_IMPORT_READINESS.json')
 for group in ['loaded_python_file_sha256','loaded_native_library_sha256']:
  for n,h in late[group].items():assert sha(n)==h,'SCCR_OBSERVED_LAZY_LIBRARY_CHANGED'
 return a,files
