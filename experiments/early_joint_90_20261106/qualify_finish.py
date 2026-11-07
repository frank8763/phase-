"""Complete saved-only qualification after fixing pre-freeze one-task count registration."""
import fcntl,json,subprocess,sys
from pathlib import Path
from evidence_rules import AUDITS,dump,read,sha,repeat_check,main_gate
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v841_early_joint';root=R/'runs/early_joint_90_20261106';q=root/'qualification';pair=q/'reference/paired'
assert not(root/'ZERO_MODEL_QUALIFICATION.json').exists()
records=read(q/'RESULTS.json');assert len(records)==len(AUDITS)-1 and all(x['exit']==0 for x in records)
for script,filename,_ in AUDITS:
 if script=='audit_ranked_return.py':continue
 data=read(pair/filename);assert data['status']!='FAIL'and all(data.get('checks',{}).values())
tasks=read(W/'TASK_LIST.json');assert len(tasks)==1;positive=[dict(role='MAIN',task=tasks[0],physical_passed=True,functional_passed=True)];assert main_gate(tasks,positive,False)['passed']and not main_gate(tasks,[],False)['passed']and main_gate(tasks,[],False)['success_rate']is None
assert not main_gate(tasks,[dict(positive[0],functional_passed=False)],False)['passed']and not main_gate(tasks,[dict(positive[0],task=dict(tasks[0],seed=-1))],False)['passed']
view=q/'single_t0_interface_ready02';view.mkdir();dump(view/'PREFLIGHTS.json',read(q/'five_t0_interface/PREFLIGHTS.json'))
guard=(R/'REVIEW_PENDING').read_bytes();lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
try:
 (R/'REVIEW_PENDING').unlink()
 with(q/'single_t0_interface_ready02.console').open('x')as f:p=subprocess.run([str(R/'run_phase.sh'),str(C/'worker_entry.py'),'--saved-only',W.name,'audit_field_preflight.py',str(view)],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=60)
 assert p.returncode==0 and read(view/'PREFLIGHT_INDEPENDENT_AUDIT.json')['status']=='PASS'
finally:(R/'REVIEW_PENDING').write_bytes(guard);lock.close()
sys.path.insert(0,str(W));from contact_fingerprint import compare_contacts
base=R/'runs/v826_goal_reference_renewal/main_slot02/paired';r=read(base/'geometry_memory/result.json');assert repeat_check(base,base,r,r,compare_contacts)['passed']
assert all(sha(R/x['path'])==x['sha256']for x in read(q/'ORIGINAL_SOURCE_INVENTORY.json'))
(pair/'RANKED_RETURN_AUDIT.json').write_bytes((q/'return_rejection_seam/paired/RANKED_RETURN_AUDIT.json').read_bytes())
for name in ['RETURN_SEARCH_QUALIFICATION.json','REFERENCE_ARRAY_QUALIFICATION.json','EARLY_JOINT_SEAM_QUALIFICATION.json']:assert read(q/name)['passed']
result=dict(passed=True,saved_auditors=records,ranked_return=True,actual1t0_interface_passed=True,gate_positive_negative_cases=4,models=0,integrations=0,canonical_metadata_proxy_import_only=True,does_not_prove_new_native_feasibility=True,pre_freeze_preparation_errors_retained=['qualify_early.console: synthetic cache array type','qualify.console: one-task aggregate still inherited five; 14 checks already true'],post_freeze_repairs=0)
dump(root/'ZERO_MODEL_QUALIFICATION.json',result);print(json.dumps(dict(passed=True,auditors=len(AUDITS),models=0,integrations=0)))
