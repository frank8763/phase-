"""Finish bounded runner adapters and freeze the one registered scientific condition."""
import ast,datetime,hashlib,json,pathlib
repo=pathlib.Path(__file__).resolve().parents[2];own=repo/'experiments/v806_sensor_activated_dynamic';old=repo/'experiments/v802_exact_rejection_global';root=repo/'runs/v806_sensor_activated_dynamic'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=own/'execute_development.py';s=p.read_text()
s=s.replace("assert read(repo/'runs/v801_exact_rejection_qualification/FINALIZED.json')['qualification_passed'];assert read(repo/'runs/v801_exact_rejection_qualification/FINAL_INDEPENDENT_AUDIT.json')['status']=='PASS';", "assert read(root/'pre_navigation/RESULT.json')['status']=='REACTIVE_ZERO_MODEL_QUALIFICATION_PASS';")
s=s.replace("day=read(repo/'RPCCR_EXACT_ACCELERATION_LEDGER_20261104.json');assert day['acceleration_versions_used']==1 and day['global_batches_started']==1;authorization=read(repo/'RPCCR_EXACT_ACCELERATION_AUTHORIZATION_20261104.json')", "day=read(repo/'RPCCR_SENSOR_ACTIVATED_LEDGER_20261104.json');assert day['candidate_versions']==1 and day['nav_started']==0;authorization=read(repo/'RPCCR_SENSOR_ACTIVATED_AUTHORIZATION_20261104.json')")
s=s.replace("assert deadline-started>=7199", "assert deadline-started>=6000")
s=s.replace("'--wall-seconds',900", "'--wall-seconds',1500").replace("),905)", "),1505)")
# The literal list calls below have no closing tuple; verify the adaptation.
s=s.replace("],window/(name+'.console'),905)", "],window/(name+'.console'),1505)")
s=s.replace("('audit_rejection_witnesses.py',300)","('audit_reactive.py',300)")
s=s.replace("THREE_ROUTE_MAIN_AND_REPEAT_PASSED", "ONE_REACTIVE_MAIN_AND_REPEAT_PASSED")
s=s.replace("V802_OUTER_TERMINATED", "V806_OUTER_TERMINATED")
# A separate window.lock prevents duplicate masters; the worker holds canonical execution.lock.
anchor="guard=(repo/'REVIEW_PENDING').read_bytes();"
s=s.replace(anchor,"master_lock=(root/'window.lock').open('a+');fcntl.flock(master_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)\n"+anchor)
p.write_text(s)
assert "'--wall-seconds',1500"in s and "1505)"in s and 'RPCCR_EXACT_ACCELERATION'not in s and 'audit_rejection_witnesses.py'not in s
p=own/'finalize_development.py';s=p.read_text().replace("'audit_rejection_witnesses.py'","'audit_reactive.py'").replace('len(records)==6','len(records)==2').replace('THREE_ROUTE_MAIN_AND_REPEAT_PASSED','ONE_REACTIVE_MAIN_AND_REPEAT_PASSED').replace('THREE_ROUTE_DEVELOPMENT_VERIFIED','ONE_REACTIVE_DEVELOPMENT_VERIFIED').replace('GLOBAL_DYNAMIC_DEVELOPMENT_NOT_PASSED','REACTIVE_DYNAMIC_DEVELOPMENT_NOT_PASSED').replace('planned_main=3,planned_repeat=3','planned_main=1,planned_repeat=1').replace('rpccr_exact_rejection_global_v802_20261104','rpccr_sensor_activated_dynamic_v806_20261104')
s=s.replace("report=repo/'docs/RPCCR_EXACT_REJECTION_GLOBAL_V802_REPORT.md';text=", "report=repo/'docs/RPCCR_SENSOR_ACTIVATED_V806_REPORT.md';text=")
start=s.index('report=repo/');end=s.index("report.write_text",start)
s=s[:start]+'''report=repo/'docs/RPCCR_SENSOR_ACTIVATED_V806_REPORT.md';text=['# RP-CCR V806 雷达触发完整场地动态开发','',f"实际结论：**{result['status']}**。主尝试{result['main_attempts']}/计划1；成功条件完整重复{result['repeat_attempts']}/计划1，新确认0。",'', '障碍仍是原物理场景的小型actor，在线只接收原始有噪声测距。发现前跟随已知静态全局参考，证书仅覆盖静态/自体/控制；发现后原估计外集合、完整328动态合同、停车/重规划恢复。此处主动移除旧未见域的在线鲁棒约束，明确更弱的反应式课程，不能声称旧未知域保证保留。','', f"实际导航{actual}/私有{result['private_native']}/完整重放{result['replay_native']}原生；null是未知。"]
for row in records:
 r=row['result'];text.append(f"- {row['name']}："+(f"{r.get('outcome','INTERRUPTED')}；{r.get('public_steps')}公开/{r.get('physics_steps')}原生，首次发现{r.get('first_discovery_step')}；完整链及全部所需审核通过={row['full_chain_and_repeat_if_applicable_passed']}。"if r else'未完成/未知。'))
text+=['', '同WEST_EAST/原10010001/原相位、19静态体及原actor、测距/噪声/模型/控制库不改；软墙钟1200/硬1500，不是实时。全部实际净空.15/原预测.155/完整自体合法ctrl速率/无根改写/原生重放门保持；发现前静态合同并不提供隐藏actor保证。', '一个已观察任务的开发和重复，不是新24验收或统计优势。与静态五回合、旧空白24/24各分账。原失败不覆盖，停止后不刷种子/新版本/第三导航；训练/Stage/实机0，REVIEW_PENDING恢复。',f"全证据{dest.relative_to(repo)}：{len(inventory)}来源/{summary['raw_bytes']}原始字节，来源与解压SHA回读通过；原始runs不删除。"]
''' +s[end:]
p.write_text(s)
# Remove unused old audit entry that asserts a different unchanged hypothesis;
# keep the original frozen V802 file untouched. Not a run-time audit omission.
(own/'audit_rejection_witnesses.py').unlink()
for p in own.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
auth=read(repo/'RPCCR_SENSOR_ACTIVATED_AUTHORIZATION_20261104.json')
for name in ['AGENTS.md','RESEARCH_STATUS.md']:
 p=repo/name;p.write_text(p.read_text()+"\n- 用户审阅无动态五回合5/5后明确继续真实场景actor、雷达发现后重规划。V806新独立一条件有界开发，先读experiments/v806_sensor_activated_dynamic/PROTOCOL.md；绝对截止"+str(auth['absolute_deadline_unix'])+"不延长。唯一科学变化为未发现时静态合同，不再将整个未见actor域用于在线约束/评分；发现后原外集合/328完整安全尾/刹停重规划/329执行657规划恢复。明确更弱反应式假设，不冒称原未见风险保证保留；真值只物理/传感/评价，不能在线读坐标。原WEST_EAST/10010001/相位0一个主+成功条件完整重复，1200公开/1200soft1500hard1505outer，首次异常或功能失败停/冻结后零修补/不新24。物理净空.15/自体ctrl/全原生重放原门不降，训练/Stage/实机0，所有实际模型积分只run_phase单CPU单实例。旧失败与静态五表永久保持；报告如实分账，闭批恢复REVIEW_PENDING。\n")
