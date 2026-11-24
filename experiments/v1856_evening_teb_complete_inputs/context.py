"""One new scope and pure immutable-source helpers; numerical imports are lazy."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs/v1859_evening_complete_inputs';RID=os.environ.get('PHASE_EVENING_ASSIGNMENT','');O=SOURCE/'rounds'/RID if RID else SOURCE
OLD=R/'experiments/v1281_partial_reconnection_fixed24'
GUARD='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def put(p,x):
 raw=json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False,default=lambda a:a.tolist()).encode()+b'\n'
 assert len(raw)<=4*1024**2;p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def remaining(w):
 assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def sources():
 value=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in value.items());return value
def admission(assignment):
 p=O/'PILOT_ADMISSION.json';assert p.is_file(),'TEB_NAVIGATION_NOT_ADMITTED'
 a=read(p);w=read(O/'PILOT_WINDOW.json')
 assert a['scope']=='TEB_COMMON_CONDITION_FULL_TASK'and a['assignment']==assignment
 registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');shared=next(x['task']for x in registry['tasks']if x['task']['task_id']==assignment['common_task_id']);assert assignment['common_task_id']==shared['task_id']
 for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction']:assert assignment[k]==shared[k]
 assert a['common_registry_sha256']==sha(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')
 assert RID==assignment['task_id']and any(row['round_id']==RID and row['production']==C.name for row in read(SOURCE/'PLAN_LOCKED.json')['assignments'])
 assert a['models_authorized']and remaining(w)>60 and a['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')
 assert read(R/'runs/v1620_mechanism_boundary/UNATTENDED_CONTINUATION_AUTHORIZATION_20261123.json')['overall_calendar_deadline_unix'] is None
 assert 0<w['absolute_deadline_unix']-w['started_unix']<=5400 and 0<w['hard_stop_monotonic']-w['started_monotonic']<=5400
 assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['passed']
 assert read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 assert not(R/'REVIEW_PENDING').exists()and(O/'PILOT_ONCE_CLAIM.json').is_file()
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ['PHASE_REPO']==str(R)
 return a,w,sources()
