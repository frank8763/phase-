"""One-route closure and night engineering diagnosis; no model imports or integration."""
import fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=R/'experiments/v974_daytime_binding_gate';O=R/'runs/v974_daytime_binding_gate';REC=R/'records/nav2_v974_20261110'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def main():
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 d=read(O/'COMPLETION.json');assert d['closed']and not read(O/'AUTHORIZATION.json')['models_authorized']
 frozen=read(C/'SOURCE_FREEZE.json');assert all((R/p).is_file()and sha(R/p)==h for p,h in frozen['files'].items())
 task=read(C/'TASKS.json')[0];out=Path(task['output']);native=read(out/'RESULT.json')if(out/'RESULT.json').exists()else{};audit=read(out/'INDEPENDENT_AUDIT.json')if(out/'INDEPENDENT_AUDIT.json').exists()else{}
 report='docs/RPCCR_DAYTIME_BINDING_V974_REPORT.md';REC.mkdir(exist_ok=True)
 final=dict(closed=True,passed=d['status']=='ONE_DYNAMIC_ROUTE_PASSED',source_sha_all_verified=True,source_count=len(frozen['files']),new_day=d,independent_audit=audit,
    carried_night=dict(status='V971_NOT_PASSED',actual_native=18201,replay_native=18201,private_native=0,algorithm_motion_exercised=False,not_in_new_denominator=True),
    models_during_closure=0,integrations=0,review_pending_original_restored=True,execution_lock_idle=True)
 dump(O/'FINAL_INDEPENDENT_AUDIT.json',final);dump(REC/'FINAL_INDEPENDENT_AUDIT.json',final)
 for p in O.glob('*.json'):(REC/p.name).write_bytes(p.read_bytes())
 for p in(R/'runs/v972_daytime_binding_probe').glob('*.json'):(REC/('BINDING_PROBE_'+p.name)).write_bytes(p.read_bytes())
 lines=['# V974白天单项：模块绑定与西向东动态整路','',f"结果：**{d['status']}**；单次原WE10010001/相位.6573753567727383动态180秒+2秒停车，窗口硬截止{d['deadline_unix']}，实际关闭{d['closed_unix']}。",
 '本轮最多90分钟、只此一主；没有自动重复、三路线、24确认或通宵。用户要求白天逐项推进，夜间另安排。旧08:00窗口和所有失败保持。','',
 '## 昨晚实际发生的事','',
 'V971在2026-11-09 22:57:17提前关闭。原完整WE执行18201原生、完整自身控制重放18201，私有0，距目标8.001964m；3600发令全为零，0条计划/0非零Nav2命令。149规划请求每次ValueError（expected2而实供3），不是走到最后两米或计算超时。坏接触0、最低实际.314989m、状态重放通过，不等于动态功能通过。其余任务和24未执行。',
 '快速零模型复现直接运行实际worker懒导入及实际planner协程，确认规划端选中V891两字段旧代理，物理端选中V881旧factory，缺少预期V958适配器和原精确传感绑定。V971原审核因缺EXACT_SENSOR_BINDING文件失败，原失败不追认。先前预目标/FollowPath组件资格未覆盖真实NavigateToPose全局代理，也未覆盖实际native懒导入；这是本轮工程检查遗漏。','',
 '## 本轮改动与资格','',
 '以仓库内受SHA核验的本地别名固定V968科学模块；规划包装器使用原三字段原子快照，已知接口异常立即停止，真实NO_PATH/几何拒绝门不改。原生factory明确委托原V968/V959/V958，并在真实t0核验控制compute源文件、适配器SHA、转向编码器和EXACT_SENSOR_BINDING，未通过禁止第一步积分。',
 '同两复现从红变绿；真实factory guard用明确无模型夹具接受正确源，拒绝昨晚真实坏SETUP及积分后绑定。参数、模型、19静态体/小actor/传感噪声、控制安全门与原RP-CCR科学函数不改。',
 '真实安装Nav2的NavigateToPose→Smac→RPP→安全准入软件演练通过：3规划/59条获证非零前进。合成运动学peer，0模型/0物理积分，不能当实际动态通过。首软件演练管理服务35秒未响应，0模型，原记录保留；第二次增加服务调用/响应诊断后成功（STARTUP响应约2.233秒），没有延长启动门或证明该偶发超时唯一原因、实时可靠性。','',
 '## 新旧积分分账','',
 f"V974新主：实际{native.get('actual_native','未知')}，自身控制重放{native.get('replay_native','未知')}，私有{native.get('private_native','未知')}，距目标{native.get('goal_distance_m','未知')}m，最低实际{native.get('minimum_actual_clearance_m','未知')}m，坏接触{native.get('bad_contacts','未知')}。",
 f"功能通过{audit.get('functional_passed',False)}，证据通过{audit.get('evidence_passed',False)}，独立总门{audit.get('passed',False)}。",
 f"原生错误：{native.get('error')}。审核错误：{audit.get('timing_audit_error',audit.get('selected_binding_error'))}。闭批原因：{d.get('error')}。",
 '旧V971的18201/18201与旧V968组件2794/2794、旧18响应全部独立，不混本轮一主或新24分母。','',
 '## 范围与收尾','',
 '原逐原生.15净空/完整自体与接触未知0/合法ctrl与速率/静态体固定/无积分外根写/完整状态控制重放≤1e−8保留；原.155准入、非反向.02/.035经验管、.2s命令+2s刹停、50ms新权限/200ms expiry/100Hz100ms门不变。必须真实行驶测距发现—原因果参考—发现后实际续行>=1m—目标<=.45并实际停稳。全生效恢复参考仍独立.04/.035跟踪审核。',
 '发现前较弱反应式合同/3m起步排除先验、单.08m/s且.32周期小actor条件明示；不恢复旧328定理，不是任意遮挡/多actor/地图/实时/递归安全/RAS保证。一主成功也不是24动态验收。训练/SAC/实机0，Stage隔离。',
 '模型授权关闭、原guard恢复、锁空闲、全部源SHA核验。今天此项结束后停下复盘，不自动通宵。必要新证据与昨晚失败记录分组归档，同仓库Release下载/memberSHA核验后按清单清理；新批唯一30秒push/5秒HEAD核验，失败保留必要缓存，不循环重试。']
 (R/report).write_text('\n'.join(lines)+'\n')
 current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,execution_window_closed=True,next_physical_authorized=False,report=report,current_report=report);dump(R/'CURRENT_EXPERIMENT.json',current)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f"\n- 2026-11-10 V974白天只一主：{d['status']}，{native.get('actual_native')}/{native.get('replay_native')}新实际/重放，旧V97118,201/18,201及错误源绑定保留不混账。真实全局规划→非零控制软件资格通过，真实t0绑定与单次整路结果见{report}。旧08窗不延长/新单项闭批，不自动晚间通宵/24/训练实机。\n")
 dump(REC/'LOCAL_CLOSURE.json',dict(closed=True,source_sha_verified=True,scientific_outcome=d['status'],report=report,models=0,integrations=0))
 fcntl.flock(lock,fcntl.LOCK_UN)
 for action in ['prepare','publish']:
  result=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('deliver.py')),action],cwd=R,timeout=180 if action=='prepare'else 300)
  if result.returncode:raise RuntimeError('DAY_EVIDENCE_DELIVERY_FAILED_KEEP_RAW '+action)
if __name__=='__main__':main()
