"""Generate the review report from closed persisted evidence, zero integration."""
from pathlib import Path
import json
from datetime import datetime
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v690_visible_eight_meter'
read=lambda p:json.loads(p.read_text())
a=read(root/'FINAL_ANALYSIS.json');account=read(root/'FINAL_ACCOUNT_AUDIT_V2.json');comparison=read(root/'TEACHER_LEARNER_COMPARISON.json');ledger=read(root/'ROUND_WINDOW.json');assert ledger['round_closed']
fmt=lambda t:datetime.fromtimestamp(t,ZoneInfo('Asia/Shanghai')).isoformat()
metrics={r['name']:r for r in comparison['records']}
table=['| 任务 | 相位 | 严格到达 | 公开步 | 终距m | 最低原生净空m | 学习执行/普通步 | 后备步 | 路径m |','|---|---:|---|---:|---:|---:|---:|---:|---:|']
for r in sorted(a['records'],key=lambda x:['teacher8m','learned8m_train_task','learned8m_phase_holdout','learned8m_phase_holdout_repeat'].index(x['name'])):
 m=metrics[r['name']];table.append(f"| {r['name']} | {r['phase']:.6f} | {r['strict_arrival']} | {r['public_steps']} | {r['goal_distance_m']:.6f} | {r['minimum_actual_clearance_m']:.6f} | {r['learned_actual_ordinary_steps']}/{r['ordinary_sample_count']} | {r['backup_steps']} | {m['path_length_m']:.6f} |")
train=a['training'][0]if a['training']else None
repeat=root/'learned8m_phase_holdout_repeat/paired/EXACT_REPEAT_AUDIT.json'
rr=read(repeat)if repeat.exists()else None
teacher=metrics.get('teacher8m');learner=metrics.get('learned8m_train_task')
delta='对照未完整执行。'
if teacher and learner:
 delta=f"同场景模型与规范初态下，学习版{learner['public_steps']}步、示范{teacher['public_steps']}步，少{teacher['public_steps']-learner['public_steps']}步（{(1-learner['public_steps']/teacher['public_steps'])*100:.2f}%）；路径{learner['path_length_m']:.6f} vs {teacher['path_length_m']:.6f}m，增加{(learner['path_length_m']/teacher['path_length_m']-1)*100:.2f}%，最低净空也更小。因此仅有时间步改善，不能称全面优于示范。首次完整状态/控制分叉步{comparison['teacher_vs_learner']['first_full_state_control_difference_step']}。没有旧6m权重在新8m任务的未微调实跑，不能隔离训练权重的独立因果效果。"
