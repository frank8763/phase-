"""Final finite-benchmark report from closed, independently audited V657 data."""
import datetime
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

repo=Path(__file__).resolve().parents[2]
root=repo/'runs/v657_static_fixed_work_confirmation';window=root/'confirmation01'
def read(p,default=None):return json.loads(p.read_text())if p.exists()else default
done=read(window/'COMPLETION.json');assert done,'Report requires closed batch'
audit=read(root/'INDEPENDENT_ACCEPTANCE_AUDIT.json');assert audit
selection=read(window/'SELECTION_FREEZE.json',{'tasks':[]});rows=read(window/'CONFIRMATION_RESULTS.json',[])
passed=done['static_engineering_acceptance_passed']and audit['static_engineering_acceptance_passed']
by_seed={x['seed']:x for x in rows};by_pair={x['pair']:x for x in audit['runs']}
fig,axes=plt.subplots(1,2,figsize=(13,6.2),constrained_layout=True)
for scene,ax in zip(['single_event','legacy_two'],axes):
    for row in rows:
        if row['scene']!=scene:continue
        pair=root/row['name']/'paired';trace=read(pair/'geometry_memory/trace.json',[])
        if not trace:continue
        r=row['result'];label=f'{row["seed"]} '+(r['outcome']if r else'INCOMPLETE')
        ax.plot([x['step']for x in trace],[x['goal_distance_m']for x in trace],
                label=label,linewidth=1.3 if row['strict_success']else 2.1,
                color=None if row['strict_success']else'#ba6b21',linestyle='-'if row['strict_success']else'--')
    ax.axhline(.45,color='#197b55',linestyle=':');ax.grid(alpha=.2)
    ax.set(title=scene,xlabel='Public control steps (8 native ticks each)',ylabel='Distance to goal (m)')
    ax.legend(fontsize=6.5,ncol=3,loc='upper center',bbox_to_anchor=(.5,-.18))
fig.suptitle('Fresh frozen static confirmation: every locked task, including the HORIZON failure\n'
             'Fixed online search work; no task replacement or denominator deletion')
figures=repo/'docs/figures';figures.mkdir(exist_ok=True)
fig.savefig(figures/'v657_confirmation_progress.png',dpi=180);plt.close(fig)
nav_records=audit['runs'][:len(rows)]
native_nav=sum(x.get('native_steps',0)for x in nav_records)
native_all=sum(x.get('native_steps',0)for x in audit['runs'])
minimum_all=min((x['minimum_native_clearance_m']for x in audit['runs']if'minimum_native_clearance_m'in x),default=None)
minimum_nav=min((x['minimum_native_clearance_m']for x in nav_records if'minimum_native_clearance_m'in x),default=None)
results=[x['result']for x in rows if x['result']is not None]
ratios=[r['elapsed_s']/(r['physics_steps']*.01)for r in results if r['physics_steps']]
win=read(window/'WINDOW.json');tz=datetime.timezone(datetime.timedelta(hours=8))
start=datetime.datetime.fromtimestamp(win['started_unix'],tz)
finish=start+datetime.timedelta(seconds=done['elapsed_s'])
scene_name={'single_event':'单未知障碍','legacy_two':'双未知障碍'}
lines=['# Phase 静态未知障碍稳定验收报告 · V657','',
       '**结论：'+('预注册的有限静态基准工程验收通过，等待用户审阅。'if passed else'完整静态工程验收未通过。')+'** 动态未开始，SAC训练更新0。','',
       f'全新锁定24项任务，{audit["strict_audited_arrivals"]}/24严格到达；单障碍{audit["class_successes"]["single_event"]}/12、双障碍{audit["class_successes"]["legacy_two"]}/12。三场景同版本完整重复及27项物理审计已由独立脚本重算。原V652/V653/V654未通过记录保留，不并入本轮分母。','',
       '## 核心结果','',
       '| 项目 | 结果 |','|---|---|',
       f'| 冻结新清单严格到达 | {audit["strict_audited_arrivals"]}/24，门槛≥23/24 |',
       f'| 单/双障碍 | {audit["class_successes"]["single_event"]}/12、{audit["class_successes"]["legacy_two"]}/12，门槛各≥11/12 |',
       f'| 确认实际原生物理步 | {native_nav}，含未到达任务，不含重复 |',
       f'| 连同3次重复审计原生步 | {native_all}，重复不增独立样本 |',
       f'| 新确认原生步实际自体净空最小 | {minimum_nav:.9f}m |'if minimum_nav is not None else'| 新确认原生净空 | 未完成 |',
       f'| 含重复的原生净空最小 | {minimum_all:.9f}m；硬下限0.15m |'if minimum_all is not None else'| 含重复原生净空 | 未完成 |',
       '| 障碍接触/穿透/未知接触 | 完整逐物理步日志及控制重放分别核验；详见独立门槛表 |',
       '| 动态/训练/实机 | 均未开始 |','',
       '## 保留的未成功任务','']
