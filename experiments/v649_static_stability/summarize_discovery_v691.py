"""Closed discovery result, diagnostic figures and report; zero integrations."""
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v691_discovery_in_motion';pair=root/'moving_discovery01/paired';cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
ledger=read(root/'ROUND_WINDOW.json');assert ledger['round_closed'];r=read(cell/'result.json');chain=read(pair/'DISCOVERY_CHAIN_AUDIT.json');d=chain['details'];diag=read(root/'FAILURE_DIAGNOSIS.json');probe=read(root/'CURRENT_ONLY_SPATIAL_PROBE.json');replay=read(pair/'NATIVE_REPLAY_AUDIT.json');account=read(root/'FINAL_ACCOUNT_AUDIT.json');execution=lines(cell/'v648_execution.jsonl');coverage=lines(cell/'forecast_coverage.jsonl')
analysis={'status':ledger['status'],'moving_discovery_gate_passed':False,'strict_arrival':r['strict_safe_arrival'],'outcome':r['outcome'],'goal_distance_m':r['goal_distance_m'],'actual_navigation_tasks':1,'new_navigation_native_steps':r['physics_steps'],'full_control_replay_native_steps':replay['replay_integration_steps'],'private_prediction_integrations':r['prediction_steps'],'maximum_full_replay_error':max(replay[k]for k in ['maximum_full_public_qpos_error','maximum_full_public_qvel_error','maximum_public_mocap_error']),'minimum_actual_clearance_m':r['minimum_dynamic_native_clearance_m'],'first_discovery_and_brake':d,'functional_checks':chain['checks'],'physical_command_audit':read(pair/'INDEPENDENT_CANONICAL_AUDIT.json')['status'],'final_account_audit':account['status'],'finite_forecast_decision_frames':len(coverage),'finite_forecast_samples':len(coverage)*329,'full_repeat_executed':False,'repeat_skip_reason':'MAIN_STRICT_ARRIVAL_FAILED','diagnostic_new_simulation_integrations':0,'supervised_gradient_updates':0,'sac_gradient_updates':0,'stage_access':0,'real_robot':0,'independent_confirmation':0,'actual_whole_round_elapsed_s':ledger['elapsed_s'],'original_absolute_deadline_unix':ledger['absolute_deadline_unix'],'raw_deleted':False,'scope':'finite natural range-entry with public startup3m center-exclusion prior; observed/stopped/replanned/continued but not arrived'}
(root/'FINAL_ANALYSIS.json').write_text(json.dumps(analysis,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
xy=np.asarray([[-4.,-2.],*[e['qpos_full'][:2]for e in execution]]);tt=np.asarray([0.,*[e['time']for e in execution]]);speed=np.asarray([0.,*[np.linalg.norm(np.asarray(e['qvel_full'])[:2])for e in execution]]);fig,axes=plt.subplots(1,3,figsize=(15,4.4))
axes[0].plot(xy[:,0],xy[:,1],label='Actual executed');post=read(cell/'planning_0073.json');path=np.asarray(post['path']);axes[0].plot(path[:,0],path[:,1],ls='--',alpha=.45,label='Post-stop reference');axes[0].scatter([-4,4],[-2,-2],c='black',marker='*',s=60,label='Start / goal');axes[0].scatter([xy[-1,0]],[xy[-1,1]],c='red',marker='x',s=70,label='Final non-arrival');axes[0].plot([-.6,-.6],[-2.25,-1.75],c='red',lw=8,alpha=.3,label='Actor center sweep');axes[0].set_aspect('equal',adjustable='datalim');axes[0].set_xlabel('x (m)');axes[0].set_ylabel('y (m)');axes[0].set_title('Detected, stopped, replanned; not arrived');axes[0].legend(fontsize=6)
axes[1].plot(tt,speed);axes[1].axvline(d['first_detection_sim_time_s'],c='tab:orange',ls='--',label='First causal detection');axes[1].axvline(d['first_detection_sim_time_s']+3.28,c='tab:green',ls='--',label='Certified stop complete');axes[1].axhline(.025,c='gray',ls=':',label='Stop threshold');axes[1].set_xlabel('Simulated time (s)');axes[1].set_ylabel('Actual planar speed (m/s)');axes[1].set_title('Physical motion before discovery');axes[1].legend(fontsize=6)
curves=read(root/'FAILURE_GEOMETRY_CURVES.json');axes[2].plot(curves['times_s'],curves['causal_stationary_clearance_m'],label='Causal stationary-pose union');axes[2].plot(curves['times_s'],curves['truth_stationary_clearance_m'],label='Retrospective physical geometry');axes[2].axhline(.155,c='black',ls='--',label='Admission threshold');axes[2].axhline(diag['future_projection_start_clearance_m'],c='gray',ls=':',label='Projected spatial start');axes[2].set_xlabel('Hypothetical future time (s)');axes[2].set_ylabel('Envelope clearance (m)');axes[2].set_title('Final saved pose: geometry only');axes[2].legend(fontsize=6)
for ax in axes:ax.grid(alpha=.2)
fig.tight_layout();out=repo/'docs/figures';fig.savefig(out/'dynamic_discovery_v691.png',dpi=180);fig.savefig(out/'dynamic_discovery_v691.pdf');plt.close(fig)
fmt=lambda t:datetime.fromtimestamp(t,ZoneInfo('Asia/Shanghai')).isoformat()
report=f'''# V691 车辆正常行驶后首次发现动态障碍

**本轮完整通行未通过。** 已实现真实行驶→首次检测→完整制动→因果重规划→继续移动，但第408步因后续预测/后备接续失败停止，终距{r['goal_distance_m']:.6f}m。不能把检测、停车、零接触或账目审计PASS当作完整到达。

## 场景与假设

原±5m空白场地，起点(-4,-2)、目标(4,-2)，原车/地面/求解器。动态圆柱从t0就真实存在于锚点(-0.6,-2)，初始中心距3.4m；直径0.20m、y振幅0.25m、最大速度0.08m/s。初始确在原3m传感范围外，47束/噪声/漏检/有效hit筛选不变，没有定时生成、回波隐藏或瞬移。完整扫掠不堵中央保护区，有>=0.15m连续几何参考前置。

公共启动条件为t0未知中心距起点>=3m，它是已声明的受控场地清空先验，**不是带漏检测距无回波推导的自由空间证书**。首次发现前，按每坐标速度<=0.12m/s，未知中心外域为半径max(0,3-sqrt(2)*0.12*t)初始圆的补集。预测净空下界为该半径减完整足迹角点最远半径、再减actor0.10m半径；与原场地净空共同准入，普通控制保留原完整328步后备。3000组0积分几何/可达验证通过。适用范围不含任意遮挡贴近突入或未知空间无条件安全。

## 实际功能链

| 环节 | 证据 | 结果 |
|---|---|---|
| 正常行驶后首次发现 | 第{d['first_detection_step']}步，t={d['first_detection_sim_time_s']:.2f}s；已前进{d['forward_progress_before_discovery_m']:.6f}m，实际速度{d['speed_before_discovery_m_s']:.6f}m/s，此前10步最低速度{d['minimum_last10_speed_m_s']:.6f}m/s | 通过 |
| 安全减速至停止 | 完整328原生/41公开步制动，预测最低净空{d['stop_minimum_causal_clearance_m']:.6f}m；实际末速{d['terminal_stop_speed_m_s']:.9f}m/s；完整状态/控制误差0 | 通过 |
| 新因果路线 | 停稳后第{d['first_post_stop_replan_step']}步重规划，参考与发现前不同，新路线当前联合占据净空{d['new_reference_current_causal_clearance_m']:.6f}m | 通过 |
| 新路线实际执行 | 制动结束后实际位移{d['post_stop_actual_displacement_m']:.6f}m | 通过 |
| 最终严格到达 | 408公开/3264原生后终距{r['goal_distance_m']:.6f}m，原门槛0.45m | **未通过** |
| 成功条件完整重复 | 因主任务未严格到达，未启动 | 未执行 |

初始观察步数0，首次发现32仅由第一帧有效未知回波触发，之前32步正在运动；这与V690起初32步静止观察不同。逐帧原包重建Tracker状态、首次检测和329时刻未来覆盖均匹配，409个决策帧包含最后一个未执行拒绝，覆盖计数134561，不能当作独立实验数。

## 未到达原因的零积分定位

第408步仍有新鲜有效actor回波（age=0，1条严格未知射线），不存在最后阶段完全失去检测。当前联合外覆盖净空{diag['current_joint_causal_clearance_m']:.6f}m，实际准入函数保守粗界{diag['operational_current_gate_clearance_m']:.6f}m；将未来3.28s扫掠压成空间障碍后，起点净空变成{diag['future_projection_start_clearance_m']:.6f}m。原搜索返回START_BELOW_HARD_FLOOR、展开0节点，不能据此证明物理场景无路。

最后一次第404步切回测试的16个有限候选全部因未来净空拒绝，最佳{diag['last_backup_return_best_rejected_minimum_m']:.6f}<0.155m。第367步预留的有限前进制动尾完整执行到407，末速0.001711m/s，无法更新证书后缓存耗尽；408重新规划又被未来空间投影的起点检查拒绝。直接在当前因果占据固定状态上做一次0积分空间探针，{probe['spatial_search']['expanded']}节点找到到目标的空间参考，最低{probe['spatial_search']['minimum_clearance_m']:.6f}m。它没有时间表、执行器加速或保留尾验证，**不是救回成功**。

固定最终位姿的未来几何反事实：因果外覆盖在未来{diag['first_stationary_future_causal_below_0155_s']:.2f}s首次低于0.155m，而评价器已知实际运动扫掠最低{diag['retrospective_stationary_pose_true_sweep_minimum_m']:.6f}m。这是已保存位姿上的几何对比，既不是新停车仿真，也不证明全部合法动作无解。测距维持检测但每帧多为1条回波、y速度外区间仍宽，信息保守性、空间投影与未来安全门不一致、有限后备可续接性共同影响，不能归为单一根因或笼统说算法/场景不行。

## 物理、账目与边界

最低实际原生净空{r['minimum_dynamic_native_clearance_m']:.6f}m，障碍接触/穿透/未知0；3264导航原生与3264完整控制重放全qpos/qvel/mocap误差0。普通/后备/新制动命令幅值/速率、自体域、原生ctrl、完整状态接续、无积分外根改写、原车/地面/求解器、因果/投影/路线/尾审计通过。私有预测{r['prediction_steps']}原生积分，全部经./run_phase.sh、单CPU顺序。V690网络SHA fc9d3132c912033e2ec04cd8ae1ce236c818c484d5b96961c6f3dc1b0548b527冻结，提案训练/SAC/Stage/实机/独立确认0。模型字节依赖副本与来源也保留在本轮dependencies，未训练或改写旧模型。

开始{fmt(ledger['started_unix'])}，原硬截止{fmt(ledger['absolute_deadline_unix'])}，实际闭批{ledger['elapsed_s']:.3f}s。最多1前置/1主导航+成功条件重复；实际1前置/1主导航，严格到达0，重复0。失败按事前依赖提前关闭，不延长原截止、不换种子、不改冻结算法或门槛。之后所有诊断都是0积分，原COMPLETION和DISCOVERY_CHAIN_AUDIT=FAIL保留。FINAL_ACCOUNT_AUDIT={account['status']}仅说明账目与证据一致，完整功能门仍false。

## 下一轮具体修复方向，尚未实跑

先在已锁定408完整状态上验证：起点准入使用当前因果占据，候选路径必须带时间与合法执行器动态，继续逐原生0.155净空/0.002自体/0.025末速和完整有限尾；不能仅换成当前空间规划就称解决。进一步选择能续接的逃离/观察机动，使后备结束前能更新有效证书；改善每帧单回波下速度信息的主动观测。任何新控制候选需独立冻结与有界协议，本轮没有追加导航或训练。

## 复核入口

- 协议：experiments/v691_discovery_in_motion/PROTOCOL.md。
- 功能FAIL：runs/v691_discovery_in_motion/moving_discovery01/paired/DISCOVERY_CHAIN_AUDIT.json；全账目FINAL_ACCOUNT_AUDIT.json、FINAL_ANALYSIS.json。
- 离线原因：FAILURE_DIAGNOSIS.json、CURRENT_ONLY_SPATIAL_PROBE.json，明确0积分与能力边界。
- 完整内容寻址证据：evidence/dynamic_discovery_v691_20261101，原始runs保留，未远端核验不清理。
- 图：figures/dynamic_discovery_v691.png与PDF；右图全部为固定保存位姿的几何反事实。
'''
(repo/'docs/DYNAMIC_DISCOVERY_V691_REPORT.md').write_text(report)
print(json.dumps(analysis,indent=2))