text=f'''# V690 可比初始观测的8米动态课程

本轮结果：**{'有限8米课程通过'if a['eight_meter_gate_passed']else'有限8米课程未通过'}**。最终独立账目审计：{account['status']}。这是空白场地、一个固定8米几何、两个预注册运动相位和条件重复的开发门，不是原复杂墙体场地动态验收，也不是统计泛化成功率。

## 任务为何重新声明

原V689八米起步没有有效actor回波，0原生步失败永久保留，见[DYNAMIC_ROUTE_COMMITMENT_V689_REPORT.md](DYNAMIC_ROUTE_COMMITMENT_V689_REPORT.md)。本轮明确另建几何：原±5m空白场地，起点(-4,-2)、目标(4,-2)，actor锚点(-2,-2)，初始遇障中心距离2m，与6米课程匹配。没有把新几何成功回填为原不可见任务成功。起点离左边界更近，不能当作仅长度变化的单变量对照。

原47束/3m测距、噪声与漏检/有效hit筛选全部保留。actor物理直径0.20m、振幅0.25m、最大速度0.08m/s；完整扫掠不堵中央保护区，并有全车身连续参考净空下界>=0.15m。两相位零积分预检均独立重建初始原始测距包、因果位置速度联合外覆盖和329未来时刻覆盖，未刷新随机数、没有真值输入在线规划器。真实导航也执行同一初始前置检查。

## 全部实际结果

{chr(10).join(table)}

两相位不是两个独立随机场景，重复也不加入成功率分母。所有失败/未执行项见runs/v690_visible_eight_meter/FINAL_ANALYSIS.json，原V688/V689失败不改。

## 训练与控制参与

{('使用通过全审计的8m相位0示范普通实际执行'+str(train['samples'])+'个样本，从旧6m模型微调固定512次；归一化与12→32→32→4 tanh架构不变，Adam.001/seed688/batch128/float64。初始MSE '+format(train['initial_mse'],'.9f')+'，最终 '+format(train['final_mse'],'.9f')+'，NumPy/Torch推理最大差 '+str(train['numpy_torch_max_difference'])+'。新权重SHA256 `'+train['model_sha256']+'`。')if train else'前置失败，未训练。'}

训练网络的12维输入是车体坐标下的局部参考、朝向、自车速度、上次合法控制和期望转向/速度，输出执行器目标提案；动态障碍检测、运动联合外覆盖、路径规划与安全准入仍由因果模块承担。网络输入没有障碍真值或真值未来。

本轮新增监督更新{a['supervised_gradient_updates']}；旧6m已512，因此本研究课程累计{512+a['supervised_gradient_updates']}。这是独立机动提案网络的监督学习，冻结Phase20 SAC与Phase6没有训练更新。新模型在第一次学习评估前冻结，两个相位与重复不再训练。最终独立审计逐样本核对被执行普通候选、合法目标、样本哈希、归一化、初末损失与模型哈希；不以训练损失替代闭环到达。

{delta}

独立审计V1原FAIL保留：它假设旧权重按完整float64载入，初始MSE复算与日志差3.2747e-11。零积分复核确认，冻结训练源码用torch.tensor(list)默认float32再拷入float64网络，最大单参数舍入1.48165e-8；按实际已冻结转换复算初始损失与日志完全一致，最终损失同样匹配。V2重建实际载入规则并核对原FAIL留存，没有改权重、控制、安全门或重跑训练/导航。运行中的训练运算为float64，但不能称热启动参数逐位继承旧float64精度；后续候选应显式声明载入dtype。证据INITIALIZATION_PRECISION_DIAGNOSIS.json，V1/V2分别保留。

## 物理与复现证据

新增导航原生积分{a['new_navigation_native_steps']}，完整原生控制重放{a['full_replay_native_steps']}，私有预测积分{a['private_prediction_integrations']}。所有实际积分均经./run_phase.sh隔离入口、单CPU顺序；完整原车/地面/求解器参数独立比较保持。原生步零障碍/穿透/未知接触、实际净空>=0.15m、完整自体域、命令幅值/速率和逐原生实际ctrl、无积分外根状态改写全部逐项审计。保留普通、后备与切回的完整状态接续证据。

原2.4s动作预测、首8+尾320原生步的3.28s保留尾、预测净空0.155m、自体0.002m、末速0.025m/s门槛均不变；V689路线当前占据重核验/同路线弧长停滞判别保持，没有本轮算法调参。329时刻覆盖是本有限运动轨迹的评价器检验，不是无限时域安全定理。

完整重复：{json.dumps(rr['errors'],ensure_ascii=False)if rr else'未执行'}。{('模型、规范初态及真实接触事件匹配；原始接触摘要分别保留，只规范化已验证XML字节一致的生成目录。')if rr and rr['passed']else'不能称完整重复通过。'}

## 窗口与范围

开始{fmt(ledger['started_unix'])}，硬截止{fmt(ledger['absolute_deadline_unix'])}，实际闭批{ledger['elapsed_s']:.3f}s；5400秒原截止未延长。预检{ledger['preflight_attempts']}/2、导航尝试{ledger['navigation_attempts']}/4、监督更新{ledger['supervised_gradient_updates']}/512；SAC更新/独立确认/实机/Stage访问均0。此次闭批后不自动追加10米或原场地实验。

下一步要区分长度、初始可见性和边界机动空间，并在冻结协议下逐步回到有静态结构的场地，补独立场景与规范基线/消融。本轮只能加强有限课程闭环可行性证据，尚不足以证明RAS所需的算法创新优势。

## 可复核入口

- 协议：experiments/v690_visible_eight_meter/PROTOCOL.md；源码/文档/旧与新权重事前冻结清单位于runs/v690_visible_eight_meter/curriculum01。
- 全账目：runs/v690_visible_eight_meter/FINAL_ACCOUNT_AUDIT_V2.json（原V1失败保留于FINAL_ACCOUNT_AUDIT.json）、FINAL_ANALYSIS.json、TEACHER_LEARNER_COMPARISON.json。
- 完整内容寻址证据：evidence/dynamic_visible_eight_meter_v690_20261101；每原文件字节哈希回读核验，原始runs在远端验证前保留。
- 图：figures/dynamic_visible_eight_meter_v690.png（并有独立PDF）。
'''
(repo/'docs/DYNAMIC_VISIBLE_EIGHT_METER_V690_REPORT.md').write_text(text)
print('WROTE_CLOSED_EVIDENCE_REPORT')
