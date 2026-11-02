"""Bounded zero-integration finalization with truthful outcome and archival."""
import datetime,fcntl,gzip,hashlib,json,os,subprocess,sys
from pathlib import Path
from zoneinfo import ZoneInfo
repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent;root=repo/'runs/v701_rpccr_recovery_ablation'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
lock=(root/'finalize.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if (root/'FINALIZED.json').exists():print((root/'FINALIZED.json').read_text());raise SystemExit(0)
assert read(root/'ROUND_WINDOW.json')['round_closed']
(repo/'REVIEW_PENDING').write_text('V701 navigation window closed; zero-integration final audit and evidence closure pending. No automatic new simulations.\n')
os.environ['OPENBLAS_NUM_THREADS']='1'
run=subprocess.run([sys.executable,'-B',str(own/'audit_ablation_final.py')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=repo,timeout=120)
(root/'final_audit.console').write_bytes(run.stdout);assert run.returncode==0,'FINAL_AUDITOR_CRASH'
a=read(root/'FINAL_INDEPENDENT_AUDIT.json');c=read(root/'ablation01/COMPLETION.json');w=read(root/'ROUND_WINDOW.json');now=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
rows=[]
for record in a['records']:
    m=record['metrics'] or {};rows.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |'%(record['name'],record['mode'],m.get('outcome','未知'),m.get('public_steps','未知'),m.get('backup_steps','未知'),m.get('path_length_m','未知'),m.get('accumulated_goal_regression_m','未知'),m.get('private_integrations','未知'),record['all_physical_evidence']))
effects=[]
for e in a['paired_effects']:
    d=e['complete_tail_minus_full'];effects.append('slot%d：COMPLETE_TAIL − FULL：公开步%s、路径%.6fm、目标退步累计%.6fm、后备步%s、私有积分%s；首次物理差异%s，FULL首次成功续接%s，之前前缀一致%s。'%(e['slot'],d['public_steps'],d['path_length_m'],d['accumulated_goal_regression_m'],d['backup_steps'],d['private_integrations'],e['first_physical_state_or_command_difference_step'],e['first_full_certified_return_step'],e['identical_prefix_before_disabled_decision']))
report=f'''# V701 RP-CCR恢复续接机制诊断

收尾{now}，证据终审状态 **{a['status']}**；这是诊断完整性，不能读作机制优越PASS。原V700原清单24/24有限课程结果与原V698 NOT_PASSED均保持。

选择原24项中最先实际触发中途续接的两个旧案例slot14/20，FULL与COMPLETE_TAIL成对，另重复COMPLETE_TAIL各一次。最多6执行，未执行{a['unexecuted_registered_executions']}。0新独立确认任务、0训练；车辆/传感/噪声/安全不变，实际计算分别记录。FULL额外续接预测工作不能隐藏或当作同实际计算收益。不是完整RP-CCR净收益或泛化证明。

| 执行 | 模式 | 结果 | 公开步 | 后备步 | 路径m | 目标退步累计m | 私有积分 | 全部物理证据 |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## 成对差异

{chr(10).join(effects)}

所有原生安全/控制/自体/因果覆盖/发现停车/状态重放/尾证书门及前缀与完整重复结果见[独立终审](../runs/v701_rpccr_recovery_ablation/FINAL_INDEPENDENT_AUDIT.json)。候选更差/相同/不达均保留，不调参救回。两FULL应与原V700基准完全一致；两消融重复功能结果和完整状态/控制/接触必须一致，否则诊断不完整。

导航原生{a['navigation_native_steps']}、重放{a['replay_native_steps']}、私有{a['private_integrations']}为已知账目；精确性分别{a['native_account_exact']}/{a['replay_account_exact']}/{a['private_account_exact']}，未知不填0。窗口{w['elapsed_s']:.3f}s，上限7200s，不重置。全部原始证据保留，收尾新增积分0。

局限：已观察机制活跃的两个旧任务、固定空白8m/单慢速actor/公共3m起步先验；需独立新任务、计算预算控制和强基线，才评价方法收益。未证明任意遮挡突入、复杂场地、概率校准、实时性、递归可行或无限安全。协议[PROTOCOL](../experiments/v701_rpccr_recovery_ablation/PROTOCOL.md)，[全证据](../evidence/rpccr_recovery_ablation_v701_20261102/README.md)。闭批停止并待用户审阅，不自动再跑新机制或更长距离。
'''
(repo/'docs/RPCCR_RECOVERY_ABLATION_V701_REPORT.md').write_text(report);(root/'REPORT.md').write_text(report)
current=read(repo/'CURRENT_EXPERIMENT.json')
if current.get('protocol')=='experiments/v701_rpccr_recovery_ablation/PROTOCOL.md':
    current.update(status='V701_RECOVERY_ABLATION_CLOSED',active_run=None,active_window=None,active_pid=None,active_entrypoint=None,execution_window_closed=True,requires_user_review_before_next_experiment=True,report='docs/RPCCR_RECOVERY_ABLATION_V701_REPORT.md',last_observed_at=now,v701_result={k:v for k,v in a.items() if k not in ['records','comparisons']});dump(repo/'CURRENT_EXPERIMENT.json',current)
    (repo/'REVIEW_PENDING').write_text('V701 diagnostic closed: '+a['status']+'. Read docs/RPCCR_RECOVERY_ABLATION_V701_REPORT.md. No automatic additional simulations.\n')
with (repo/'RESEARCH_STATUS.md').open('a') as stream:stream.write('\n\n## V701机制诊断闭批\n'+now+' '+a['status']+'；6固定执行中完成记录'+str(len(a['records']))+'，未执行'+str(a['unexecuted_registered_executions'])+'；导航/重放/私有已知'+str(a['navigation_native_steps'])+'/'+str(a['replay_native_steps'])+'/'+str(a['private_integrations'])+'，精确性'+str([a['native_account_exact'],a['replay_account_exact'],a['private_account_exact']])+'。不是机制优越PASS或独立确认，原V700/V698不改，停止待审阅。\n')
archive=subprocess.run([sys.executable,'-B',str(own/'archive_ablation.py')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=repo,timeout=150)
(repo/'runs/v701_archive.console').write_bytes(archive.stdout);assert archive.returncode==0,'ARCHIVE_ERROR'
ar=json.loads(archive.stdout.decode().splitlines()[-1]);dump(root/'FINALIZED.json',{'status':a['status'],'finalized_at':now,'archive':ar,'report':'docs/RPCCR_RECOVERY_ABLATION_V701_REPORT.md','verification_integrations':0,'needs_review_commit_and_bounded_sync':True,'automatic_new_simulation':False})
print((root/'FINALIZED.json').read_text())
