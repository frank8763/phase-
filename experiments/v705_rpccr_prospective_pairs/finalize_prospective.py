"""Bounded zero-integration finalization with truthful outcome and archival."""
import datetime,fcntl,gzip,hashlib,json,os,subprocess,sys
from pathlib import Path
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent;root=repo/'runs/v705_rpccr_prospective_pairs'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
lock=(root/'finalize.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if (root/'FINALIZED.json').exists():print((root/'FINALIZED.json').read_text());raise SystemExit(0)
assert read(root/'ROUND_WINDOW.json')['round_closed']
(repo/'REVIEW_PENDING').write_bytes((repo/'runs/v705_setup/REVIEW_PENDING.before').read_bytes())
os.environ['OPENBLAS_NUM_THREADS']='1'
run=subprocess.run([sys.executable,'-B',str(own/'audit_prospective_final.py')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=repo,timeout=120)
(root/'final_audit.console').write_bytes(run.stdout);assert run.returncode==0,'FINAL_AUDITOR_CRASH'
a=read(root/'FINAL_INDEPENDENT_AUDIT.json');c=read(root/'prospective01/COMPLETION.json');w=read(root/'ROUND_WINDOW.json');now=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
rows=[]
for record in a['records']:
    m=record['metrics'] or {};rows.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |'%(record['name'],record['mode'],m.get('outcome','未知'),m.get('public_steps','未知'),m.get('backup_steps','未知'),m.get('path_length_m','未知'),m.get('accumulated_goal_regression_m','未知'),m.get('private_integrations','未知'),record['all_physical_evidence']))
pairs=[]
for e in a['paired_effects']:
    pairs.append('| %s | %s | %s | %s | %s | %s | %s |'%(e['slot'],e.get('full_arrival'),e.get('shadow_arrival'),e.get('mechanism_triggered'),e.get('first_full_commit_step'),e.get('first_physical_difference_step'),e.get('status')))
report=f'''# V705 RP-CCR新任务与计算对照

收尾{now}，证据终审状态 **{a['status']}**。这是固定实验数据完整性，不是机制优越PASS。原V700有限课程与V701旧案例诊断、原V698未通过均保持。

新噪声/相位任务4项，在所有结果和是否触发续接未知时按SHA规则锁定；正反方向各2，不筛选未触发/无差异任务。旧校准复用V704两条已独立审计证据、不新增导航；新任务每条件4执行、固定task1每条件完整重复共2，最大10导航。已执行{len(a['records'])}、未执行{a['unexecuted_registered_executions']}。旧校准/重复不计新4任务分母。原训练/算法开发修订0。

## 全执行账目

| 执行 | 模式 | 结果 | 公开步 | 后备步 | 路径m | 目标退步累计m | 私有积分 | 全物理证据 |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## 事前新任务配对

| 任务 | FULL到达 | SHADOW到达 | 实际触发续接 | 首提交步 | 首物理差异步 | 配对审核 |
|---|---|---|---|---|---|---|
{chr(10).join(pairs)}

完整新任务分母4；各条件完整链到达{a['main_arrivals_by_condition']}；全分母成功率{a['full_condition_success_rates']}（None表示未执行完整，不能报全分母率）。在已完成的{len(a['paired_effects'])}对中实际触发{a['mechanism_triggered_pairs']}对；未完成4对时整体触发率未评估，未触发仍保留，不补阳性种子。全原生安全/源模型/控制/状态重放/因果/覆盖/路线/影子与执行证书几何、配对共同前缀计算和两完整重复见[独立终审](../runs/v705_rpccr_prospective_pairs/FINAL_INDEPENDENT_AUDIT.json)。

两组在相同状态均执行原名义候选/进展门/完整后备候选核验；SHADOW只保存未执行证书、继续原安全尾，不改实际状态或保留合同。事前V704校准FULL已复现V701 FULL14，SHADOW已复现V701原不计算续接的tail14物理轨迹，首提交307候选/计算与FULL一致；本轮只冻结和复核其证据，不重复导航或纳入新分母。

导航原生{a['navigation_native_steps']}、完整重放{a['replay_native_steps']}、私有{a['private_integrations']}为已知账目，精确性{a['native_account_exact']}/{a['replay_account_exact']}/{a['private_account_exact']}；未知不能填0。所有影子预测计入私有积分，不计实际导航或到达。窗口{w['elapsed_s']:.3f}s，上限7200s，不延期。收尾0新增积分，原始runs保留。

局限：计算匹配只对相同前缀决策与首提交候选，分叉后总工作/墙钟与终点不同，实际分别报告，不能称同总计算效率。影子消融用于因果诊断，不是有竞争力的强基线。4项仅新噪声/相位小样本、固定空白8m/单慢速actor/公开3m起步先验，未建立新几何泛化、统计显著优势、完整RP-CCR新颖性、实时/概率风险/递归安全或无限必达。

[事前协议](../experiments/v705_rpccr_prospective_pairs/PROTOCOL.md)，[完整证据](../evidence/rpccr_prospective_pairs_v705_20261102/README.md)。已停止，待用户审阅，不自动扩大任务/距离或调参。
'''
(repo/'docs/RPCCR_PROSPECTIVE_PAIRS_V705_REPORT.md').write_text(report);(root/'REPORT.md').write_text(report)
current=read(repo/'CURRENT_EXPERIMENT.json')
if current.get('protocol')=='experiments/v705_rpccr_prospective_pairs/PROTOCOL.md':
    current.update(status='V705_PROSPECTIVE_COMPUTE_CLOSED',active_run=None,active_window=None,active_pid=None,active_entrypoint=None,execution_window_closed=True,analysis_window_closed=True,analysis_active=None,requires_user_review_before_next_experiment=True,report='docs/RPCCR_PROSPECTIVE_PAIRS_V705_REPORT.md',last_observed_at=now,v705_result={k:v for k,v in a.items() if k not in ['records','comparisons']});dump(repo/'CURRENT_EXPERIMENT.json',current)
    (repo/'REVIEW_PENDING').write_bytes((repo/'runs/v705_setup/REVIEW_PENDING.before').read_bytes())
with (repo/'RESEARCH_STATUS.md').open('a') as stream:stream.write('\n\n## V705新任务计算对照闭批\n'+now+' '+a['status']+'；10固定执行中完成记录'+str(len(a['records']))+'，未执行'+str(a['unexecuted_registered_executions'])+'；导航/重放/私有已知'+str(a['navigation_native_steps'])+'/'+str(a['replay_native_steps'])+'/'+str(a['private_integrations'])+'，精确性'+str([a['native_account_exact'],a['replay_account_exact'],a['private_account_exact']])+'。不是机制优越PASS或独立确认，原V700/V698不改，停止待审阅。\n')
archive=subprocess.run([sys.executable,'-B',str(own/'archive_prospective.py')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=repo,timeout=150)
(repo/'runs/v705_archive.console').write_bytes(archive.stdout);assert archive.returncode==0,'ARCHIVE_ERROR'
ar=json.loads(archive.stdout.decode().splitlines()[-1]);dump(root/'FINALIZED.json',{'status':a['status'],'finalized_at':now,'archive':ar,'report':'docs/RPCCR_PROSPECTIVE_PAIRS_V705_REPORT.md','verification_integrations':0,'needs_review_commit_and_bounded_sync':True,'automatic_new_simulation':False})
print((root/'FINALIZED.json').read_text())
