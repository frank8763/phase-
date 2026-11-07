"""Register this newly authorized overnight; preserve every prior closed round."""
import datetime,hashlib,json,pathlib,time
repo=pathlib.Path(__file__).resolve().parents[2];root=repo/'runs/global_dynamic_overnight_20261104';root.mkdir(exist_ok=False)
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
deadline=datetime.datetime(2026,11,5,8,tzinfo=datetime.timezone(datetime.timedelta(hours=8))).timestamp();assert deadline==1793836800 and time.time()<deadline
auth=dict(user_instruction='2026-11-04 可以考虑今天的通宵实验了；采用后台无人监管的方式实验，跑到明天早上，合理安排实验',authorized_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),unique_absolute_deadline_unix=deadline,hard_stop_beijing='2026-11-05 08:00:00+08:00',deadline_inferred_from_prior_morning_reporting_preference=True,max_development_revisions=2,max_fresh_confirmation_rounds=1,development_wall_cap_s=7200,confirmation_wall_cap_s=21600,all_subprocess_deadlines_absolute=True,preparation_calibration_fixture_failures_consume_development_slot=True,extra_seeds_action_scans=False,source_freeze_before_navigation=True,actual_models_and_integrations_only_run_phase=True,training=0,stage_access=0,real_robot=0,old_authorizations_deadlines_failures_unchanged=True,scope='Physical scene small actor, raw lidar causal detection, finite reactive full-field development. Predetection static-only condition retained explicitly; no arbitrary unseen/occluded guarantee. Confirmation only after all three original development routes and full same-version repeats pass.')
dump(repo/'GLOBAL_DYNAMIC_OVERNIGHT_AUTHORIZATION_20261104.json',auth)
dump(repo/'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json',dict(status='PREPARING_TIME_ALIGNED_QUALIFICATION',round_closed=False,unique_absolute_deadline_unix=deadline,development_revisions_used=0,max_development_revisions=2,confirmation_rounds_started=0,max_confirmation_rounds=1,actual_new_model_initializations=0,actual_new_navigation_native=0,actual_private_native=0,actual_replay_native=0,accounts_currently_exact=True,active_simulation=False,authorization='GLOBAL_DYNAMIC_OVERNIGHT_AUTHORIZATION_20261104.json',old_V807_closed_not_passed=True))
cases=json.loads((repo/'experiments/v807_reactive_single_task_continuation/SCENE_CASES.json').read_text());tasks=[]
for case in cases:
 for j in range(8):
  slot=len(tasks)+1;seed=10050000+slot;u=int.from_bytes(hashlib.sha256(f'RPCCR_TIME_REFERENCE_20261104|{seed}'.encode()).digest()[:8],'big')/2**64;phase=(u-.5)*3.141592653589793+(0 if j%2==0 else 3.141592653589793)
  tasks.append(dict(slot=slot,seed=seed,phase=phase,case_id=case['id'],course_distance_m=case['euclidean_distance_m'],initial_axis_motion_direction='POSITIVE_AXIS'if j%2==0 else'NEGATIVE_AXIS',phase_rule='SHA256 RPCCR_TIME_REFERENCE_20261104|seed, cos sign alternates within each route',role='RESERVED_FRESH_CONFIRMATION_NOT_STARTED'))
