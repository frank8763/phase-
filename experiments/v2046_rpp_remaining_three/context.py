"""Exposed-course current RPP component, no common formal slot authority."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs/v2045_remaining_parallel_source';RID=os.environ.get('PHASE_COMMON_ASSIGNMENT','common_10__RPP');assert RID in ['common_10__RPP', 'common_11__RPP', 'common_12__RPP'];O=SOURCE/'rounds'/RID;OLD=R/'experiments/v1281_partial_reconnection_fixed24'
def read(p):
 p=Path(p);v=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and 'inherit_freeze_path'in v:
  parent=R/v['inherit_freeze_path'];assert sha(parent)==v['inherit_freeze_sha256'];base=read(parent)['files'];assert all(n not in base or base[n]==h for n,h in v['files'].items());v=dict(v,files=dict(base,**v['files']))
 return v
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def put(p,x):
 raw=json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False,default=lambda a:a.tolist()).encode()+b'\n';assert len(raw)<=4*1024**2;p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def remaining(w):
 assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip();return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def admission(task):
 a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json');assert a['scope']=='RPP_CURRENT_COMMON_FULL_TASK'and a['models_authorized']and a['assignment']==task
 assert a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and remaining(w)>60 and (O/'PILOT_ONCE_CLAIM.json').is_file()and a['independent_parallel_owner']is True
 assert task['component_not_navigation']is False and task['maximum_control_native']==57600 and task['stop_native']==2200 and task['task_id']==RID and task['common_task_id']==RID.split('__')[0]
 assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)
 assert read(SOURCE/'SOURCE_QUALIFICATION.json')['passed']and read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files
