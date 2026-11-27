"""Pure admission check BEFORE SciPy/NumPy or any numerical constructor."""
from pathlib import Path
import os,json,hashlib,time,importlib.util,sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;O=S/'components/PROJ';A=O/'actual'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):
 p=Path(p);x=json.loads(p.read_bytes())
 if p.name=='SOURCE_FREEZE.json'and'inherit_freeze_path'in x:
  q=R/x['inherit_freeze_path'];assert sha(q)==x['inherit_freeze_sha256'];old=read(q)['files'];assert all(n not in old or old[n]==v for n,v in x['files'].items());x=dict(x,files=dict(old,**x['files']))
 return x
def authority():
 a=read(A/'PROJECTION_OPTIMIZER_ADMISSION.json') # deliberately FIRST
 assert os.sched_getaffinity(0)=={6}and os.environ.get('CUDA_VISIBLE_DEVICES')==''and os.environ.get('PHASE_REPO')==str(R)
 assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and min(a['absolute_deadline_unix']-time.time(),a['hard_stop_monotonic']-time.monotonic())>0,'PEER_ADMISSION_DUAL_CLOCK'
 assert a['scope']=='ONE_FRESH_REST_ORIENTATION_PROJECTION_ONLY'and a['models_authorized']is False and a['maximum_queries']==1
 assert a['worker_sha256']==sha(C/'peer_entry.py')and a['source_freeze_sha256']==sha(S/'SOURCE_FREEZE.json')and(A/'PROJECTION_PEER_ONCE.json').exists()
 claim=read(A/'PROJECTION_PEER_ONCE.json');assert claim['admission_sha256']==sha(A/'PROJECTION_OPTIMIZER_ADMISSION.json')and claim['query_nonce']==a['query_nonce']and claim['maximum_queries']==1 and 'first_input_sha256'not in a,'ACYCLIC_SINGLE_QUERY_CLAIM'
 w=read(O/'PILOT_WINDOW.json');assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and min(w['normal_end_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic()-1200)>120
 assert not(O/'COMPLETION.json').exists()and not(A/'RESULT.json').exists();p=read(O/'PILOT_ADMISSION.json');assert p['models_authorized']and p['scope']=='FILTER_CURRENT_VEHICLE_COMPONENT'and p['source_freeze_sha256']==a['source_freeze_sha256']
 assert read(S/'SOURCE_QUALIFICATION.json')['passed']and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files