p=repo/'CURRENT_EXPERIMENT.json';d=read(p);d.update(status='V806_PREPARED',state='V806_PREPARED',current_experiment='V806_SENSOR_ACTIVATED_REACTIVE_DYNAMIC',active_automation=None);d['sensor_activated_dynamic']={'protocol':str((own/'PROTOCOL.md').relative_to(repo)),'authorization':'RPCCR_SENSOR_ACTIVATED_AUTHORIZATION_20261104.json','absolute_deadline_unix':auth['absolute_deadline_unix'],'main':1,'conditional_repeat':1,'unseen_universal_guarantee':False,'scope':'Physical scene actor, actual range-only detection, original tracked gate after first hit; predetection static-only.'};p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
p=repo/'RPCCR_SENSOR_ACTIVATED_LEDGER_20261104.json';d=read(p);d.update(status='FROZEN_READY',qualification_passed=True);p.write_text(json.dumps(d,indent=2)+'\n')
files={k:v for k,v in read(old/'CANDIDATE_FREEZE.json')['files'].items()if not k.startswith('experiments/v802_exact_rejection_global/')}
for p in own.iterdir():
 if p.suffix in ('.py','.md','.json')and p.name!='CANDIDATE_FREEZE.json':files[str(p.relative_to(repo))]=sha(p)
p=repo/'RPCCR_SENSOR_ACTIVATED_AUTHORIZATION_20261104.json';files[str(p.relative_to(repo))]=sha(p)
freeze={'schema':'V806_SENSOR_ACTIVATED_REACTIVE','frozen_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'files':files,'scope_changed_explicitly':'Predetection known-static certificate; original tracked dynamic gate after first causal hit.'}
(own/'CANDIDATE_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
assert all(sha(repo/k)==v for k,v in files.items())
print(json.dumps({'frozen_files':len(files),'deadline_unix':auth['absolute_deadline_unix'],'models':0,'integrations':0}))
