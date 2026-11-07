"""Review/freeze/start same-revision physical stage after independent saved qualification."""
import ast,datetime,fcntl,hashlib,json,pathlib,subprocess,time
repo=pathlib.Path(__file__).resolve().parents[2];own=repo/'experiments/v809_time_reference_global';q=repo/'experiments/v808_timed_reference_qualification';root=repo/'runs/v809_time_reference_global';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(repo/'runs/v808_timed_reference_qualification/FINALIZED.json')['source_decompressed_sha_verified'];assert read(repo/'runs/v809_preparation/RESULT.json')['status']=='PHYSICAL_INTERFACE_SAVED_PREPARATION_PASS'
p=own/'execute_development.py';s=p.read_text();start=s.index('def execute(');end=s.index('def set_task(',start)
s=s[:start]+'''def execute(script,args,log,cap):
 global process
 args=list(map(str,args));unchanged();assert time.time()+cap+3<deadline,'ABSOLUTE_BUDGET_INSUFFICIENT';dump(window/'ACTIVE.json',dict(script=script,args=args,started_unix=time.time(),cap_s=cap,deadline=deadline))
 stage_lock=None
 try:
  if script!='run_static.py':
   stage_lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(stage_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with log.open('x')as stream:
   process=subprocess.Popen([str(repo/'run_phase.sh'),str(own.relative_to(repo)/script),*args],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   try:return process.wait(timeout=min(cap,deadline-time.time()))
   finally:
    if process.poll()is None:
     os.killpg(process.pid,signal.SIGTERM)
     try:process.wait(timeout=2)
     except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    process=None
 finally:
  if stage_lock is not None:stage_lock.close()
'''+s[end:];p.write_text(s)
# Review candidate equivalence, all fixed task counts, parse every source before freeze.
for p in own.glob('*.py'):ast.parse(p.read_text())
assert (own/'planner.py').read_bytes()==(q/'planner.py').read_bytes()and (own/'timed_reference.py').read_bytes()==(q/'timed_reference.py').read_bytes()
assert len(read(own/'DEVELOPMENT_TASKS.json'))==3
assert "len(details)==len(tasks)==3"in(own/'audit_field_preflight.py').read_text()
assert "'audit_time_reference.py'"in(own/'finalize_development.py').read_text()
root.mkdir(exist_ok=False);deadline=read(repo/'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json')['development_absolute_deadline_unix'];assert deadline-time.time()>5000
with (repo/'runs/v648_static_unknown/execution.lock').open('a+')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert(repo/'REVIEW_PENDING').exists()
files=dict(read(q/'CANDIDATE_FREEZE.json')['files'])
for p in own.iterdir():
 if p.is_file():files[str(p.relative_to(repo))]=sha(p)
(own/'CANDIDATE_FREEZE.json').write_text(json.dumps({'schema':'V809_SAME_V808_TIME_REFERENCE_REVISION','files':files,'inherited_absolute_deadline_unix':deadline,'same_scientific_candidate_as_qualification':True},indent=2)+'\n')
assert all(sha(repo/p)==h for p,h in files.items())
proof=dict(status='PHYSICAL_SOURCE_REVIEWED_FROZEN',qualification='runs/v808_timed_reference_qualification/FINALIZED.json',saved_interface_check='runs/v809_preparation/RESULT.json',three_original_tasks=read(own/'DEVELOPMENT_TASKS.json'),source_files=len(files),planner_and_time_module_exact=True,remaining_original_development_s=deadline-time.time(),all_model_workers_including_replay_and_model_metadata_audit_canonical_locked=True,no_simulation_in_review=True)
(root/'PRE_NAV_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n')
for n in ['AGENTS.md','RESEARCH_STATUS.md']:
 p=repo/n;p.write_text(p.read_text()+'\n- V808五保存输入全部数学/657集合/时间几何独立PASS，最大误差7.77e-16/3285覆盖/0模型积分，303旧2.129881m分段改善为目标.256551m完整参考；四旧晚态仍分段，非实际导航成功。87来源资格归档解压SHA回读。V809同候选物理阶段已事前冻结，planner/timed_reference字节精确，原3路线10010001–03/原相位3t0+3主，全链全门过才3完整重复；原V808总截止'+str(deadline)+'不重置/夜间08不变。初始原A*完全精确、10保存参考查询独立误差<=8.89e-16、原三t0传感审核接口零模型演练PASS。运行不改冻结源、不重复实例，首功能/安全证据异常停；模型含重放/元数据审核均执行锁保护，只run_phase单CPU。闭批后无同finalizer/FINALIZED时零模型finalize_development.py独立归档收尾。当前确认未准备未启动，训练/Stage/实机0。\n')
