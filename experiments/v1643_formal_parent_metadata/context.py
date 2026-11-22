"""Immutable registry plus per-assignment authority; source checks are lazy."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;ROOT=R/'runs'/C.name
OLD=R/'experiments/v1281_partial_reconnection_fixed24'
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
key=os.environ.get('PHASE_FORMAL_ASSIGNMENT')
if key is None:O=ROOT
else:
 keys=[a['assignment_id']for row in read(ROOT/'TASKS_LOCKED.json')['tasks']for a in row['assignments']]
 assert key in keys and '/'not in key,'UNREGISTERED_FORMAL_ASSIGNMENT';O=ROOT/'rounds'/key

def put(p,x):
 raw=json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False,default=lambda a:a.tolist()).encode()+b'\n'
 assert len(raw)<=4*1024**2;p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def remaining(w):
 assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def sources():
 value=read(ROOT/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in value.items());return value

def admission():
 p=O/'FORMAL_ADMISSION.json';assert O!=ROOT and p.is_file(),'REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED'
 task=read(O/'FORMAL_TASK.json');a=read(p);w=read(O/'ROUND_WINDOW.json')
 descriptor=load('v1642_registered_selection',C/'phase_contract.py').select(read(ROOT/'TASKS_LOCKED.json'),key,ROOT)
 assert descriptor['task']==task and task['case_id']=='WEST_EAST'
 assert task['mechanism_variant']in {'full','no_onward'}
 assert a['scope']=='ORIGINAL_V1281_WE_PHASE_COMPARISON'and a['assignment']==task and a['models_authorized']
 assert a['scientific_task_sha256']==descriptor['scientific_task_sha256']and a['source_freeze_sha256']==sha(ROOT/'SOURCE_FREEZE.json')
 assert read(R/'runs/v1620_mechanism_boundary/UNATTENDED_CONTINUATION_AUTHORIZATION_20261123.json')['overall_calendar_deadline_unix']is None
 assert 0<w['absolute_deadline_unix']-w['started_unix']<=5400 and 0<w['hard_stop_monotonic']-w['started_monotonic']<=5400 and remaining(w)>60
 q=read(ROOT/'SOURCE_QUALIFICATION.json');assert q['passed']and set(q['qualified_variants'])=={'full','no_onward'}and q['qualified_case_id']=='WEST_EAST'
 recovery=read(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
 assert not(R/'REVIEW_PENDING').exists()and(O/'ROUND_ONCE_CLAIM.json').is_file()
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ['PHASE_REPO']==str(R)
 return a,w,sources(),task