failed=[x for x in rows if not x['strict_success']]
if failed:
    for row in failed:
        r=row['result']
        if r:
            lines += [f'- {row["seed"]} {scene_name[row["scene"]]}：{r["outcome"]}，{r["public_steps"]}公开步后终距{r["goal_distance_m"]:.6f}m，未到达；物理审计'+('通过。'if row['physical_audit_passed']else'未通过。')]
        else:lines +=[f'- {row["seed"]}：执行未完整完成，保留为未成功。']
else:lines+=['无已记录的未成功任务；仍须检查未执行项与完整门槛。']
lines +=['', '95000132双障碍先后执行多个安全进展前缀，较晚找到全局路径，绕行耗尽1200步。该项零障碍/未知接触、原生净空0.211213076m，但没有到达，永久计入失败，不以安全停止替代成功。通过23/24门槛不代表该负例已经解决。'if any(x['seed']==95000132 for x in failed)else'未成功、未执行与到达分开记账，不补样、不换种子。','',
          '## 本轮改动与复现修复','',
          '旧同一因果输入的2秒搜索一次在2998扩展后截断，另一次在3197扩展找到路径，造成真实轨迹差异。修订30固定在线优先搜索4000次、必要时回退16000次有效扩展，保留其他搜索代价/原语、感知、控制准入、制动尾、换挡与安全阈值。墙钟仍记录计算开销并由任务900秒硬限约束。32倍人工时钟速率差的零仿真回放得到同路径；随后三个困难基准及完整同版本重复通过，再冻结新池。预算定义本身改变，不能据此单独声称效率或机制净收益。','',
          'V653原重复还因接触分类依据含生成XML绝对目录导致原始SHA不同。新池前已注册唯一元数据规范化：仅在路径恰好指向各自pair/assets/isolated_indoor.xml且XML原始字节SHA一致时，用相对路径及已核对XML字节SHA替代该路径比较。所有位置、距离、时间、步号、分类、几何/自体标识与其他字段逐条完全相同，不删除、不舍入。三个重复的原始接触SHA并不相同，各自仍独立核对本次result并完整保留；只在上述严格路径规则下接触事件相同。','',
          '这不能改写原V652/V653/V654失败。本轮24项与3次重复均使用同一冻结V657运行源码；除输出目录外，在线算法逐字等同已通过开发的V656修订30。','',
          '## 任务选择与范围','',
          f'候选池95000001–95000600，按种子升序做t0预检；实际检查{selection.get("screened",0)}项，找到单障碍{selection.get("eligible_counts",{}).get("single_event",0)}项、双障碍{selection.get("eligible_counts",{}).get("legacy_two",0)}项合格参考，分别取前12项并在首次导航前锁定。其余{selection.get("unscreened_candidates_not_counted",0)}项未预检。初始化异常、不合格及未找到参考记录均保留，不按导航结局替换。','',
          '任务限定已知先验地图、准确定位、1或2个起初未知的静态圆柱，以及初始完整自体域净空和事前规定的运动学几何参考条件。固定域[-0.44,-0.375,0.44,0.375]，理想Ackermann中心转角上限约0.427221rad；t0参考保持原8秒/22000扩展、离散净空≥0.155m、插值位姿下界≥0.15m、参考终距≤0.28m。真值及参考仅作离线任务评价，不进入在线决策。未找到参考不等于无解，几何参考不保证动力学可达。','',
          '## 全部24项任务','',
          '| 种子 | 场景 | 结局 | 公开步 | 终距/m | 原生净空最小/m | 物理审计 |',
          '|---|---|---|---:|---:|---:|---|']
