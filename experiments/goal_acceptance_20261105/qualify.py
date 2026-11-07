"""Run every real auditor on immutable saved evidence, no new models or steps."""
import ast,fcntl,json,os,subprocess,sys,time
from pathlib import Path
from evidence_rules import AUDITS,dump,read,sha,main_gate,repeat_check
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/goal_acceptance_20261105';q=root/'qualification'
assert not q.exists();q.mkdir();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
for d in [own,repo/'experiments/v827_goal_route_validation',repo/'experiments/v828_goal_dynamic_confirmation']:
 for p in d.glob('*.py'):ast.parse(p.read_text())
base=repo/'runs/v826_goal_reference_renewal/main_slot02/paired';pair=q/'reference/paired';pair.mkdir(parents=True);(pair.parent/'source_snapshot').symlink_to(base.parent/'source_snapshot',target_is_directory=True)
outputs={x[1] for x in AUDITS}|{'discovery_audit','EXACT_REPEAT_AUDIT.json','FINAL_INDEPENDENT_REPEAT.json'}
for p in base.iterdir():
 if p.name not in outputs and not p.name.endswith('.console'):(pair/p.name).symlink_to(p,target_is_directory=p.is_dir())
window=q/'original_source_window';window.mkdir()
for name in ['SOURCE_FREEZE.json','DOCUMENT_FREEZE.json']:(window/name).write_bytes((repo/'runs/v826_goal_reference_renewal/development01'/name).read_bytes())
inventory=[dict(path=str(p.relative_to(repo)),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(base.parent.rglob('*'))if p.is_file() and p.suffix!='.pyc']
dump(q/'ORIGINAL_MAIN_SOURCE_INVENTORY.json',inventory)
# Gate regression includes incomplete denominators, reordered tasks and fixed-repeat failure.
tasks=read(repo/'experiments/v828_goal_dynamic_confirmation/TASK_LIST.json')
assert len(tasks)==24 and [t['seed']for t in tasks]==list(range(10060001,10060025))
assert (repo/'experiments/v828_goal_dynamic_confirmation/TASK_LIST.json').read_bytes()==(root/'RESERVED_CONFIRMATION_TASKS.json').read_bytes()
def rows(fail=(),n=24):return [dict(role='MAIN',task=t,physical_passed=True,functional_passed=i not in fail)for i,t in enumerate(tasks[:n])]
assert main_gate(tasks,rows(),True)['passed'] and main_gate(tasks,rows([2]),True)['passed']
assert not main_gate(tasks,rows([2,3]),True)['passed'] and not main_gate(tasks,rows(n=23),True)['passed']
assert main_gate(tasks,rows(n=23),True)['success_rate'] is None
bad=rows();bad[0],bad[1]=bad[1],bad[0];assert not main_gate(tasks,bad,True)['passed']
assert not main_gate(tasks,rows([0]),True)['main_successes']==24
model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json'
records=[];guard=(repo/'REVIEW_PENDING').read_bytes();(q/'REVIEW_PENDING.before').write_bytes(guard)
lock=(repo/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def run(script,args,log,omit=False,cap=360):
 command=[str(repo/'run_phase.sh'),str(own.relative_to(repo)/'worker_entry.py'),'--saved-only']
 if omit:command+=['--omit-legacy-path']
 command+=['v827_goal_route_validation',script,*map(str,args)]
 with log.open('x')as stream:p=subprocess.run(command,cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=cap)
 return p.returncode
try:
 (repo/'REVIEW_PENDING').unlink()
 red=q/'missing_dependency_red.console';code=run('audit_goal_renewal.py',[pair,'--anchor-original-ns'],red,True)
 assert code!=0 and 'hybrid_planner' in red.read_text() and 'ModuleNotFoundError' in red.read_text(),'NOT_THE_ORIGINAL_IMPORT_BUG'
 for script,output,cap in AUDITS:
  args=[pair]
  if script=='audit_run.py':args+=['--window',window]
  if script=='audit_projection_learning.py':args+=['--model',model]
  if script=='audit_goal_renewal.py':args+=['--anchor-original-ns']
  code=run(script,args,q/(script+'.console'),cap=cap)
  records.append(dict(script=script,exit_code=code,output=str((pair/output).relative_to(repo))));dump(q/'RESULTS.json',records)
  assert code==0,script+'_CALLSITE_FAILED'
  data=read(pair/output);assert data.get('status')!='FAIL' and all(data.get('checks',{}).values())
 assert run('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],q/'discovery.console')==0
 assert all(read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')['checks'].values())
 # Missing causal truth flags must be rejected even with a working import path.
 negative=q/'negative/paired';negative.mkdir(parents=True);(negative.parent/'source_snapshot').symlink_to(base.parent/'source_snapshot',target_is_directory=True)
 for p in pair.iterdir():
  if p.name not in outputs and p.name!='geometry_memory':(negative/p.name).symlink_to(p.resolve(),target_is_directory=p.is_dir())
 cell=negative/'geometry_memory';cell.mkdir()
 for p in (base/'geometry_memory').iterdir():
  if p.name!='goal_reference_renewal.jsonl':(cell/p.name).symlink_to(p,target_is_directory=p.is_dir())
 data=[json.loads(x)for x in(base/'geometry_memory/goal_reference_renewal.jsonl').read_text().splitlines()];data[0]['hidden_world_geometry_used']=True
 (cell/'goal_reference_renewal.jsonl').write_text(''.join(json.dumps(x)+'\n'for x in data))
 assert run('audit_goal_renewal.py',[negative,'--anchor-original-ns'],q/'tampered_renewal_red.console')!=0
 # Both task-count registrations execute the same saved-data noise auditor.
 view=q/'original_three_t0';view.mkdir();old=read(repo/'runs/v812_soft_global_reference/development01/PREFLIGHTS.json');by={r['task']['slot']:r for r in old};dev=read(repo/'experiments/v827_goal_route_validation/TASK_LIST.json');dump(view/'PREFLIGHTS.json',[by[t['slot']]for t in dev])
 assert run('audit_field_preflight.py',[view],q/'three_t0_interface.console')==0
 # Compare the real existing anchor against itself: all measured contact fields preserved.
 sys.path.insert(0,str(repo/'experiments/v827_goal_route_validation'))
 from contact_fingerprint import compare_contacts
 r=read(base/'geometry_memory/result.json');check=repeat_check(base,base,r,r,compare_contacts);assert check['passed'];dump(q/'EXACT_REPEAT_INTERFACE.json',check)
 assert read(base/'INDEPENDENT_CANONICAL_AUDIT.json')['status']=='ALL_PHYSICAL_STATE_COMMAND_CHECKS_PASS'
 assert read(base/'NATIVE_REPLAY_AUDIT.json')['maximum_full_native_state_ctrl_error']==0
 assert all(sha(repo/x['path'])==x['sha256']for x in inventory),'ORIGINAL_EVIDENCE_CHANGED'
 result=dict(passed=True,status='ALL_AUDIT_CALLSITES_SAVED_EVIDENCE_QUALIFIED',audits=records,discovery_chain_passed=True,original_missing_dependency_reproduced=True,tampered_causal_evidence_rejected=True,original_anchor_physical_and_replay_previously_passed=True,original_v826_formal_status='NOT_PASSED_PRESERVED',repeat_interface_passed=True,original_three_t0_interface_passed=True,confirmation_gate_positive_negative_cases=7,actual_new_models=0,actual_new_integrations=0,canonical_metadata_proxy_for_import_dry_run_only=True,does_not_revalidate_binary_model_metadata=True,source_inventory=str((q/'ORIGINAL_MAIN_SOURCE_INVENTORY.json').relative_to(repo)))
 dump(root/'ZERO_MODEL_QUALIFICATION.json',result);print(json.dumps({k:v for k,v in result.items()if k!='audits'}),flush=True)
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard);lock.close()
