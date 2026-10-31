"""Final scientific report for the fixed V652 confirmation; zero simulation."""
import json, shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

repo = Path(__file__).resolve().parents[2]
root = repo/'runs/v652_static_confirmation'
window = root/'confirmation_window01'
def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default
completion = read(window/'COMPLETION.json')
assert completion, 'Final report requires a closed window; do not report partial completion'
audit = read(root/'INDEPENDENT_ACCEPTANCE_AUDIT.json')
assert audit, 'Run audit_v652_final.py first'
selection = read(window/'SELECTION_FREEZE.json',{})
tasks = selection.get('tasks',[])
outcomes = read(window/'CONFIRMATION_RESULTS.json',[])
ledger = read(window/'LEDGER.json',[])
screened = [x for x in ledger if x['feasibility_only']]
safe = {x['name']:x for x in audit['runs']}
by_seed = {x['seed']:x for x in outcomes}
passed = completion['static_engineering_acceptance_passed'] and audit['static_engineering_acceptance_passed']
fig, axes = plt.subplots(1,2,figsize=(13,4.8),constrained_layout=True)
for scene,ax in zip(['single_event','legacy_two'],axes):
    for row in outcomes:
        if row['scene'] != scene: continue
        p=root/row['name']/'paired/geometry_memory/trace.json'
        trace=read(p,[])
        if not trace:continue
        result=row.get('result') or {}
        ax.plot([t['step'] for t in trace],[t['goal_distance_m'] for t in trace],linewidth=1.2,label=f'{row["seed"]}: {result.get("outcome","incomplete")}')
    ax.axhline(.45,color='#23754b',linestyle='--',label='Strict arrival: 0.45 m')
    ax.set(xlabel='Public control steps (8 native ticks each)',ylabel='Distance to goal (m)',title=scene)
    ax.grid(alpha=.2)
    ax.legend(fontsize=7,ncol=2)
fig.suptitle('Frozen static confirmation — all attempted tasks\nGeometry-reference-selected benchmark; development and repeats excluded')
out=repo/'docs/figures/v652_confirmation_progress.png'
out.parent.mkdir(exist_ok=True)
fig.savefig(out,dpi=180)
classes=audit['class_successes']
physical=[x for x in audit['runs'] if x.get('passed') and x.get('native_clearance_min_m') is not None]
minimum=min((x['native_clearance_min_m'] for x in physical),default=None)
lines=['# V652 静态未知障碍新池确认','',f'**结论：{"上述有限静态基准工程验收通过，等待用户审阅" if passed else "静态工程验收未通过"}。动态未开始，SAC训练更新0。**','',f'运行结束状态`{completion["status"]}`。预锁定任务{len(tasks)}项，完成{len(outcomes)}项，其中严格到达且物理/记录审计通过{audit["strict_audited_arrivals"]}项；单障碍{classes["single_event"]}/12、双障碍{classes["legacy_two"]}/12。未执行项显式列出，不能填成成功或失败。开发修复与重复不进入这24项分母。','', '## 冻结、筛选与边界','', '在线算法为V651修订29的逐字等价副本，唯一归一化差别是runner输出根目录。新池94000001–94000360奇数单障碍、偶数双障碍；按种子顺序t0预检，在首次各类至少12项时锁定各类前12项。该停止规则在新池预检/导航均为0时注册，未来更大种子不改变选定清单。','',f'实际预检{len(screened)}项，未预检{360-len(screened)}项。参考只用于离线任务构建核验，不提供给在线导航；未找到参考不等于无解。所有初始化失败、不合格和未解记录保留。','', '目标总体限已知地图、准确定位、1或2个未知静态圆柱、固定完整自体配置域[-.44,-.375,.44,.375]、初始净空≥0.15m且存在规定运动学几何参考的任务。参考按关节/执行器一致的理想Ackermann中心转角上限约0.427221rad；它不同于V650原35°参考，不能直接将两轮成功率比较为算法总体改进。几何参考不是动力学可达证明，在线失败仍计失败。','', '## 全部预锁定任务','', '| 种子 | 场景 | 结局 | 公开步 | 终距/m | 原生日志净空/m | 审计 |','|---|---|---|---:|---:|---:|---|']
for task in tasks:
    row=by_seed.get(task['seed'])
    if row is None:
        lines.append(f'| {task["seed"]} | {task["scene"]} | 未执行 | — | — | — | — |');continue
    result=row.get('result')
    if not result:
        lines.append(f'| {task["seed"]} | {task["scene"]} | 未完整完成 | — | — | — | 未通过 |');continue
    physical=safe.get(row['name'],{})
    native=physical.get('native_clearance_min_m')
    clearance='—' if native is None else f'{native:.6f}'
    lines.append(f'| {task["seed"]} | {task["scene"]} | {result["outcome"]} | {result["public_steps"]} | {result["goal_distance_m"]:.6f} | {clearance} | {"PASS" if physical.get("passed") else "未通过/未完成"} |')
lines += ['', '## 完整门槛','', '24项至少23项严格到达且单/双各至少11/12；所有障碍接触/穿透/未知接触0、完整自体逐原生步覆盖、积分外根状态修改0、静态未知障碍不移动。每项1200公开步/900秒，第二次未成功即停止；原生控制重放需全公开完整qpos/qvel逐值匹配容差1e-8、重建净空≥0.15m。','', '| 独立核验项 | 结果 |','|---|---|']
for name,value in audit['checks'].items():lines.append(f'| {name} | {"PASS" if value else "未通过/未完成"} |')
lines += ['',f'已通过审计轨迹的重建原生净空最小：{minimum if minimum is not None else "未形成有效重放结果"}米。控制重放不增加独立样本，也不构成连续时间安全证明。','', '## 三场景同版本重复','', '固定重复V651修订29开发任务93000074双障碍、93000045单障碍、91000002单障碍；规范初态、模型、全公开qpos/qvel/ctrl、接触内容与结局均比较，容差1e-8。墙钟搜索截止造成不同路径也按不匹配处理，不自动放宽。','']
for row in audit['repeats']:lines.append(f'- `{row["name"]}`：{"PASS" if row["passed"] else "未完成/不匹配"}；{row.get("maximum_full_state_errors",row.get("reason"))}。')
lines += ['', '## 时间与后续','', f'该独立窗口使用{completion["elapsed_s"]:.3f}秒，上限{completion["limit_s"]:.3f}秒；前V650/V651窗口独立记账，不重置其失败和时限。','', '通过仅表示上述有限静态基准的工程验收，不是校准概率风险、连续时间安全、统计优越性、任意障碍/未知地图、实时性或实机结论。恢复器可接管全部控制，SAC收益未隔离。后续论文需要固定感知/足迹下对照与组件消融、到达/停滞/计算耗时和适用边界。','', '本窗口结果给用户查看后停止；即使静态通过，动态也必须等用户明确继续。新证据未远端校验前不删除原始运行。','', '![全部确认任务进展](figures/v652_confirmation_progress.png)','']
(repo/'docs/STATIC_CONFIRMATION_V652_REPORT.md').write_text('\n'.join(lines))
link=repo.parent/'outputs/Phase新池静态确认报告.md'
if not link.exists():link.symlink_to('../phase-/docs/STATIC_CONFIRMATION_V652_REPORT.md')
print(json.dumps({'report':'docs/STATIC_CONFIRMATION_V652_REPORT.md','static_engineering_acceptance_passed':passed,'completed_tasks':len(outcomes),'audited_strict_arrivals':audit['strict_audited_arrivals']},ensure_ascii=False))
