"""Zero-simulation closure, honest report and complete evidence archive."""
import datetime,fcntl,json,os,subprocess,sys
from pathlib import Path
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent;root=repo/'runs/v700_rpccr_dynamic_continuation'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
lock=(root/'finalize.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if (root/'FINALIZED.json').exists():print((root/'FINALIZED.json').read_text());raise SystemExit(0)
assert read(root/'ROUND_WINDOW.json')['round_closed'],'ROUND_NOT_CLOSED'
os.environ['OPENBLAS_NUM_THREADS']='1'
run=subprocess.run([sys.executable,'-B',str(own/'audit_final.py')],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
(root/'final_audit.console').write_bytes(run.stdout);assert run.returncode==0,'FINAL_AUDITOR_PROCESS_ERROR'
a=read(root/'FINAL_INDEPENDENT_AUDIT.json');c=read(root/'continuation01/COMPLETION.json');ledger=read(root/'ROUND_WINDOW.json');passed=a['status']=='FINITE_MOVING_DISCOVERY_SAME24_CONTINUATION_PASS'
now=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();title='有限动态课程跨版本接续通过' if passed else '本次动态接续未通过'
error=read(root/'continuation01/ERROR.json') if (root/'continuation01/ERROR.json').exists() else None
rows=[];main={x['slot']:x for x in a['records'] if not x['repeat']}
for task in read(own/'TASK_LIST.json'):
    r=main.get(task['slot']);state='未执行' if r is None else ('原V698轨迹复核到达' if r['origin']=='V698_EXISTING_TRAJECTORY_V699_REAUDITED' else '本轮完整链到达') if r['functional_arrival'] else '未成功/证据异常'
    rows.append('| %02d | %s | %s | %s | %s | %s |'%(task['slot'],task['seed'],state,'—' if r is None else r['public_steps'],'—' if r is None else r['goal_distance_m'],'—' if r is None else r['minimum_actual_clearance_m']))
rate='未执行完整24项，不报全24成功率' if a['full24_navigation_success_rate'] is None else f"{a['main_functional_arrivals']}/24 = {a['full24_navigation_success_rate']:.2%}"
provenance_note=f"原V698始终NOT_PASSED，原截止不改。新增实际导航尝试{a['new_total_navigation_attempted']}，其中主任务{a['new_main_navigation_attempted']}、重复{a['complete_repeats_attempted']}；复用原13轨迹不计为新样本。新增导航/重放/私有{a['new_navigation_native_steps']}/{a['new_replay_native_steps']}/{a['new_private_integrations']}；来源原导航/重放/私有{a['imported_navigation_native_steps']}/{a['imported_replay_native_steps']}/{a['imported_private_integrations']}。精确/未知标记见终审，不把未知填0。"
report=f'''# RP-CCR V700：{title}

收尾时间：{now}。独立零积分终审状态：**{a['status']}**。原冻结24任务中尝试{a['main_navigation_attempted']}项、生成完整结果{a['main_result_count']}项、完整链到达{a['main_functional_arrivals']}项，未执行{a['main_navigation_unexecuted']}项；{rate}。正/反初始运动方向到达数：{a['groups']}。完整重复尝试{a['complete_repeats_attempted']}/3。

本轮沿用原V698固定98010001–98010024清单与事前连续相位；前13项原轨迹按V699修复审核复核，仅新增余11主任务和固定3重复，不是全新24池；冻结V697初始化修复后的导航算法、8m提案网络与全部安全门不变，算法修订/训练/SAC更新0。不是继续旧夜间或覆盖V696失败。来源及分母见[事前协议](../experiments/v700_rpccr_dynamic_continuation/PROTOCOL.md)。

{provenance_note}

## 实际结果和完整分母

| 任务 | 噪声种子 | 状态 | 公开步 | 终距m | 最低原生实际净空m |
|---|---|---|---|---|---|
{chr(10).join(rows)}

三项预定完整重复为slot1/8/20。逐公开qpos/qvel/ctrl/mocap、模型、规范初态、真实接触事件和首次发现事件要求一致；原始接触SHA分别保留，只允许原注册XML路径来源规范化。详细重复误差与全门审核见[独立终审](../runs/v700_rpccr_dynamic_continuation/FINAL_INDEPENDENT_AUDIT.json)。

## 门槛与实际账目

门槛：24项至少23完整链到达、两方向各≥11/12，三项预定完整重复；每原生步净空≥.15m、障碍接触/穿透/未知0、自体与合法ctrl/速率覆盖、无积分外根改写、全部控制状态重放≤1e-8、因果原始包/集合重建、329执行预测与657规划包含、路线与全部保留尾证书审核。审核未通过时，零碰撞或已到达前缀不能替代完整确认通过。

记录下限：导航原生{a['known_navigation_native_steps']}、重放原生{a['known_native_replay_steps']}、私有积分{a['known_private_integrations']}。账目是否完整精确：导航{a['native_account_exact']}、重放{a['replay_account_exact']}、私有{a['private_account_exact']}；False表示还有未恢复账目，不把未知填0。最低已完成任务实际净空{a['minimum_actual_clearance_m']}m。实际批窗口{ledger['elapsed_s']:.3f}s，上限15000s，原绝对截止不延长。

停止原因：{None if error is None else error['message']}。本轮已闭批，未执行项目不补种子、不刷池；任何下一轮修订需先依据本轮日志定位原因并单独冻结有限协议。旧成功/失败/截止全部保留。原始runs不删除。

## 结论范围

{title}只适用于固定空白8m、一个直径0.20m/振幅0.25m/最大速0.08m/s小障碍、真实途中进入3m量程与公开3m起步排除先验。它不是复杂原场地、任意遮挡突入、多个/更快障碍、长距离、实时性或实机验收；不证明RP-CCR原创性、机制净收益或无限安全。

下一方法研究仍围绕RP-CCR风险、目标进展和可续接走廊恢复，并做同输入/车辆/传感/控制/计算预算对照和消融，见[研究设计](RPCCR_DYNAMIC_MECHANISM_EVIDENCE_PLAN_20261102.md)。

[全证据归档](../evidence/rpccr_dynamic_continuation_v700_20261102/README.md)。工人原始输出位于runs/v697_rpccr_dynamic_initialization/v700_*，批账目位于runs/v700_rpccr_dynamic_continuation；按冻结来源明确标注，没有新导航算法或新权重。
'''
(repo/'docs/RPCCR_DYNAMIC_CONTINUATION_V700_REPORT.md').write_text(report)
(root/'REPORT.md').write_text(report)
current_path=repo/'CURRENT_EXPERIMENT.json';current=read(current_path)
if current.get('protocol')=='experiments/v700_rpccr_dynamic_continuation/PROTOCOL.md':
    current.update(status='V700_FINITE_DYNAMIC_CONTINUATION_PASS_CLOSED' if passed else 'V700_CONTINUATION_NOT_PASSED_CLOSED',active_run=None,active_window=None,active_pid=None,active_entrypoint=None,execution_window_closed=True,requires_user_review_before_next_experiment=True,report='docs/RPCCR_DYNAMIC_CONTINUATION_V700_REPORT.md',evidence='evidence/rpccr_dynamic_continuation_v700_20261102',last_observed_at=now,v700_result={k:v for k,v in a.items() if k not in ['records','repeat_details']})
    dump(current_path,current)
    (repo/'REVIEW_PENDING').write_text(f'V700 closed: {a["status"]}. Read docs/RPCCR_DYNAMIC_CONTINUATION_V700_REPORT.md. No automatic new simulations, repairs, seeds, training or distance extension.\n')
note=f'\n\n## V700 动态原清单接续收尾\n{now}，独立状态{a["status"]}；24项中尝试{a["main_navigation_attempted"]}、完整链到达{a["main_functional_arrivals"]}、未执行{a["main_navigation_unexecuted"]}；正反组{a["groups"]}，重复尝试{a["complete_repeats_attempted"]}/3。导航/重放/私有已知账目{a["known_navigation_native_steps"]}/{a["known_native_replay_steps"]}/{a["known_private_integrations"]}；精确性分别{a["native_account_exact"]}/{a["replay_account_exact"]}/{a["private_account_exact"]}。训练与算法修订0，原V696/V697和旧夜间账目不变。报告docs/RPCCR_DYNAMIC_CONTINUATION_V700_REPORT.md，闭批后不自动追加。\n'
with (repo/'RESEARCH_STATUS.md').open('a') as f:f.write(note)
archive=subprocess.run([sys.executable,'-B',str(own/'archive_evidence.py')],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150)
(repo/'runs/v700_archive.console').write_bytes(archive.stdout);assert archive.returncode==0,'ARCHIVE_ERROR'
archive_result=json.loads(archive.stdout.decode().splitlines()[-1])
with (repo/'evidence/README.md').open('a') as f:f.write(f'\n\n## V700 RP-CCR动态原清单接续\n[完整证据](rpccr_dynamic_continuation_v700_20261102/README.md)独立结论{a["status"]}，尝试{a["main_navigation_attempted"]}/24、完整链到达{a["main_functional_arrivals"]}、未执行{a["main_navigation_unexecuted"]}，重复{a["complete_repeats_attempted"]}/3；全部已归档字节解压哈希核验通过，原始runs保留。见[实际报告](../docs/RPCCR_DYNAMIC_CONTINUATION_V700_REPORT.md)。不凭归档完成宣称导航成功。\n')
dump(root/'FINALIZED.json',{'status':a['status'],'finalized_at':now,'report':'docs/RPCCR_DYNAMIC_CONTINUATION_V700_REPORT.md','archive':archive_result,'automatic_new_simulation':False,'needs_chat_review_commit_and_bounded_sync':True,'simulation_steps_in_finalizer':0})
print((root/'FINALIZED.json').read_text())
