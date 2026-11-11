"""Zero-model selected reproducibility records; never launches a driver."""
import fcntl,hashlib,json,shutil,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1022_full_route_planner';D=R/'records/nav2_v1022_20261111'
def read(p):return json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert digest(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 D.mkdir(exist_ok=True)
 names=['FAST_QUALIFICATION.json','CERTIFICATE_QUALIFICATION.json','API_QUALIFICATION.json','INDEPENDENT_STATIC_GEOMETRY.json','PREPARATION_ERRORS.json']
 for name in names:shutil.copyfile(O/name,D/name)
 plan=read(O/'ns_initial.input_route.json');pref=R/'runs/v858_nav2_verified/v1020/PREFLIGHTS/ns'
 p=read(pref/'PREFLIGHT.json');packet=dict(body=p['body'],native_tick=0,sim_time=0.,body_measured_at=0.,dynamic_discovered=False,steering=dict(position=p['steering'][:2],velocity=p['steering'][2:],native_tick=0,measured_at=0.),controller_memory=dict(last_ctrl=[0.]*4,integral=0.))
 fixture=dict(packet=packet,source=None,setup=read(pref/'SETUP.json'),original_goal=plan['original_goal'],edge_targets=plan['edge_targets'],certificate_scope=plan['certificate_scope'],snapshot_binding_sha256=plan['snapshot_binding_sha256'])
 dump(D/'NS_SOURCE_FIXTURE.json',fixture)
 np.savez_compressed(O/'NS_COMPLETE_INPUT_PREDICTION.npz',state=np.asarray(plan['state_path']),ctrl=np.asarray(plan['predicted_actuator_controls']),requests=np.asarray(plan['planned_body_requests']))
 summaries=[]
 for path in sorted(O.glob('*.input_route.json')):
  p=read(path);summary={k:v for k,v in p.items()if k not in ['path','state_path','planned_body_requests','predicted_actuator_controls','edge_targets']};summaries.append(dict(input=path.name,**summary))
 dump(D/'FIXED_INPUT_RESULTS.json',summaries)
 # Retain non-success preparation diagnoses and all fixed dynamic input packets,
 # so the failed route searches remain reproducible without whole old raw runs.
 failures=[]
 for route in ['we','ns']:
  old=R/'runs/v858_nav2_verified/v1020'/('main_'+route);row=read(old/'RECOVERY_CORRIDORS.json')[0]
  failures.append(dict(route=route,packet=row['search_packet'],source=row['search_source'],original_goal=row['original_goal'],setup=read(old/'physics/SETUP.json')))
 dump(D/'DYNAMIC_REJECTION_FIXTURES.json',failures)
 scientific=[*C.glob('*.py'),*C.glob('*.cpp'),*C.glob('*.md')]
 freeze=dict(models=0,integrations=0,scope='ZERO_MODEL_SOURCE_ONLY',files=[dict(path=str(p.relative_to(R)),sha256=digest(p))for p in sorted(scientific)])
 dump(C/'SOURCE_FREEZE.json',freeze)
 result=dict(status='CORE_SOURCE_QUALIFIED_DYNAMIC_ROUTE_UNRESOLVED',core_admission_qualification_passed=all(read(O/n)['passed']for n in names if n!='PREPARATION_ERRORS.json'),
  full_static_NS_source_qualified=True,dynamic_full_route_qualification_passed=False,physical_ready=False,models_authorized=False,
  model_initializations=0,navigation_native=0,private_mujoco_native=0,own_replay_native=0,training_updates=0,hardware_steps=0,
  analytic_steps_and_search_expansions_in_separate_qualifications=True,old_failures_and_deadlines_preserved=True,
  guard_original=True,execution_lock_idle=True,source_freeze_sha256=digest(C/'SOURCE_FREEZE.json'),created_unix=time.time(),
  remaining='New full-route native/discovery/ownership and installed Nav2 integration qualification; complete dynamic input route; new bounded physical window before any model.')
 dump(D/'SOURCE_QUALIFICATION.json',result)
 index=dict(necessary_evidence=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=digest(p))for p in sorted(D.iterdir())if p.is_file()and p.name not in {'EVIDENCE_INDEX.json','RECORD_INDEX.json','REMOTE_VERIFIED.json','SOURCE_SYNC_CLAIM.json','SOURCE_SYNC_RESULT.json'}],
  whole_prediction=dict(path=str((O/'NS_COMPLETE_INPUT_PREDICTION.npz').relative_to(R)),bytes=(O/'NS_COMPLETE_INPUT_PREDICTION.npz').stat().st_size,sha256=digest(O/'NS_COMPLETE_INPUT_PREDICTION.npz')),
  raw_source_scope='Analytical source qualification only; no new physical evidence',remote_verified=False)
 dump(D/'EVIDENCE_INDEX.json',index);print(json.dumps(result))
if __name__=='__main__':main()
