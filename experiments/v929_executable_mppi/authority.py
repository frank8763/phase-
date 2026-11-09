import hashlib,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v929_executable_mppi'
sys.path.insert(0,str(R/'experiments/v862_ready_static'));from handshake import require
read=lambda p:json.loads(Path(p).read_text())
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def root_authorized(now,freeze):
 a=read(O/'AUTHORIZATION.json');w=read(O/'ROUND_WINDOW.json');require(not(O/'COMPLETION.json').exists(),'ROUND_CLOSED');require(a['models_authorized']and a['scope']=='V929_PREDICTIVE_BASELINE','NO_AUTHORITY');require(a['started_unix']==w['started_unix']and a['deadline_unix']==w['deadline_unix']and 0<a['deadline_unix']-a['started_unix']<=5400 and a['started_unix']<=now<a['deadline_unix']-30,'WINDOW');require(a['source_freeze_sha256']==freeze,'FREEZE');require(all(read(O/n)['passed']for n in ['PROJECTION_QUALIFICATION.json','ZERO_MODEL_QUALIFICATION.json','FULL_STARTUP_QUALIFICATION.json','CONTROLLER_SOFTWARE_QUALIFICATION.json']),'QUALIFICATION_FAILED');return a

def authorized(task,receipt,now,freeze):
 a=root_authorized(now,freeze);require(receipt==dict(a,run_id=task['run_id'],task_sha256=digest(task)),'RECEIPT');tasks=read(C/'TASKS.json');require(task in tasks,'UNREGISTERED');i=tasks.index(task)
 for prior in tasks[:i]:require(read(Path(prior['output'])/'INDEPENDENT_AUDIT.json')['passed'],'PRIOR_STAGE_FAILED')
 return a['deadline_unix']