for task in selection['tasks']:
    row=by_seed.get(task['seed'])
    if row is None:
        lines.append(f'| {task["seed"]} | {scene_name[task["scene"]]} | 未执行 | — | — | — | — |');continue
    r=row['result'];record=by_pair.get(str((root/row['name']/'paired').relative_to(repo)),{})
    if not r:
        lines.append(f'| {task["seed"]} | {scene_name[task["scene"]]} | 未完整完成 | — | — | — | 未通过 |');continue
    clear=record.get('minimum_native_clearance_m');clear_text=f'{clear:.6f}'if clear is not None else'—'
    lines.append(f'| {task["seed"]} | {scene_name[task["scene"]]} | {r["outcome"]} | {r["public_steps"]} | {r["goal_distance_m"]:.6f} | {clear_text} | '+('PASS'if record.get('passed')else'未通过')+' |')
lines+=['','## 三场景完整同版本重复','',
        '基准为V656修订30开发分支，重复不进入24项分母。模型、规范初态、严格到达结局、全公开状态/控制及逐条接触事件分别核对。','',
        '| 种子 | 场景 | 独立重复核验 | 完整qpos/qvel/ctrl最大误差 |','|---|---|---|---|']
for row in audit['repeats']:
    lines.append(f'| {row["seed"]} | {scene_name[row["scene"]]} | '+('PASS'if row['passed']else'未通过')+f' | {row.get("maximum_full_state_error",row.get("reason"))} |')
lines+=['','## 独立重算全部门槛','','| 门槛 | 结果 |','|---|---|']
for key,value in audit['checks'].items():lines.append(f'| {key} | '+('PASS'if value else'未通过')+' |')
lines+=['','## 时间与计算开销','',
        f'开始{start.isoformat()}，实验关闭{finish.isoformat()}，耗时{done["elapsed_s"]:.3f}秒，上限{done["limit_s"]:.0f}秒；原批截止05:26:04.678及全夜08:00均未越过，没有延长或追加新池。','']
if ratios:
    lines +=[f'确认分支墙钟/仿真时长中位数{np.median(ratios):.2f}倍，范围{min(ratios):.2f}–{max(ratios):.2f}倍，包含本机感知、规划与完整记录开销，不含离线审计。该量不是逐控制调用p95，也不支持实时性结论。','']
lines+=['## 证据、论文边界与下一步','',
        '独立脚本：[audit_v657_final.py](../experiments/v649_static_stability/audit_v657_final.py)；协议：[冻结确认协议](../experiments/v657_static_fixed_work_confirmation/PROTOCOL.md)；完整证据：[V657精选证据](../evidence/static_acceptance_v657_20261101/README.md)。源码、模型、原始接触摘要、完整状态、控制轨迹及所有失败保留。GitHub同步以[同步状态](../SYNC_STATUS.json)为准，远端逐文件验证前不删除原始运行。','',
        '通过仅指上述有限筛选静态基准的预注册工程门槛。原生步重建净空不是连续时间安全证明；圆柱估计未独立校准风险，没有统计优越性、任意未知地图/形状、实时性或实机结论。恢复器可接管全部SAC动作，冻结SAC收益未隔离。以RAS为目标，后续仍需同输入/足迹/预算对照、机制消融及真实计算开销证据。','',
        '静态结果交用户审阅后再决定下一步。当前停止追加实验，动态、训练和实机保持0。','',
        '## 轨迹与进展查看','',
        '所有24项都列出，失败保留；示例固定取清单每类第一项，不用挑选最好看的场景代替全分母。灰色为已知地图，红色为起初未知障碍的离线真值展示，轮廓是固定规划自体域；真值不进入在线决策。绘图新增仿真0步。','',
        '![每类第一项的实际轨迹](figures/v657_first_each_class.png)','',
        '![全部确认任务的目标进展，含HORIZON](figures/v657_confirmation_progress.png)','',
        '[全部24项实际轨迹](figures/v657_all_trajectories.png)','']
report=repo/'docs/STATIC_ACCEPTANCE_V657_REPORT.md';report.write_text('\n'.join(lines))
out=repo.parent/'outputs/Phase静态最终验收报告.md'
if out.is_symlink():out.unlink()
if not out.exists():out.symlink_to('../phase-/docs/STATIC_ACCEPTANCE_V657_REPORT.md')
print(json.dumps({'static_engineering_gate_passed':passed,'report':str(report),'audited_arrivals':audit['strict_audited_arrivals'],'native_ticks':native_all},ensure_ascii=False))
