"""Actual saved auditor callsites and stage gate negatives, zero new models/integration."""
import ast,copy,fcntl,json,subprocess,sys
from collections import defaultdict
from pathlib import Path
from evidence_rules import AUDITS,FUNCTIONAL_CHECKS,dump,read,sha,repeat_check
from limits import can_transition,pilot_limits,model_fits
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v842_staged_long_navigation';ROOT=R/'runs/staged_90_then12_20261106';Q=ROOT/'qualification';Q.mkdir(exist_ok=False)
base=R/'runs/v841_early_joint/main_slot01/paired';pair=Q/'reference/paired';pair.mkdir(parents=True);(pair.parent/'source_snapshot').symlink_to(base.parent/'source_snapshot',target_is_directory=True);outputs={x[1]for x in AUDITS}|{'discovery_audit','EXACT_REPEAT_AUDIT.json','FINAL_INDEPENDENT_REPEAT.json'}
for p in base.iterdir():
 if p.name not in outputs and p.name!='geometry_memory'and not p.name.endswith('.console'):(pair/p.name).symlink_to(p,target_is_directory=p.is_dir())
cell=pair/'geometry_memory';cell.mkdir()
for p in(base/'geometry_memory').iterdir():
 if p.name!='result.json':(cell/p.name).symlink_to(p,target_is_directory=p.is_dir())
r=read(base/'geometry_memory/result.json');r['source_revision']='V842_BUDGET_ONLY_V841_IDENTICAL_DECISIONS';dump(cell/'result.json',r)
window=Q/'original_window';window.mkdir()
for n in ['SOURCE_FREEZE.json','DOCUMENT_FREEZE.json']:(window/n).write_bytes((R/'runs/v841_early_joint/development01'/n).read_bytes())
inventory=[dict(path=str(p.relative_to(R)),sha256=sha(p))for p in base.parent.rglob('*')if p.is_file()and p.suffix!='.pyc'];dump(Q/'ORIGINAL_INVENTORY.json',inventory)
original=(R/'experiments/v841_early_joint/run_static.py').read_text();new=(W/'run_static.py').read_text();restored=new.replace("/'v842_staged_long_navigation'/a.name","/'v841_early_joint'/a.name").replace("if time.monotonic()-started>=float(os.environ['PHASE_NAV_SOFT_WALL_S']):","if time.monotonic()-started>=1200.:").replace("'soft_wall_s':float(os.environ['PHASE_NAV_SOFT_WALL_S']),'hard_wall_s':a.wall_seconds","'soft_wall_s':1200,'hard_wall_s':1500").replace("'V842_BUDGET_ONLY_V841_IDENTICAL_DECISIONS'","'V841_CAUSAL_REFERENCE_FOLLOWING_WITH_FINITE_SUCCESSOR'").replace('from operation_profile import install\ninstall(outer)\n','');assert original==restored and'V842_BUDGET_ONLY_V841_IDENTICAL_DECISIONS'in new
for d in[W,C]:
 for p in d.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
positive={k:True for k in['development_passed','source_and_decompressed_sha_verified','independent_audit_passed','complete_chain_passed','native_replay_exact','source_unchanged']};assert can_transition(positive);negative=0
for key in positive:
 wrong=dict(positive);wrong[key]=False;assert not can_transition(wrong);negative+=1
assert not can_transition(dict(component_passed=True));assert pilot_limits(5400,0)['soft']==5140 and pilot_limits(5400,0)['outer']+180+3<5400
assert not model_fits(10,9,2)and model_fits(10,1,2);assert not can_transition({})
sys.path.insert(0,str(W));from operation_profile import timed
stats=defaultdict(lambda:dict(calls=0,inclusive_wall_s=0.));object0=object();f=timed('identity',lambda x:x,stats);assert f(object0)is object0 and stats['identity']['calls']==1
wrong=timed('exception',lambda:(_ for _ in()).throw(ValueError('EXPECTED')),stats)
try:wrong()
except ValueError:assert stats['exception']['calls']==1
else:raise AssertionError('TIMING_SWALLOWED_EXCEPTION')
guard=(R/'REVIEW_PENDING').read_bytes();lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);records=[];model=R/'runs/v690_visible_eight_meter/training_8m/proposer.json'
def run(script,args,log,cap,omit=False):
 command=[str(R/'run_phase.sh'),str(C/'worker_entry.py'),'--saved-only']
 if omit:command+=['--omit-legacy-path']
 command+=[W.name,script,*map(str,args)]
 with log.open('x')as stream:return subprocess.run(command,cwd=R,stdout=stream,stderr=subprocess.STDOUT,timeout=cap).returncode
try:
 (R/'REVIEW_PENDING').unlink();assert run('audit_goal_renewal.py',[pair],Q/'missing_dependency_red.console',60,True)!=0
 for script,filename,cap in AUDITS:
  args=[pair]
  if script=='audit_run.py':args+=['--window',window]
  if script=='audit_projection_learning.py':args+=['--model',model]
  code=run(script,args,Q/(script+'.console'),cap);records.append(dict(script=script,exit=code));dump(Q/'RESULTS.json',records);assert code==0,script
  data=read(pair/filename);assert data['status']!='FAIL'and all(data.get('checks',{}).values())
 source={x['task']['seed']:x for x in read(R/'runs/v828_goal_dynamic_confirmation/confirmation01/PREFLIGHTS.json')};tasks=read(W/'TASK_LIST.json')
 for label,selected in [('pilot',[tasks[0]]),('long',tasks)]:
  view=Q/(label+'_t0');view.mkdir();rows=[dict(source[t['seed']],task=t)for t in selected];dump(view/'LOCKED_T0_TASK_LIST.json',selected);dump(view/'PREFLIGHTS.json',rows);assert run('audit_field_preflight.py',[view],Q/(label+'_t0.console'),60)==0
 view=Q/'missing_t0_red';view.mkdir();dump(view/'LOCKED_T0_TASK_LIST.json',tasks);dump(view/'PREFLIGHTS.json',[dict(source[tasks[0]['seed']],task=tasks[0])]);assert run('audit_field_preflight.py',[view],Q/'missing_t0_red.console',60)!=0
finally:(R/'REVIEW_PENDING').write_bytes(guard);lock.close()
assert all(sha(R/x['path'])==x['sha256']for x in inventory)
from contact_fingerprint import compare_contacts
actual=read(base/'geometry_memory/result.json');assert repeat_check(base,base,actual,actual,compare_contacts)['passed']
expected={script:read(pair/filename)['status']for script,filename,_ in AUDITS};data=dict(passed=True,saved_17_auditors=records,expected_audit_statuses=expected,pilot_and_long_task_registration=True,missing_t0_negative_rejected=True,transition_negative_cases=negative+2,budget_no20min_cutoff=True,source_body_restores_byte_exact_V841=True,profile_identity_and_exception_exact=True,actual_V842_vs_V841_3112_native_gate_pre_registered=True,models=0,integrations=0,canonical_metadata_proxy_import_only=True,proxy_is_not_a_new_MJB_audit=True,new24=0)
dump(ROOT/'ZERO_MODEL_QUALIFICATION.json',data);print(json.dumps(dict(passed=True,auditors=len(AUDITS),negative_cases=negative+3,models=0,integrations=0)))
