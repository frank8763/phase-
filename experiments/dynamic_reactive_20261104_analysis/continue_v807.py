"""One last audit-cardinality interface correction, no scientific change/deadline reset."""
import ast,hashlib,json,pathlib,shutil
repo=pathlib.Path(__file__).resolve().parents[2];old=repo/'experiments/v806_sensor_activated_dynamic';own=repo/'experiments/v807_reactive_single_task_continuation';root=repo/'runs/v807_reactive_single_task_continuation';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not own.exists();assert read(repo/'runs/v806_sensor_activated_dynamic/FINALIZED.json')['development_passed']is False
assert not read(repo/'runs/v806_sensor_activated_dynamic/development01/COMPLETION.json')['records']
own.mkdir();root.mkdir()
for p in old.iterdir():
 if p.suffix in ['.py','.json','.md']and p.name!='CANDIDATE_FREEZE.json':(own/p.name).write_text(p.read_text().replace('v806_sensor_activated_dynamic','v807_reactive_single_task_continuation'))
p=own/'audit_field_preflight.py';s=p.read_text();assert s.count('len(details)==len(tasks)==3')==1;s=s.replace('len(details)==len(tasks)==3','len(details)==len(tasks)==1').replace('Three original development routes','One preregistered original development route');p.write_text(s)
p=own/'execute_development.py';s=p.read_text();start=s.index(' for t in tasks:\n');end=s.index(" for role in ['MAIN_DEVELOPMENT'",start)
s=s[:start]+''' # Reuse the unchanged zero-integration t0; never repeat initialization.
 preflights=read(repo/'runs/v806_sensor_activated_dynamic/development01/PREFLIGHTS.json')
 assert [x['task']for x in preflights]==tasks
 dump(window/'PREFLIGHTS.json',preflights)
 assert execute('audit_field_preflight.py',[window],window/'noise_audit.console',60)==0,'T0_SENSOR_NOISE_FAILED'
'''+s[end:]
p.write_text(s)
p=own/'finalize_development.py';s=p.read_text().replace('rpccr_sensor_activated_dynamic_v806_20261104','rpccr_reactive_continuation_v807_20261104').replace('RPCCR_SENSOR_ACTIVATED_V806_REPORT.md','RPCCR_REACTIVE_CONTINUATION_V807_REPORT.md').replace('RP-CCR V806','RP-CCR V807');p.write_text(s)
p=own/'PROTOCOL.md';s=p.read_text().replace('V806','V807').replace('原WEST_EAST/10010001/相位0','原WEST_EAST/10010001/原相位0.6573753567727383');s+='\n## 单任务审核接口接续\nV806模型和t0全部14项检查已通过，但继承的审核总数仍写死三路线，故原STOPPED_EXCEPTION/原源码/FINALIZED=NOT_PASSED永久保持，实际导航/私有/重放0。V807只将总数校验三改为已事前注册的一，复用V806原t0字节，不重初始化；控制器/场景/传感/风险变化与任务全部不改。沿用V806原绝对截止1793805252.794241，不增加任何物理导航名额。明确这是对原冻结后零夹具修正计划的一次审核接口接续；再出现任何初始化/审核接口异常即终止，不继续克隆修补。原首次启动台账错误亦永久保留。\n';p.write_text(s)
auth=dict(reason='Original one task t0 has every sensor/model/geometry/causal check true, inherited audit aggregate hardcoded three tasks. Change only cardinality to preregistered one, reuse original t0, no controller change.',original_failure='runs/v806_sensor_activated_dynamic/development01/ERROR.json',original_finalized='runs/v806_sensor_activated_dynamic/FINALIZED.json',absolute_deadline_unix=read(repo/'RPCCR_SENSOR_ACTIVATED_AUTHORIZATION_20261104.json')['absolute_deadline_unix'],additional_navigation_allowance=0,original_main_and_conditional_repeat_still_unexecuted=True,no_further_interface_retry=True,scope='One explicit last audit interface exception within current user dynamic continuation, not a second algorithm candidate')
(repo/'RPCCR_SENSOR_ACTIVATED_SINGLE_TASK_CONTINUATION_20261104.json').write_text(json.dumps(auth,indent=2)+'\n')
q=root/'pre_navigation';q.mkdir();shutil.copy2(repo/'runs/v806_sensor_activated_dynamic/pre_navigation/RESULT.json',q/'RESULT.json')
for p in own.glob('*.py'):ast.parse(p.read_text())
# Record and verify exact scientific modules and only output namespaces in the runner.
mods=['motion_tracker.py','dynamic_scene.py','scene_sensors.py','discovery_brake.py','future_guide.py','serial_predictor.py','reserved_recovery.py','joint_admission.py','recovery_supervisor.py','rejection_witness.py']
assert all((own/n).read_bytes()==(old/n).read_bytes()for n in mods)
assert (own/'run_static.py').read_text().replace('v807_reactive_single_task_continuation','v806_sensor_activated_dynamic')==(old/'run_static.py').read_text()
(root/'PRE_NAV_EQUIVALENCE.json').write_text(json.dumps({'status':'SAME_SCIENTIFIC_CANDIDATE', 'byte_identical_scientific_modules':mods,'runner_only_output_namespace_changes':True,'additional_initializations':0,'original_phase':0.6573753567727383,'t0_reused':True},indent=2)+'\n')
f=repo/'RPCCR_SENSOR_ACTIVATED_LEDGER_20261104.json';d=read(f);d.update(status='V807_SAME_CANDIDATE_AUDIT_CARDINALITY_CONTINUATION',nav_started=0,failed_t0_audit_cardinality=1,interface_corrections_after_freeze=1,original_v806_failure_preserved=True,continuation='RPCCR_SENSOR_ACTIVATED_SINGLE_TASK_CONTINUATION_20261104.json');f.write_text(json.dumps(d,indent=2)+'\n')
for n in ['AGENTS.md','RESEARCH_STATUS.md']:
 p=repo/n;p.write_text(p.read_text()+'\n- V806原单t0各14项审核全真但继承总数写死3，原STOPPED_EXCEPTION/FINALIZED NOT_PASSED保存、导航私有重放0。V807仅三改原注册一的审核接口接续，复用t0不再初始化，所有科学模块字节不变/runner只输出namespace变，原相位0.6573753567727383（V806协议误写0现纠正说明）、原绝对截止1793805252.794241不变。原一个主和成功条件重复均未执行，不增加导航额度；再有任何接口异常停止，不继续克隆修补。先读V807协议。\n')
