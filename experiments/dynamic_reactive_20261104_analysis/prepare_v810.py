"""Register/freeze the last overnight revision; no model access or integration."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import time

repo = Path(__file__).resolve().parents[2]
old = repo / 'experiments/v809_time_reference_global'
own = repo / 'experiments/v810_forward_reference_global'
root = repo / 'runs/v810_forward_reference_global'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

assert not own.exists() and not root.exists()
assert (repo / 'REVIEW_PENDING').exists()
previous = read(repo / 'runs/v809_time_reference_global/FINALIZED.json')
assert not previous['development_passed']
assert previous['archive']['all_source_and_decompressed_readback_verified']
ledger_path = repo / 'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json'
ledger = read(ledger_path)
assert ledger['development_revisions_used'] == 1
assert ledger['confirmation_rounds_started'] == 0
started = time.time()
deadline = min(started + 7200, ledger['unique_absolute_deadline_unix'])
assert deadline - started == 7200
# Charge qualification/preparation before evaluating the new candidate.
ledger.update(status='V810_LAST_DEVELOPMENT_PREPARING',
              development_revisions_used=2, active_simulation=False,
              development02_started_unix=started,
              development02_absolute_deadline_unix=deadline,
              development02='V810_FORWARD_REFERENCE_PREFERENCE_WITH_ORIGINAL_BIDIRECTIONAL_FALLBACK',
              development01_closed=dict(status=previous['status'], main_attempts=1,
                  successful_main=0, main_not_executed=2, repeats_not_executed=3,
                  navigation_native=9600, private_native=7914320, replay_native=9600,
                  full_archive_readback=True), active_master_pid=None)
dump(ledger_path, ledger)
own.mkdir()
root.mkdir()
for p in old.iterdir():
    if p.is_file() and p.suffix in ['.py', '.md', '.json'] and p.name != 'CANDIDATE_FREEZE.json':
        (own / p.name).write_text(p.read_text().replace('v809_time_reference_global', 'v810_forward_reference_global'))

p = own / 'planner.py'
s = p.read_text()
a = s.index('def timed_search(')
b = s.index('\ndef search(', a)
timed = s[a:b]
assert timed.count('work_limit=None):') == 1
timed = timed.replace('work_limit=None):', 'work_limit=None,forward_only=False):', 1)
assert timed.count('for gear in (1,-1):') == 1
timed = timed.replace('for gear in (1,-1):', 'for gear in ((1,) if forward_only else (1,-1)):', 1)
s = s[:a] + timed + '''\ndef search(field,*args,**kwargs):
    if getattr(field,'temporal_state',None)is None:return spatial_search(field,*args,**kwargs)
    preferred,preferred_stats=timed_search(field,*args,**kwargs,forward_only=True)
    selected=preferred is not None and preferred_stats['status']=='GLOBAL_GOAL_PATH'
    if selected:path,stats=preferred,dict(preferred_stats)
    else:path,stats=timed_search(field,*args,**kwargs)
    stats['forward_reference_preference']={
        'selected_forward_goal_reference':selected,
        'preferred_status':preferred_stats['status'],
        'preferred_expanded':preferred_stats.get('expanded',0),
        'original_bidirectional_fallback_called':not selected,
        'total_expanded':preferred_stats.get('expanded',0)+(0 if selected else stats.get('expanded',0)),
        'actual_reverse_control_and_recovery_unchanged':True,
        'scope':'Reference proposal preference only; all execution safety contracts unchanged.'}
    return path,stats
'''
p.write_text(s)

p = own / 'execute_development.py'
s = p.read_text()
start = s.index("unchanged();assert")
end = s.index('with(repo/', start)
s = s[:start] + """unchanged();assert(repo/'REVIEW_PENDING').exists();assert read(root/'pre_navigation/FINAL_INDEPENDENT_AUDIT.json')['status']=='FORWARD_REFERENCE_SAVED_QUALIFICATION_PASS';assert not(root/'ROUND_WINDOW.json').exists()
""" + s[end:]
s = s.replace("assert day['development_revisions_used']==1 and day.get('physical_batches_started',0)==0", "assert day['development_revisions_used']==2 and day.get('development02_physical_batches_started',0)==0")
s = s.replace("deadline=day['development_absolute_deadline_unix']", "deadline=day['development02_absolute_deadline_unix']")
s = s.replace("('audit_time_reference.py',300)", "('audit_time_reference.py',300),('audit_forward_preference.py',60)")
s = s.replace('V809_OUTER_TERMINATED', 'V810_OUTER_TERMINATED')
s = s.replace('THREE_TIME_REFERENCE_MAIN_AND_REPEAT_PASSED', 'THREE_FORWARD_REFERENCE_MAIN_AND_REPEAT_PASSED')
p.write_text(s)

p = own / 'finalize_development.py'
s = p.read_text().replace("'audit_time_reference.py']", "'audit_time_reference.py','audit_forward_preference.py']")
s = s.replace('THREE_TIME_REFERENCE_MAIN_AND_REPEAT_PASSED', 'THREE_FORWARD_REFERENCE_MAIN_AND_REPEAT_PASSED')
s = s.replace('THREE_TIME_REFERENCE_DEVELOPMENT_VERIFIED', 'THREE_FORWARD_REFERENCE_DEVELOPMENT_VERIFIED')
s = s.replace('rpccr_time_reference_global_v809_20261104', 'rpccr_forward_reference_global_v810_20261104')
s = s.replace('RPCCR_TIME_REFERENCE_GLOBAL_V809_REPORT.md', 'RPCCR_FORWARD_REFERENCE_GLOBAL_V810_REPORT.md')
s = s.replace('RP-CCR V809', 'RP-CCR V810')
s = s.replace('唯一科学新变化是V808资格已核验的时间标记参考', '本夜最后修订仅在原时间标记参考上先查完整向前目标路径、无完整向前路径才原双向回退；实际倒车控制及后备保持')
s = s.replace('原V807失败不改写', '原V807及V809失败不改写')
p.write_text(s)

(own / 'PROTOCOL.md').write_text('''# V810 夜间最后开发02：完整向前参考优先

2026-11-04用户授权后台无人监管至11月5日08:00/1793836800。本夜开发已登记2/2，确认0/1；V808/V809原开发01已HORIZON失败及全部原证据永久保持。本候选资格/初始化/夹具失败也消耗最后名额，不可第三开发或克隆修补。开发02一次7200秒，绝对截止见DEVELOPMENT_WINDOW.json，含准备/资格/物理/重放审核，不重置且不越08。

V809原1200公开/9600原生、7914320私有、9600重放，首次262原测距发现、302实际328刹停及其后续行完成，但剩2.402864m未到达。21发现后参考都有完整目标且各有倒车，20参考失效触发重规划，停车后走9.87755m/倒行4.05755m/净目标减少1.54928m；所有普通命令有完整安全后备，不能归结为前向命令全安全拒绝或简单延长必通过。

唯一修订：检测后同时间标记Hybrid A*先搜索原七转角的gear+1子集，仅当得到GLOBAL_GOAL_PATH才优先；否则原双向搜索完全保持。发现前原空间A*精确不变。原.18/4000与.155/16000两级调用不变，每级可能多一个有限向前搜索，总最坏扩展由20000增加至40000，非等计算优势。原动作/评分/名义控制/可用倒车/紧急后备/完整328执行安全合同、原始测距/估计、6.56s参考边界不改。参考优先不是强制实际向前或全局执行保证。

先固定V809原303/363/649/1183四个保存输入，零模型/禁止MuJoCo导入，每个原4000优先/16000条件回退，最多600秒共享原开发截止；全部必须得到无倒车完整目标参考、所有原时间几何/657覆盖/曲率/密集.155或原更严格guard和作用域独立审核通过。保存原21双向参考及原控制日志作为反例，不能用新的动作/种子/真实actor未来或调参扫描。资格失败停止本夜所有新物理。

资格独立通过后原三路线WEST_EAST/NORTH_SOUTH/EAST_WEST、10010001–03原相位、同19实体地图/直径.20幅.25欧氏速.08actor/3m测距5%漏检。3t0全预检、原序3主，完整链全过才原序3完整重复。首功能失败或首次安全/源/模型/真值/状态/控制/覆盖/证据异常停该批及依赖确认，不能换任务重跑。

完整链正常行驶首次原测距发现、原328实际停稳、新因果全局参考、实际续行>=1m、目标<=.45。原生净空>=.15/障碍穿透未知0/完整自体合法ctrl速率/静态实体固定/无积分外根写/全部状态控制重放<=1e-8/329执行657规划包含/原始测距因果/全部尾和再接入审核保持。重复同结果长度qpos/qvel/ctrl/mocap<=1e-8、模型规范初态真实接触发现一致。

实际模型/导航/私有预测/重放只run_phase.sh单CPU单实例执行锁。nav1200公开/1200soft1500hard1505outer，t0120内125外，各子进程绝对墙钟不越开发/夜间截止。运行冻结源不编辑；训练/SAC/Stage/实机0，current/runtime与冻结网络不改、原证据不删、不新聊天/子代理或外部消息。发现前静态合同是更弱反应式条件，不能冒称隐藏actor安全保证；6.56s外参考仍未证，不宣称完备/最优/实时/RAS创新。

闭批后仅零模型finalize_development.py独立终审及全来源/解压SHA回读，原archive不覆盖，大blob32MiB块无损重组核验。失败即开发用尽，停止新物理并报告；全部3主3重复及全证据门通过才可另立唯一预留10050001–24新确认，确认实现尚未准备，余时不足不启动。最终仅一次有界同步及REVIEW_PENDING恢复、关闭台账/删除自动任务。
''')
dump(own / 'DEVELOPMENT_WINDOW.json', dict(started_unix=started, absolute_deadline_unix=deadline,
    hard_night_deadline_unix=1793836800, limit_s=7200, development_slot=2, final_development=True))
dump(own / 'QUALIFICATION_INPUTS.json', [dict(step=s,
    source=f'runs/v809_time_reference_global/main_slot01/paired/geometry_memory/planning_{s:04d}.json',
    sha256=sha(repo / f'runs/v809_time_reference_global/main_slot01/paired/geometry_memory/planning_{s:04d}.json'))
    for s in [303,363,649,1183]])
dump(root / 'PREPARATION.json', dict(status='LAST_DEVELOPMENT_REGISTERED_BEFORE_QUALIFICATION',
    started_unix=started, absolute_deadline_unix=deadline, models=0, integrations=0,
    evidence='runs/v809_time_reference_global/FINALIZED.json'))
for p in own.glob('*.py'):
    ast.parse(p.read_text())
current_path = repo / 'CURRENT_EXPERIMENT.json'
current = read(current_path)
current.update(status='V810_LAST_DEVELOPMENT_PREPARING', state='V810_LAST_DEVELOPMENT_PREPARING',
               current_experiment='V810_FORWARD_REFERENCE_GLOBAL', active_automation='phase-11-5-08-00')
current['global_dynamic_overnight_20261104'].update(current_protocol=str((own/'PROTOCOL.md').relative_to(repo)),
    development02_absolute_deadline_unix=deadline, latest_actual_state='V809 failed closed and archived; final development02 registered, no new physical work')
dump(current_path, current)
print(json.dumps(dict(prepared=str(own.relative_to(repo)), development_used=2,
    deadline_unix=deadline, deadline_beijing=datetime.datetime.fromtimestamp(deadline).isoformat(),
    frozen=False, qualification_started=False, models=0, integrations=0)))
