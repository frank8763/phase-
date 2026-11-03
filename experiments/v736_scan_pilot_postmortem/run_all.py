"""One bounded immutable supplemental audit after the failed closed pilot."""
import copy,gzip,hashlib,json,math,os,subprocess,sys,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v736_scan_pilot_postmortem';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (repo/'REVIEW_PENDING').exists();freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());begun=time.time();deadline=begun+600;window=dict(started_unix=begun,absolute_deadline_unix=deadline,limit_s=600,round_closed=False,new_initializations=0,new_integrations=0);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def dump(name,x):(root/name).write_text(json.dumps(x,indent=2)+'\n')
dump('ROUND_WINDOW.json',window);records=[]
try:
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory'
 with gzip.open(cell/'observation_scan_certificate.json.gz','rt')as stream:c=json.load(stream)
 state=next(json.loads(x)for x in(cell/'motion_estimate.jsonl').read_text().splitlines()if json.loads(x)['step']==32)
 def same(candidate,logged):return logged.get('step')==32 and candidate=={k:v for k,v in logged.items()if k!='step'}
 assert c['forecast_state']=={k:v for k,v in state.items()if k!='step'}and set(state)-set(c['forecast_state'])=={'step'}
 negatives=0
 def leaves(value,path=()):
  if isinstance(value,dict):
   for key,v in value.items():yield from leaves(v,path+(key,))
  elif isinstance(value,list):
   for key,v in enumerate(value):yield from leaves(v,path+(key,))
  else:yield path,value
 for path,value in leaves(state):
  altered=copy.deepcopy(state);target=altered
  for key in path[:-1]:target=target[key]
  if isinstance(value,bool):new=not value
  elif isinstance(value,int):new=value+1
  elif isinstance(value,float):new=math.nextafter(value,math.inf)
  elif value is None:new='NOT_NONE'
  else:new=value+'X'
  target[path[-1]]=new;assert not same(c['forecast_state'],altered);negatives+=1
 for mode in ['missing','extra']:
  altered=copy.deepcopy(state)
  if mode=='missing':del altered['free_space_renewal']
  else:altered['unregistered_metadata']=0
  assert not same(c['forecast_state'],altered);negatives+=1
 dump('METADATA_COMPARISON_TESTS.json',dict(status='EXACT_INTERNAL_STATE_AND_NEGATIVES_VERIFIED',original_log_wrapper_only_extra_key='step',all_internal_keys_values_and_hashes_exact=True,negative_cases_rejected=negatives,original_failed_audit_unchanged=True,new_integrations=0))
 for script in ['audit_early_scan.py','audit_route_commitment.py','audit_projection_learning.py','audit_all_tail_geometry.py','audit_shadow_mode.py','audit_field_discovery.py']:
  assert time.time()+93<deadline
  with (root/(script+'.console')).open('x')as out:r=subprocess.run([sys.executable,'-B',str(own/'supplement.py'),script],cwd=repo,stdout=out,stderr=subprocess.STDOUT,timeout=90)
  name={'audit_early_scan.py':'EARLY_SCAN_AUDIT.json','audit_route_commitment.py':'ROUTE_COMMITMENT_AUDIT.json','audit_projection_learning.py':'PROJECTION_LEARNING_AUDIT.json','audit_all_tail_geometry.py':'SAVED_TAIL_GEOMETRY_AUDIT.json','audit_shadow_mode.py':'SHADOW_MODE_AUDIT.json','audit_field_discovery.py':'DISCOVERY_CHAIN_AUDIT_V699.json'}[script];a=read(root/script.removesuffix('.py')/name);failed=[k for k,v in a.get('checks',{}).items()if not v]
  assert r.returncode==(1 if script=='audit_field_discovery.py'else 0),'SUPPLEMENT_CRASH_OR_CHECK_FAILURE'
  if script=='audit_field_discovery.py':assert set(failed)=={'moving_before_discovery','new_causal_route_after_stop','actually_continued_after_replanning','strict_arrival'}
  else:assert not failed
  records.append(dict(script=script,status=a['status'],failed_checks=failed));dump('PROGRESS.json',records)
 window['status']='SAVED_EVIDENCE_COMPLETE_ORIGINAL_FUNCTIONAL_AND_AUDIT_FAILURES_RETAINED';assert all(sha(repo/n)==h for n,h in freeze['files'].items())
finally:window.update(round_closed=True,elapsed_s=time.time()-begun,records=records);dump('ROUND_WINDOW.json',window)
print(json.dumps(window))
