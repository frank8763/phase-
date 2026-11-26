"""One exposed SVG vehicle component, admitted only after the current queue closes."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;OLD=R/'experiments/v1281_partial_reconnection_fixed24'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):
 p=Path(p);x=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and'inherit_freeze_path'in x:
  q=R/x['inherit_freeze_path'];assert sha(q)==x['inherit_freeze_sha256'];f=read(q)['files'];assert all(n not in f or f[n]==h for n,h in x['files'].items());x=dict(x,files=dict(f,**x['files']))
 return x
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def put(p,x):
 p=Path(p);raw=json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False,default=lambda a:a.tolist()).encode()+b'\n';assert len(raw)<=2*1024**2;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def remaining(w):
 assert w['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip();return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
def queue_closed():
 S=R/'runs/v2045_remaining_parallel_source';plan=read(S/'PLAN_LOCKED.json')
 for row in plan['methods']['MPPI']:
  d=R/row['root'];assert read(d/'COMPLETION.json')['closed']and read(d/'POST_ROUND_STORAGE_BARRIER.json')['passed'],'PRIOR_CASE_EVIDENCE_BARRIER_PENDING'
  i=read(d/'OWNED_CHILD.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks'],'PRIOR_NUMERICAL_OWNER_STILL_LIVE'
 # Preserve every old failed parent as historical metadata. It need not be
 # rewritten as PASS when its actual cases have genuine final barriers.
 old=read(R/'runs/v2051_mppi_remaining_seven_resume/RESULT.json');assert old['closed']and old['pipeline_passed']is False
 retire=R/'runs/v2050_closed_queue_retention_recovery/reconcile_common_12__MPPI/PROOF.json';assert read(retire)['passed'],'FINAL_CASE_QUIESCENT_RETIREMENT_PENDING'
 assert read(S/'RETENTION_STATE.json')['retention_reconciliation_proof_path']==str(retire.relative_to(R)),'FINAL_CASE_STORAGE_STATE_PENDING'
 import fcntl
 for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  with(R/name).open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for root in ['v2055_svg_vehicle_stop_component','v2059_svg_recovered_queue_prerequisite']:
  p=R/'runs'/root;assert not(p/'PILOT_ONCE_CLAIM.json').exists()and not(p/'actual').exists(),'PRIOR_SVG_SCOPE_ALREADY_EXECUTED'
 prior=R/'runs/v2073_svg_parameter_inheritance_scope';assert read(prior/'COMPLETION.json')['closed']and read(prior/'POST_COMPONENT_STORAGE_BARRIER.json')['passed'],'PRIOR_COMPONENT_EVIDENCE_PENDING'
 i=read(prior/'OWNED_CHILD.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks'],'PRIOR_COMPONENT_OWNER_STILL_LIVE'
 prior=R/'runs/v2079_svg_file_bound_transport';assert read(prior/'COMPLETION.json')['passed']and read(prior/'POST_COMPONENT_STORAGE_BARRIER.json')['passed'],'PRIOR_CURRENT_COMPONENT_PENDING'
 i=read(prior/'OWNED_CHILD.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks'],'PRIOR_CURRENT_COMPONENT_STILL_LIVE'
 prior=R/'runs/v2086_svg_persistent_peer_import_scope';assert read(prior/'COMPLETION.json')['closed']and read(prior/'POST_COMPONENT_STORAGE_BARRIER.json')['passed'],'COUNTER_FAILURE_EVIDENCE_PENDING'
 i=read(prior/'OWNED_CHILD.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks'],'COUNTER_FAILURE_CHILD_STILL_LIVE'
 return True

def admission(task):
 a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json');assert a['scope']=='SVG_CURRENT_ORIGINAL_VEHICLE_INTERFACE_COMPONENT'and a['models_authorized']and a['assignment']==task
 assert a['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')and remaining(w)>60 and(O/'PILOT_ONCE_CLAIM.json').is_file()and a['independent_parallel_owner']is True
 assert task['component_not_navigation']and task['maximum_control_native']==10 and task['stop_native']==2200
 assert os.sched_getaffinity(0)=={2}and os.environ['PHASE_REPO']==str(R)
 assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];queue_closed()
 files=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,w,files
def native_authority():
 assert os.sched_getaffinity(0)=={7};a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json');assert a['scope']=='SVG_CURRENT_ORIGINAL_VEHICLE_INTERFACE_COMPONENT'and a['models_authorized']and remaining(w)>30
 assert a['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')and read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];files=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items());return a,files