f=repo/'CURRENT_EXPERIMENT.json';d=read(f);d.update(current_experiment='V807_SAME_REACTIVE_CANDIDATE_SINGLE_TASK_AUDIT_CONTINUATION',status='V807_READY',state='V807_READY');d['sensor_activated_dynamic']['continuation_protocol']=str((own/'PROTOCOL.md').relative_to(repo));f.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
files={k:v for k,v in read(old/'CANDIDATE_FREEZE.json')['files'].items()if not k.startswith('experiments/v806_sensor_activated_dynamic/')}
for p in own.iterdir():
 if p.suffix in ['.py','.md','.json']:files[str(p.relative_to(repo))]=sha(p)
p=repo/'RPCCR_SENSOR_ACTIVATED_SINGLE_TASK_CONTINUATION_20261104.json';files[str(p.relative_to(repo))]=sha(p)
(own/'CANDIDATE_FREEZE.json').write_text(json.dumps({'schema':'V807_SAME_REACTIVE_CANDIDATE_CARDINALITY_FIX','files':files},indent=2)+'\n')
assert all(sha(repo/n)==h for n,h in files.items())
print(json.dumps({'status':'PREPARED_SAME_CANDIDATE_LAST_INTERFACE_FIX','frozen_files':len(files),'deadline':auth['absolute_deadline_unix']}))
