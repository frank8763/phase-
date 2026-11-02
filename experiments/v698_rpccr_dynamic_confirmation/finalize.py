"""Zero-simulation closure, honest report and complete evidence archive."""
import datetime,fcntl,json,os,subprocess,sys
from pathlib import Path
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent;root=repo/'runs/v698_rpccr_dynamic_confirmation'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
lock=(root/'finalize.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if (root/'FINALIZED.json').exists():print((root/'FINALIZED.json').read_text());raise SystemExit(0)
assert read(root/'ROUND_WINDOW.json')['round_closed'],'ROUND_NOT_CLOSED'
os.environ['OPENBLAS_NUM_THREADS']='1'
run=subprocess.run([sys.executable,'-B',str(own/'audit_final.py')],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
(root/'final_audit.console').write_bytes(run.stdout);assert run.returncode==0,'FINAL_AUDITOR_PROCESS_ERROR'
a=read(root/'FINAL_INDEPENDENT_AUDIT.json');c=read(root/'confirmation01/COMPLETION.json');ledger=read(root/'ROUND_WINDOW.json');passed=a['status']=='FINITE_MOVING_DISCOVERY_CONFIRMATION_PASS'
now=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();title='有限动态课程确认通过' if passed else '本次动态确认未通过'
error=read(root/'confirmation01/ERROR.json') if (root/'confirmation01/ERROR.json').exists() else None
rows=[];main={x['slot']:x for x in a['records'] if not x['repeat']}
for task in read(own/'TASK_LIST.json'):
    r=main.get(task['slot']);state='未执行' if r is None else '完整链到达' if r['functional_arrival'] else '未成功/证据异常'
    rows.append('| %02d | %s | %s | %s | %s | %s |'%(task['slot'],task['seed'],state,'—' if r is None else r['public_steps'],'—' if r is None else r['goal_distance_m'],'—' if r is None else r['minimum_actual_clearance_m']))
rate='未执行完整24项，不报全24成功率' if a['full24_navigation_success_rate'] is None else f"{a['main_functional_arrivals']}/24 = {a['full24_navigation_success_rate']:.2%}"
report=f'''# RP-CCR V698：{title}

收尾时间：{now}。独立零积分终审状态：**{a['status']}**。原冻结24任务中尝试{a['main_navigation_attempted']}项、生成完整结果{a['main_result_count']}项、完整链到达{a['main_functional_arrivals']}项，未执行{a['main_navigation_unexecuted']}项；{rate}。正/反初始运动方向到达数：{a['groups']}。完整重复尝试{a['complete_repeats_attempted']}/3。

本轮使用全新噪声种子98010001–98010024和事前连续全周期正/反方向相位规则；冻结V697初始化修复后的导航算法、8m提案网络与全部安全门不变，算法修订/训练/SAC更新0。不是继续旧夜间或覆盖V696失败。来源及分母见[事前协议](../experiments/v698_rpccr_dynamic_confirmation/PROTOCOL.md)。

## 实际结果和完整分母

| 任务 | 噪声种子 | 状态 | 公开步 | 终距m | 最低原生实际净空m |
|---|---|---|---|---|---|
{chr(10).join(rows)}

三项预定完整重复为slot1/8/20。逐公开qpos/qvel/ctrl/mocap、模型、规范初态、真实接触事件和首次发现事件要求一致；原始接触SHA分别保留，只允许原注册XML路径来源规范化。详细重复误差与全门审核见[独立终审](../runs/v698_rpccr_dynamic_confirmation/FINAL_INDEPENDENT_AUDIT.json)。

## 门槛与实际账目

门槛：24项至少23完整链到达、两方向各≥11/12，三项预定完整重复；每原生步净空≥.15m、障碍接触/穿透/未知0、自体与合法ctrl/速率覆盖、无积分外根改写、全部控制状态重放≤1e-8、因果原始包/集合重建、329执行预测与657规划包含、路线与全部保留尾证书审核。审核未通过时，零碰撞或已到达前缀不能替代完整确认通过。

记录下限：导航原生{a['known_navigation_native_steps']}、重放原生{a['known_native_replay_steps']}、私有积分{a['known_private_integrations']}。账目是否完整精确：导航{a['native_account_exact']}、重放{a['replay_account_exact']}、私有{a['private_account_exact']}；False表示还有未恢复账目，不把未知填0。最低已完成任务实际净空{a['minimum_actual_clearance_m']}m。实际批窗口{ledger['elapsed_s']:.3f}s，上限15000s，原绝对截止不延长。

停止原因：{None if error is None else error['message']}。本轮已闭批，未执行项目不补种子、不刷池；任何下一轮修订需先依据本轮日志定位原因并单独冻结有限协议。旧成功/失败/截止全部保留。原始runs不删除。

## 结论范围

{title}只适用于固定空白8m、一个直径0.20m/振幅0.25m/最大速0.08m/s小障碍、真实途中进入3m量程与公开3m起步排除先验。它不是复杂原场地、任意遮挡突入、多个/更快障碍、长距离、实时性或实机验收；不证明RP-CCR原创性、机制净收益或无限安全。

下一方法研究仍围绕RP-CCR风险、目标进展和可续接走廊恢复，并做同输入/车辆/传感/控制/计算预算对照和消融，见[研究设计](RPCCR_DYNAMIC_MECHANISM_EVIDENCE_PLAN_20261102.md)。

[全证据归档](../evidence/rpccr_dynamic_confirmation_v698_20261102/README.md)。工人原始输出位于runs/v697_rpccr_dynamic_initialization/v698_*，批账目位于runs/v698_rpccr_dynamic_confirmation；按冻结来源明确标注，没有新导航算法或新权重。
'''
(repo/'docs/RPCCR_DYNAMIC_CONFIRMATION_V698_REPORT.md').write_text(report)
(root/'REPORT.md').write_text(report)
current_path=repo/'CURRENT_EXPERIMENT.json';current=read(current_path)
if current.get('protocol')=='experiments/v698_rpccr_dynamic_confirmation/PROTOCOL.md':
    current.update(status='V698_FINITE_DYNAMIC_CONFIRMATION_PASS_CLOSED' if passed else 'V698_CONFIRMATION_NOT_PASSED_CLOSED',active_run=None,active_window=None,active_pid=None,active_entrypoint=None,execution_window_closed=True,requires_user_review_before_next_experiment=True,report='docs/RPCCR_DYNAMIC_CONFIRMATION_V698_REPORT.md',evidence='evidence/rpccr_dynamic_confirmation_v698_20261102',last_observed_at=now,v698_result={k:v for k,v in a.items() if k not in ['records','repeat_details']})
    dump(current_path,current)
    (repo/'REVIEW_PENDING').write_text(f'V698 closed: {a["status"]}. Read docs/RPCCR_DYNAMIC_CONFIRMATION_V698_REPORT.md. No automatic new simulations, repairs, seeds, training or distance extension.\n')
note=f'\n\n## V698 动态冻结确认收尾\n{now}，独立状态{a["status"]}；24项中尝试{a["main_navigation_attempted"]}、完整链到达{a["main_functional_arrivals"]}、未执行{a["main_navigation_unexecuted"]}；正反组{a["groups"]}，重复尝试{a["complete_repeats_attempted"]}/3。导航/重放/私有已知账目{a["known_navigation_native_steps"]}/{a["known_native_replay_steps"]}/{a["known_private_integrations"]}；精确性分别{a["native_account_exact"]}/{a["replay_account_exact"]}/{a["private_account_exact"]}。训练与算法修订0，原V696/V697和旧夜间账目不变。报告docs/RPCCR_DYNAMIC_CONFIRMATION_V698_REPORT.md，闭批后不自动追加。\n'
with (repo/'RESEARCH_STATUS.md').open('a') as f:f.write(note)
archive=subprocess.run([sys.executable,'-B',str(own/'archive_evidence.py')],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150)
(repo/'runs/v698_archive.console').write_bytes(archive.stdout);assert archive.returncode==0,'ARCHIVE_ERROR'
archive_result=json.loads(archive.stdout.decode().splitlines()[-1])
with (repo/'evidence/README.md').open('a') as f:f.write(f'\n\n## V698 RP-CCR动态独立确认\n[完整证据](rpccr_dynamic_confirmation_v698_20261102/README.md)独立结论{a["status"]}，尝试{a["main_navigation_attempted"]}/24、完整链到达{a["main_functional_arrivals"]}、未执行{a["main_navigation_unexecuted"]}，重复{a["complete_repeats_attempted"]}/3；全部已归档字节解压哈希核验通过，原始runs保留。见[实际报告](../docs/RPCCR_DYNAMIC_CONFIRMATION_V698_REPORT.md)。不凭归档完成宣称导航成功。\n')
dump(root/'FINALIZED.json',{'status':a['status'],'finalized_at':now,'report':'docs/RPCCR_DYNAMIC_CONFIRMATION_V698_REPORT.md','archive':archive_result,'automatic_new_simulation':False,'needs_chat_review_commit_and_bounded_sync':True,'simulation_steps_in_finalizer':0})
print((root/'FINALIZED.json').read_text())
