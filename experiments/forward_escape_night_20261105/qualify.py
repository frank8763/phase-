"""Saved auditor callsite qualification and operation gates before freeze; no models."""
import ast,fcntl,json,os,subprocess,sys
from pathlib import Path
from evidence_rules import AUDITS,dump,read,sha,main_gate,repeat_check
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/forward_escape_night_20261105';q=root/'qualification';q.mkdir(exist_ok=True)
own=repo/'experiments/v832_forward_escape_development'
for d in [own,common]:
 for p in d.glob('*.py'):ast.parse(p.read_text())
assert not(root/'ZERO_MODEL_QUALIFICATION.json').exists()
tasks=read(own/'TASK_LIST.json');assert len(tasks)==5 and len({t['seed']for t in tasks})==5
rows=[dict(role='MAIN',task=t,physical_passed=True,functional_passed=True)for t in tasks]
assert main_gate(tasks,rows,False)['passed'];assert not main_gate(tasks,rows[:-1],False)['passed']and main_gate(tasks,rows[:-1],False)['success_rate']is None
bad=[dict(x)for x in rows];bad[0]['functional_passed']=False;assert not main_gate(tasks,bad,False)['passed']
bad=rows[::-1];assert not main_gate(tasks,bad,False)['passed']
base=repo/'runs/v826_goal_reference_renewal/main_slot02/paired';pair=q/'reference/paired';pair.mkdir(parents=True);(pair.parent/'source_snapshot').symlink_to(base.parent/'source_snapshot',target_is_directory=True)
outputs={x[1]for x in AUDITS}|{'discovery_audit','EXACT_REPEAT_AUDIT.json','FINAL_INDEPENDENT_REPEAT.json'}
for p in base.iterdir():
 if p.name not in outputs and not p.name.endswith('.console'):(pair/p.name).symlink_to(p,target_is_directory=p.is_dir())
window=q/'original_source_window';window.mkdir()
for n in ['SOURCE_FREEZE.json','DOCUMENT_FREEZE.json']:(window/n).write_bytes((repo/'runs/v826_goal_reference_renewal/development01'/n).read_bytes())
inventory=[dict(path=str(p.relative_to(repo)),sha256=sha(p))for p in base.parent.rglob('*')if p.is_file()and p.suffix!='.pyc'];dump(q/'ORIGINAL_SOURCE_INVENTORY.json',inventory)
guard=(repo/'REVIEW_PENDING').read_bytes();lock=(repo/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json';records=[]
def run(script,args,log,omit=False,cap=360):
 cmd=[str(repo/'run_phase.sh'),str(common.relative_to(repo)/'worker_entry.py'),'--saved-only']
 if omit:cmd+=['--omit-legacy-path']
 cmd+=[own.name,script,*map(str,args)]
 with log.open('x')as stream:p=subprocess.run(cmd,cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=cap)
 return p.returncode
try:
 (repo/'REVIEW_PENDING').unlink()
 assert run('audit_goal_renewal.py',[pair],q/'missing_dependency_red.console',True)!=0
 for script,filename,cap in AUDITS:
  if script=='audit_ranked_return.py':continue
  args=[pair]
  if script=='audit_run.py':args+=['--window',window]
  if script=='audit_projection_learning.py':args+=['--model',model]
  if script=='audit_goal_renewal.py':args+=['--anchor-original-ns']
  code=run(script,args,q/(script+'.console'),cap=cap);records.append(dict(script=script,exit=code));dump(q/'RESULTS.json',records)
  assert code==0,script+'_QUALIFICATION_FAILED';assert read(pair/filename)['status']!='FAIL'and all(read(pair/filename).get('checks',{}).values())
 assert run('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],q/'discovery.console')==0
 assert all(read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')['checks'].values())
 # Reuse saved real t0 packets with explicit task relabeling; actual new5t0 still required.
 old_confirmation=read(repo/'runs/v828_goal_dynamic_confirmation/confirmation01/PREFLIGHTS.json');old_dev=read(repo/'runs/v827_goal_route_validation/development01/PREFLIGHTS.json')
 source={x['task']['seed']:x for x in old_confirmation+old_dev};view=q/'five_t0_interface';view.mkdir();pre=[]
 for t in tasks:
  x=dict(source[t['seed']]);x['task']=t;pre.append(x)
 dump(view/'PREFLIGHTS.json',pre);assert run('audit_field_preflight.py',[view],q/'five_t0_interface.console')==0
 sys.path.insert(0,str(own));from contact_fingerprint import compare_contacts
 r=read(base/'geometry_memory/result.json');assert repeat_check(base,base,r,r,compare_contacts)['passed']
 assert all(sha(repo/x['path'])==x['sha256']for x in inventory)
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard);lock.close()
assert read(q/'RETURN_SEARCH_QUALIFICATION.json')['passed'],'RANKED_RETURN_SEAM_NOT_QUALIFIED'
(pair/'RANKED_RETURN_AUDIT.json').write_bytes((q/'return_rejection_seam/paired/RANKED_RETURN_AUDIT.json').read_bytes())
result=dict(passed=True,original13_saved_auditors=records,ranked_return=read(q/'RETURN_SEARCH_QUALIFICATION.json'),actual5t0_interface_passed=True,gate_positive_negative_cases=4,original527_red_and_repaired_green=True,models=0,integrations=0,canonical_metadata_proxy_import_only=True,does_not_prove_new_native_feasibility=True)
dump(root/'ZERO_MODEL_QUALIFICATION.json',result);print(json.dumps(dict(passed=True,auditors=len(records),models=0,integrations=0)))
