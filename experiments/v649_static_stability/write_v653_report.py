"""Final same-list continuation report with original interruption visible."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2]
root=repo/'runs/v653_static_log_recovery';window=root/'continuation01'
def read(p,default=None):return json.loads(p.read_text())if p.exists()else default
done=read(window/'COMPLETION.json');assert done,'Final report needs closed continuation'
audit=read(root/'INDEPENDENT_ACCEPTANCE_AUDIT.json');assert audit
rows=read(window/'CONFIRMATION_RESULTS.json',[]);tasks=read(window/'SELECTION_FREEZE.json')['tasks'];by_seed={x['seed']:x for x in rows}
passed=done['static_engineering_acceptance_passed']and audit['static_engineering_acceptance_passed']
native_by={x['pair']:x for x in audit['runs']}
fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
for scene,ax in zip(['single_event','legacy_two'],axes):
    for row in rows:
        if row['scene']!=scene:continue
        branch=repo/row['run_root']/row['name']/'paired/geometry_memory';trace=read(branch/'trace.json',[])
        if not trace:continue
        label=str(row['seed'])+(' LOG INTERRUPTION (failure)'if row['result']is None else' '+row['result']['outcome'])
        ax.plot([x['step']for x in trace],[x['goal_distance_m']for x in trace],linewidth=1.3,label=label,linestyle='--'if row['result']is None else'-')
    ax.axhline(.45,color='#23754b',linestyle=':');ax.set(title=scene,xlabel='Public control steps (8 native ticks each)',ylabel='Distance to goal (m)');ax.grid(alpha=.2);ax.legend(fontsize=7,ncol=2)
fig.suptitle('Locked static benchmark: all attempts, including original logging interruption\nEquivalent decision code; diagnostic repair declared; no replacement or denominator deletion')
plot=repo/'docs/figures/v653_same_list_confirmation.png';plot.parent.mkdir(exist_ok=True);fig.savefig(plot,dpi=180)
lines=['# 静态未知障碍固定清单验收与日志续验','',f'**结论：{"有限静态基准工程门槛达到，等待用户审阅"if passed else"静态稳定验收未通过"}。动态未开始，训练更新0。**','',f'原锁定24项中，已有{len(rows)}项尝试记录，{audit["strict_audited_arrivals"]}项严格到达并通过独立物理审计；单障碍{audit["class_successes"]["single_event"]}/12，双障碍{audit["class_successes"]["legacy_two"]}/12。原94000040双障碍日志中断永久计1项未成功，没有重跑替补或从分母删除。未执行任务显式列出，不补成成功/失败。','', '## 必须保留的运行来源说明','', 'V652原冻结批次前4项到达，第5项在19公开/152原生步后因规划统计字典自引用发生日志递归异常，原批次已停止且不通过。原代码、COMPLETION和中断记录保持不变。其已执行前缀重放逐值匹配、净空0.601090745m、接触0；前缀安全核验不代表到达，也不覆盖未执行的未来。','', 'V653仅将两处诊断统计赋值改为字典浅拷贝，避免写日志自引用；感知、候选生成、路径选择、阈值、控制器及所有决策模块不变。runner只归一化输出根目录与两处dict拷贝后，逐字恢复原V652冻结哈希。零仿真日志回归通过。它按原清单顺序续跑未执行19项，仍用V652原14400秒和23:40:51.861截止时间。','', '因此本报告评价同一冻结决策算法，但不声称所有任务使用完全同一runner字节或整批从未中断；工程门槛若达到，也应明确这次诊断修复。论文的完整独立确认仍应报告这一来源限制。','', '## 任务选择与适用范围','', '全新池94000001–94000360按种子顺序t0预检，286项后单障碍19项、双障碍12项找到合格几何参考，导航前锁定各类前12项；74个候选未预检。不按导航结果选种子、替补或追加样本。未找到参考不等于无解。真值参考只作离线任务评价，不进入在线导航。','', '范围限已知地图、准确定位、1或2个未知静态圆柱、固定完整自体配置域和规定几何参考的任务；参考采用自体关节一致的理想Ackermann中心转角上限约0.427221rad，参考不是动力学可达证明。这与V650原35°参考条件不同，不能直接将两轮比例视为总体算法提升。','', '## 全部24项固定任务','', '| 种子 | 场景 | 来源/结局 | 公开步 | 终距/m | 已执行原生净空最小/m | 独立审计 |','|---|---|---|---:|---:|---:|---|']
for task in tasks:
    row=by_seed.get(task['seed'])
    if row is None:lines.append(f'| {task["seed"]} | {task["scene"]} | 未执行 | — | — | — | — |');continue
    pair=repo/row['run_root']/row['name']/'paired';branch=pair/'geometry_memory';r=row['result'];interrupted=r is None
    prefix=read(branch/'interrupted.json',{})if interrupted else r
    trace=read(branch/'trace.json',[]);distance=trace[-1]['goal_distance_m']if trace else None
    record=native_by.get(str(pair.relative_to(repo)),{});clearance=record.get('minimum_native_clearance_m');source='原V652'if'v652'in row['run_root']else'日志修复续验'
    lines.append(f'| {task["seed"]} | {task["scene"]} | {source}/{"日志中断未成功"if interrupted else r["outcome"]} | {prefix.get("public_steps","—")} | {distance:.6f} | {clearance:.6f} | {"前缀PASS，任务未成功"if interrupted and record.get("passed") else "PASS"if record.get("passed")else"未通过/未完成"} |'if distance is not None and clearance is not None else f'| {task["seed"]} | {task["scene"]} | {source}/未完整完成 | {prefix.get("public_steps","—")} | — | — | 未通过 |')
lines+=['','## 独立重算门槛','','门槛未放宽：原24项至少23项严格到达、单/双各至少11/12，所有已执行原生步障碍接触/穿透/未知接触0、完整自体覆盖、静态障碍不移动、积分外根状态修改0、净空≥0.15m。一次原日志中断保留为失败，所以剩余19项必须全成功。第二次未成功或任意安全/源码/模型审计失败立即停止。','','| 核验项 | 结果 |','|---|---|']
for name,ok in audit['checks'].items():lines.append(f'| {name} | {"PASS"if ok else"未通过/未完成"} |')
lines+=['','## 三场景同版本重复','','按原预定V651修订29基准，比较规范初态、模型、每公开步完整qpos/qvel/ctrl、接触内容摘要和到达结局，容差1e-8。重复不进入24项分母。','']
for row in audit['repeats']:lines.append(f'- {row["seed"]} {row["scene"]}：{"PASS"if row["passed"]else"未完成/不匹配"}；{row.get("maximum_full_state_error",row.get("reason"))}。')
lines+=['','## 时间、证据与研究边界','',f'从原V652起点计耗时{done["elapsed_from_original_origin_s"]:.3f}秒，上限{done["limit_s"]:.3f}秒，截止未重置。原V652失败报告见[原批次记录](STATIC_CONFIRMATION_V652_REPORT.md)，开发修复见[路径进展修复](STATIC_REPAIR_REPORT.md)。','', '原始运行和中断完整保留；GitHub远端验证前不删除。原生控制重放是审计而非新增独立试验，公开完整状态匹配也不证明物理连续时间安全。','', '工程门槛只适用于上述有限筛选静态圆柱基准。没有校准概率风险、连续时间安全、统计优越性、任意未知地图/障碍、实时性或实机结论；恢复器可接管全部控制，SAC收益未隔离。RAS论文仍需同输入/足迹/预算下对照、组件消融和真实计算开销。','', '给用户查看本报告后停止；动态必须等用户明确继续。','', '![固定清单全部尝试的进展](figures/v653_same_list_confirmation.png)','']
(repo/'docs/STATIC_SAME_LIST_ACCEPTANCE_REPORT.md').write_text('\n'.join(lines))
out=repo.parent/'outputs/Phase静态最终验收报告.md'
if not out.exists():out.symlink_to('../phase-/docs/STATIC_SAME_LIST_ACCEPTANCE_REPORT.md')
print(json.dumps({'static_engineering_gate_met':passed,'attempt_records':len(rows),'audited_arrivals':audit['strict_audited_arrivals'],'report':'docs/STATIC_SAME_LIST_ACCEPTANCE_REPORT.md'},ensure_ascii=False))
