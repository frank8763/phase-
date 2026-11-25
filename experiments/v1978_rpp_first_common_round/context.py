"""Original common01 RPP, once formal authority and immutable source."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;OLD=R/'experiments/v1281_partial_reconnection_fixed24'
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def put(p,x):
 raw=json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False,default=lambda a:a.tolist()).encode()+b'\n';assert len(raw)<=4*1024**2;p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def remaining(w):
 assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip();return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def admission(task):
 a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json');assert a['scope']=='RPP_CURRENT_COMMON_FULL_TASK'and a['models_authorized']and a['assignment']==task
 assert a['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')and remaining(w)>60 and (O/'PILOT_ONCE_CLAIM.json').is_file()and not(R/'REVIEW_PENDING').exists()
 shared=next(row['task']for row in read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')['tasks']if row['task']['task_id']==task['common_task_id'])
 for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction']:assert task[k]==shared[k]
 assert task['common_task_id']=='common_01'and task['maximum_control_native']==57600 and task['stop_native']==2200
 assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)
 assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files