dump(root/'RESERVED_CONFIRMATION_TASKS.json',tasks)
plan='''# 2026-11-04 RP-CCR全场动态通宵安排

用户明确授权后台无人监管至明早。唯一模型/积分硬截止2026-11-05 08:00北京时间/1793836800，不延后重置。旧V807及所有旧轮次已闭，失败与截止永久保持。本夜最多2开发修订（包括初始化、场景、夹具或资格修复失败），1轮新池确认；不无限克隆、换任务、刷动作池或降低门槛。通过可提前停止新模型工作，余时整理证据。08:00后仅零积分收尾、晨报和删除当前自动任务。

第一开发先V808固定原303/375/380/674/714保存输入的零模型时间参考资格，验证动态时刻一致性，不读取真实未来或场景相位。预注册一时间参考算法、原空间/车辆/控制/传感与风险阈值不变。不能仅删除动态域当作成功。资格及独立几何审核通过后才能在新物理输出namespace执行原3路线10010001–03/原相位3t0、3主；全部完整链通过后3同版本完整重复。开发一次7200秒绝对窗（含资格/准备/运行，不重置），单次nav1200公开/1200软1500硬1505外层，t0120内125外，各子进程不得越夜间截止。

只有发现前原静态路线、行驶中首次测距发现、原328实际停稳、新因果动态全局参考、真实续行>=1m、目标<=.45，以及完整原生净空>=.15/障碍穿透未知0/自体合法ctrl速率/无根改写/静态geom固定/完整全状态控制重放<=1e-8/329执行657规划包含/原因果原始测距与所有实际尾审核、三同版本完整重复全部通过，才能依赖确认。重复同结果长度和qpos/qvel/ctrl/mocap<=1e-8、模型规范初态真实接触发现一致。证据PASS不是功能通过。

若首开发失败，先保存日志零积分定位。只有剩余一个名额且有可信针对性修订/足够夜间余时，才新目录冻结第二开发；同原任务/几何/安全不换，首次安全或证据异常停整批。第二开发失败或没有可信修复后，停止所有新物理，只有限分析/报告，不为了跑满刷实验。

确认实现尚未准备，不假称就绪。预留新10050001–24，每路线8、初始正反各12，须核验未用，保留RESERVED_CONFIRMATION_TASKS原字节并在任何新导航前一次冻结全部算法、审计与24任务。全24零积分t0预检后原序24主，>=23/24、每路线>=7/8、正反各>=11/12；第二功能失败或首次物理/覆盖/源/模型/真值/状态/控制/证据异常立即停止，不替补。全分母达门后slot1/9/17完整重复。确认最多21600秒且不越08:00；余时不足完整已注册预算不启动。只一池，开发/旧24/重复不混入新确认分母。

算法路线以原A*静态走廊作拓扑，使用真实测距预测的时间标记动态约束。有限时域外只能声明参考未获动态证明，实际8+320完整安全尾仍必须。V807发现前静态合同是明确更弱反应式条件，此夜保留这个范围；不能借SIPP文献声称未知噪声模型下完备/实时/递归安全，也不能声称任意遮挡突入、多actor、全面优势或RAS保证。单直径.20/幅.25/.08欧氏速度原actor不堵中央通道；原19静态实体/3m测距噪声5%漏检保持。真实actor状态只物理/传感/离线评价，严禁输入在线控制。

全部实际模型初始化、导航、预测和重放只run_phase隔离入口、单CPU单实例/执行锁/有限绝对墙钟；不访问Stage任何文件、源、模型、输出或进程，不改current/runtime及冻结网络，训练/SAC/实机0。新源experiments、输出runs，冻结后不编辑。首次异常保存原ERROR/COMPLETION与不明账目，不伪造PASS或重启旧批。无外部消息/新聊天/子代理；原始证据未经远端验证不删除。

闭批必须独立零积分审核/全来源与解压SHA回读归档、真实报告（成功/失败/未执行、准确或未知导航私有重放分账）、审阅提交。超100MB blob无损32MiB分块重组核验、原件保留。全夜最终一次最多30秒push+5秒远端只读核验，失败不循环。恢复REVIEW_PENDING、关闭夜间台账，结束后删除自动任务。用户明早看实际结果与真实媒体，不能以开发救回或零接触代替验收。
'''
(repo/'docs/GLOBAL_DYNAMIC_OVERNIGHT_20261104_PLAN.md').write_text(plan)
(root/'OVERNIGHT_HANDOFF.md').write_text('# Overnight handoff\n\n## LATEST OVERRIDE\n\nNew overnight authorized, deadline1793836800. Qualification code being prepared; new physics0. Read root authorization/ledger and plan. No driver has started; do not invent completion or launch unprepared confirmation. Preserve V807 NOT_PASSED.\n')
p=repo/'CURRENT_EXPERIMENT.json';d=json.loads(p.read_text());d.update(status='OVERNIGHT_PREPARING',state='OVERNIGHT_PREPARING');d['global_dynamic_overnight_20261104']={'authorization':'GLOBAL_DYNAMIC_OVERNIGHT_AUTHORIZATION_20261104.json','ledger':'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json','plan':'docs/GLOBAL_DYNAMIC_OVERNIGHT_20261104_PLAN.md','hard_deadline_unix':deadline};dump(p,d)
print(json.dumps({'hard_deadline_unix':deadline,'reserved_tasks':len(tasks),'new_models':0,'integrations':0}))
