"""Prepare one early intervention candidate, one known main and conditional repeat."""
import ast,json,fcntl
from pathlib import Path
from datetime import datetime
repo=Path(__file__).resolve().parents[1]
common=repo/'experiments/early_joint_90_20261106';worker=repo/'experiments/v841_early_joint';ops=repo/'runs/early_joint_90_20261106';stage=repo/'runs/v841_early_joint'
assert all(not p.exists()for p in[common,worker,ops,stage])and(repo/'REVIEW_PENDING').exists()
with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
for p in[common,worker,ops,stage]:p.mkdir()
oldcommon=repo/'experiments/reference_differential_20261106';oldscience=repo/'experiments/v839_reference_differential_development';oldqual=repo/'experiments/v838_reference_differential_qualification'
replacements=[('reference_differential_20261106','early_joint_90_20261106'),('v838_reference_differential_qualification','v841_early_joint'),('v839_reference_differential_development','v841_early_joint'),('RPCCR_REFERENCE_DIFFERENTIAL_AUTHORIZATION_20261106.json','RPCCR_EARLY_JOINT_90_AUTHORIZATION_20261106.json'),('RPCCR_REFERENCE_DIFFERENTIAL_20261106','RPCCR_EARLY_JOINT_90_20261106'),('RPCCR_REFERENCE_DIFFERENTIAL_V838','RPCCR_EARLY_JOINT_V841_QUALIFICATION'),('RPCCR_REFERENCE_DIFFERENTIAL_V839','RPCCR_EARLY_JOINT_V841'),('V838','V841'),('V839','V841'),('v838','v841')]
for source,target in[(oldcommon,common),(oldscience,worker)]:
 for p in source.iterdir():
  if not p.is_file()or p.suffix not in['.py','.md','.json']or p.name in['CANDIDATE_FREEZE.json','INPUT_FREEZE.json','freeze.py','launch.py','campaign.py','component.py','prepare_schedule.py','configure_component.py','configure_component_audit.py','configure_science.py']:continue
  text=p.read_text()
  for a,b in replacements:text=text.replace(a,b)
  (target/p.name).write_text(text)
for name in['helpers.py','probe.py','audit_saved.py','finalize.py']:
 text=(oldqual/name).read_text()
 for a,b in replacements:text=text.replace(a,b)
 (worker/('qualify_'+name if name!='helpers.py'else'helpers.py')).write_text(text)
cell=repo/'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory'
ad={x['step']:x for x in map(json.loads,(cell/'model_admission.jsonl').open())};states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').open())}
plans=[json.loads(p.read_text())for p in cell.glob('planning_*.json')];decisions=[json.loads(x)for x in(cell/'control_decisions.jsonl').open()]
for step in sorted(ad):
 previous=ad.get(step-1,{}).get('recovery_reserve',{});margin=previous.get('reserve_minimum_clearance_m')
 if margin is None or margin>=.155+.08*3.28 or states[step]['center']is None or ad[step]['status']!='MODEL_SAFE_COMMAND':continue
 plan=max([p for p in plans if p['step']<=step],key=lambda p:p['step'])
 if plan['path']is None or ad[step]['active_gear']!=1:continue
 break
else:raise AssertionError('NO_ORIGINAL_PRE_FAILURE_GUARD_STATE')
assert step<490 and step==295
nominal=next(x for x in decisions if x['step']==step and x['candidate_role']=='ORDINARY'and x['stage']=='NOMINAL')
fixture=dict(step=step,state={k:v for k,v in states[step].items()if k!='step'},nominal=nominal,
 reference_source=f'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory/planning_{plan["step"]:04d}.json',
 reference=dict(path=plan['path'],index=0,goal_xy=[4.,-2.],wheel_base=.60),
 previous_reserve_minimum_m=margin,previous_step=step-1,previous_certificate=f'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory/ordinary_certificates/certificate_{step-1:04d}.npz',
 original_certificate=f'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory/ordinary_certificates/certificate_{step:04d}.npz',
 selection_rule='First tracked forward ordinary state whose previous accepted reserve lower bound is less than .155+.08*3.28; no posthoc replacement.')
dump=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
dump(worker/'FIXED_INPUTS.json',[fixture])
task=json.loads((oldscience/'TASK_LIST.json').read_text())[0];assert task['seed']==10060002
for name in['TASK_LIST.json','DEVELOPMENT_TASKS.json']:dump(worker/name,[task])
cfg=json.loads((oldscience/'BATCH.json').read_text());cfg.update(label=worker.name,output='runs/v841_early_joint',window='development01',confirmation=False,batch_cap_s=5400,minimum_start_budget_s=3000,repeat_slots=[1],report='docs/RPCCR_EARLY_JOINT_V841_REPORT.md',archive='evidence/rpccr_early_joint_v841_20261106',reference_view='runs/early_joint_90_20261106/qualification/reference/paired',absolute_deadline_unix=None)
dump(worker/'BATCH.json',cfg)
auth=dict(user_instruction='90分钟的',prior_question_choice='A:90分钟模型预算，集中验证一个原失败场景及成功后的完整重复',authorized_at=datetime.now().astimezone().isoformat(),model_window_s=5400,model_window_started_unix=None,absolute_deadline_unix=None,deadline_set_once_before_model=True,max_scientific_candidates=1,post_freeze_repairs=0,
 native_qualification_state=step,qualification_model_cap_s=600,qualification_private_cap=200000,old_replay_native=step*8,qualification_actual_native=336,qualification_repeat_native=336,
 guard_formula='.155+.08*3.28',guard_m=.4174,nominal_joint_probes_max=4,original_reference_tail_library=18,
 complete_main_max=1,complete_repeat_max=1,seed=10060002,phase=task['phase'],case_id=task['case_id'],new_confirmation=0,
 no_late_state_rescue_requirement=True,old_failures_and_deadlines_immutable=True,training=0,SAC=0,real_robot=0,Stage_access=0,subagents=0,new_chats=0,network=0)
dump(repo/'RPCCR_EARLY_JOINT_90_AUTHORIZATION_20261106.json',auth)
dump(ops/'LEDGER.json',dict(status='PREPARING',closed=False,active_simulation=False,model_window_s=5400,candidates_started=0))
# Single-scene gate preserves exact fixed ordering and explicit incomplete denominator.
p=common/'evidence_rules.py';s=p.read_text().replace("len(successful) == len(tasks) == 5", "len(successful) == len(tasks) == 1");p.write_text(s)
# Only new ordinary variable-control tails use their separately saved full cache.
p=worker/'audit_nominal_layers.py';s=p.read_text().replace("    assert np.array_equal(command.sequence(z['target'],z['prefix_command'],320,int(z['brake_after'])),z['controls'])", "    saved=cell/'successor_certificates'/f'certificate_{step:04d}.json.gz'\n    if saved.exists():\n        import gzip\n        c=json.load(gzip.open(saved,'rt'))\n        if 'reference_following'in c:\n            from reference_certificate_audit import expected_follow\n            expected=expected_follow(c,np.asarray(contract['limits']),command.rate)\n        else:expected=command.sequence(z['target'],z['prefix_command'],320,int(z['brake_after']))\n    else:expected=command.sequence(z['target'],z['prefix_command'],320,int(z['brake_after']))\n    assert np.array_equal(expected,z['controls'])")
p.write_text(s)
for d in[common,worker]:
 for p in d.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
print('PREPARED_ONE_EARLY_JOINT_CANDIDATE_FIXED_STATE',step,'ONE_MAIN_SEED',task['seed'])
