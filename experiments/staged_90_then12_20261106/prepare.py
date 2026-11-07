"""Model-free staging of budget-only V841 continuation; never edits a frozen source."""
import ast,hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v842_staged_long_navigation';S=R/'experiments/v841_early_joint';O=R/'runs/staged_90_then12_20261106'
assert not W.exists();W.mkdir()
for p in S.iterdir():
 if p.is_file()and((p.suffix=='.py'and not p.name.startswith('qualify_')and p.name not in ['helpers.py','execute.py','finalize.py'])or p.name in ['SCENE_CASES.json','KNOWN_FIELD.json']):shutil.copyfile(p,W/p.name)
for name in ['evidence_rules.py','worker_entry.py','hold_awake.py']:shutil.copyfile(R/'experiments/early_joint_90_20261106'/name,C/name)
p=C/'hold_awake.py';p.write_text(p.read_text().replace('early_joint_90_20261106','staged_90_then12_20261106'))
tasks=json.loads((R/'experiments/v828_goal_dynamic_confirmation/TASK_LIST.json').read_text());chosen=[dict(t,role='KNOWN_FAILURE_DEVELOPMENT')for t in tasks if t['seed']in[10060002,10060008]];assert len(chosen)==2
(W/'TASK_LIST.json').write_text(json.dumps(chosen,indent=2)+'\n')
p=W/'run_static.py';s=p.read_text().replace("/'v841_early_joint'/a.name","/'v842_staged_long_navigation'/a.name").replace("if time.monotonic()-started>=1200.:","if time.monotonic()-started>=float(os.environ['PHASE_NAV_SOFT_WALL_S']):").replace("'soft_wall_s':1200,'hard_wall_s':1500","'soft_wall_s':float(os.environ['PHASE_NAV_SOFT_WALL_S']),'hard_wall_s':a.wall_seconds").replace("'V841_CAUSAL_REFERENCE_FOLLOWING_WITH_FINITE_SUCCESSOR'","'V842_BUDGET_ONLY_V841_IDENTICAL_DECISIONS'")
needle="started=time.monotonic()";assert s.count(needle)==1;s=s.replace(needle,"from operation_profile import install\ninstall(outer)\n"+needle);p.write_text(s)
p=W/'audit_field_preflight.py';s=p.read_text().replace("tasks=read(Path(__file__).parent/'DEVELOPMENT_TASKS.json');assert", "tasks=read(window/'LOCKED_T0_TASK_LIST.json');registered=read(Path(__file__).parent/'TASK_LIST.json');assert tasks and all(t in registered for t in tasks);assert").replace('len(details)==len(tasks)==1','len(details)==len(tasks)>0').replace('One preregistered original WEST_EAST development route','Registered original known-failure tasks');p.write_text(s)
# Existing complete joint certificate checks remain; task-specific prefix and causal trigger checks replace a single-task constant.
p=W/'audit_early_joint.py';s=p.read_text();a=s.index('prefix=0;error=0.');b=s.index('out=dict(',a)
s=s[:a]+'''prefix=0;error=0.;budget_prefix=0;budget_error=0.
repo=Path(__file__).resolve().parents[2];result=read(cell/'result.json');seed=result['seed'];states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')}
if starts:
    assert len(starts)==1
    if result['source_revision'].startswith('V842')or result['source_revision'].startswith('V841'):
        eligible=[step for step in sorted(nom)if step>0 and states[step]['center']is not None and ad.get(step-1,{}).get('recovery_reserve',{}).get('reserve_minimum_clearance_m',float('inf'))<.155+.08*3.28]
        assert eligible and starts[0]['step']==eligible[0],'FIRST_CAUSAL_TRIGGER_NOT_EXACT'
    anchors={10060002:'runs/v830_ranked_return_development/main_slot01/paired/geometry_memory',10060008:'runs/v828_goal_dynamic_confirmation/main_slot08/paired/geometry_memory'}
    assert seed in anchors,'UNREGISTERED_PREFIX_ANCHOR'
    first=starts[0]['step'];old=repo/anchors[seed]
    with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as aa,gzip.open(old/'dynamic_native.jsonl.gz','rt')as bb:
        for i,(x,y)in enumerate(zip(aa,bb)):
            if i>=first*8:break
            x,y=json.loads(x),json.loads(y);error=max(error,max(float(np.max(abs(np.asarray(x[k])-y[k])))for k in['qpos_full','qvel_full','actual_ctrl','mocap_pos']));prefix+=1
    assert prefix==first*8 and error<=1e-8
if seed==10060002 and result['source_revision'].startswith('V842'):
    old=repo/'runs/v841_early_joint/main_slot01/paired/geometry_memory';expected=min(result['physics_steps'],3112)
    with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as aa,gzip.open(old/'dynamic_native.jsonl.gz','rt')as bb:
        for i,(x,y)in enumerate(zip(aa,bb)):
            if i>=expected:break
            x,y=json.loads(x),json.loads(y);budget_error=max(budget_error,max(float(np.max(abs(np.asarray(x[k])-y[k])))for k in['qpos_full','qvel_full','actual_ctrl','mocap_pos']));budget_prefix+=1
    assert budget_prefix==expected and budget_error<=1e-8,'BUDGET_ONLY_CONTROLS_OR_STATES_CHANGED'
''' +s[b:]
s=s.replace("pre_trigger_error=error,new_models", "pre_trigger_error=error,budget_only_native_prefix=budget_prefix,budget_only_native_error=budget_error,new_models");p.write_text(s)
# Immutable registration; no absolute model start is claimed at preparation time.
auth=dict(user_instruction='90分钟的开始；通过之后再开启12小时的',stage1_model_window_s=5400,stage2_model_window_s=43200,stage1_absolute_deadline_unix=None,stage2_start_only_after_pilot_full_chain_17audits_replay_and_SHA_finalized=True,stage1_tasks=[10060002],stage2_order=['repeat10060002','main10060008','conditional_repeat10060008'],scientific_algorithm='V841_UNCHANGED',scientific_revisions=0,first_functional_or_safety_or_evidence_failure_stops=True,post_freeze_repairs=0,new_confirmation=0,private_native_cap_per_navigation=100000000,training=0,SAC=0,Stage_access=0,real_robot=0,subagents=0,new_chats=0,network=0,old_failures_and_deadlines_immutable=True)
(R/'RPCCR_STAGED_90_THEN12_AUTHORIZATION_20261106.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2)+'\n');(O/'LEDGER.json').write_text(json.dumps(dict(status='PREPARING_ZERO_MODEL',closed=False,stage1_started=False,stage2_started=False,scientific_revisions=0),indent=2)+'\n')
allowed={'run_static.py','audit_field_preflight.py','audit_early_joint.py'};differences=[]
for p in W.glob('*.py'):
 same=hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256((S/p.name).read_bytes()).hexdigest()
 if not same:assert p.name in allowed;differences.append(p.name)
(O/'DECISION_PRESERVATION_REGISTRATION.json').write_text(json.dumps(dict(passed=True,changed_existing_files=differences,scientific_files_unchanged=[p.name for p in W.glob('*.py')if p.name not in allowed],instrumentation_scope='Timers and serialization timing only; full first3112 native replay against V841 required in actual pilot audit.',models=0,integrations=0),indent=2)+'\n')
for d in[W,C]:
 for p in d.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
print('BUDGET_ONLY_TWO_STAGE_PREPARATION_COMPLETE_NO_MODELS')