h=repo/'runs/global_dynamic_overnight_20261104/OVERNIGHT_HANDOFF.md';h.write_text(h.read_text()+'\n## LATEST OVERRIDE\n\nV808保存资格已独立PASS并FINALIZED/87来源回读，303完整目标参考.256551m，其余旧晚态分段，模型积分0。V809为同开发01物理阶段，三任务源/11审核事前冻结，planner和timed_reference与V808字节相同；原开发绝对截止'+str(deadline)+'不得重置，夜间1793836800也不变。先看runs/v809_time_reference_global/ROUND_WINDOW.json、development01/ACTIVE/PREFLIGHTS/RESULTS/COMPLETION/ERROR及当前任务partial_progress，日志runs/v809_driver.console。仅一次driver，不重复实例/不编辑冻结源。3t0/3主全部链过才3完整重复；失败即停。驱动不会自动finalize；确认已闭批、guard恢复且无同finalizer/FINALIZED才python3 -B experiments/v809_time_reference_global/finalize_development.py > runs/v809_finalize.console；既有归档只核验不覆盖。开发已用1/2、确认0/1，若失败先零模型真实定位，可信有余时才新目录冻结最后开发，不能修补重跑本V809。所有实际模型含重放审核均执行锁+run_phase。资格和物理预演已PASS，不再重做准备。确认实现尚未准备，禁止假称已就绪。夜间最终同步尚未执行，不做每阶段循环push。当前聊天若还在启动/监控本批，heartbeat只核实不并发工作。\n')
p=repo/'CURRENT_EXPERIMENT.json';d=read(p);d.update(status='V809_FROZEN_READY',state='V809_FROZEN_READY',current_experiment='V809_TIME_REFERENCE_GLOBAL_DEVELOPMENT',active_automation='phase-11-5-08-00');d['global_dynamic_overnight_20261104']['current_protocol']=str((own/'PROTOCOL.md').relative_to(repo));d['global_dynamic_overnight_20261104']['development_absolute_deadline_unix']=deadline;p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
p=repo/'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json';d=read(p);d.update(status='V809_FROZEN_READY',qualification_passed=True,qualification='runs/v808_timed_reference_qualification/FINALIZED.json',physical_source_review='runs/v809_time_reference_global/PRE_NAV_REVIEW.json');p.write_text(json.dumps(d,indent=2)+'\n')
subprocess.run(['git','add','AGENTS.md','RESEARCH_STATUS.md','CURRENT_EXPERIMENT.json','GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json','experiments/v809_time_reference_global','experiments/dynamic_reactive_20261104_analysis','evidence/rpccr_time_reference_qualification_v808_20261104'],check=True);subprocess.run(['git','diff','--cached','--check'],check=True);subprocess.run(['git','-c','gc.auto=0','commit','-q','-m','Verify timed-reference qualification and freeze original three-route physical development with inherited deadline'],check=True)
log=(repo/'runs/v809_driver.console').open('x');proc=subprocess.Popen(['timeout','--signal=TERM','--kill-after=5s',str(int(deadline-time.time())+1)+'s','python3','-B',str(own/'execute_development.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();(root/'LAUNCH.json').write_text(json.dumps({'outer_pid':proc.pid,'launched_unix':time.time(),'absolute_development_deadline_unix':deadline},indent=2)+'\n')
# Do not pre-set the driver's prerequisite counter. Wait only for its locked window.
for _ in range(40):
 if(root/'ROUND_WINDOW.json').exists():break
 if proc.poll()is not None:raise RuntimeError('DRIVER_EXIT_BEFORE_WINDOW; preserve log, no automatic retry')
 time.sleep(.1)
assert(root/'ROUND_WINDOW.json').exists()
p=repo/'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json';d=read(p);d.update(status='V809_RUNNING',physical_batches_started=1,active_simulation=True,active_master_pid=read(root/'ROUND_WINDOW.json')['pid']);p.write_text(json.dumps(d,indent=2)+'\n')
p=repo/'CURRENT_EXPERIMENT.json';d=read(p);d.update(status='V809_RUNNING',state='V809_RUNNING');p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'physical_development_started':True,'outer_pid':proc.pid,'master_pid':read(root/'ROUND_WINDOW.json')['pid'],'absolute_development_deadline_unix':deadline,'overnight_hard_stop':1793836800,'algorithm_revisions_used':1}))

