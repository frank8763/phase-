"""Zero-integration final audit, honest report and immutable evidence archive."""
import datetime,fcntl,json,subprocess,sys
from pathlib import Path

repo=Path(__file__).resolve().parents[2];own=Path(__file__).resolve().parent
root=repo/'runs/v704_bootstrap_repair';root.mkdir(exist_ok=True)
lock=(root/'finalize.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
if (root/'FINALIZED.json').exists():
    print((root/'FINALIZED.json').read_text());raise SystemExit(0)
original=repo/'runs/v704_setup/REVIEW_PENDING.before'
assert original.exists(),'ORIGINAL_REVIEW_GUARD_NOT_SAVED'
(repo/'REVIEW_PENDING').write_bytes(original.read_bytes())
audit=subprocess.run([sys.executable,'-B',str(own/'audit_repair_final.py')],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
(root/'final_independent_audit.console').write_bytes(audit.stdout)
assert audit.returncode==0 and (root/'FINAL_INDEPENDENT_AUDIT.json').exists(),'INDEPENDENT_AUDIT_CRASH'
a=read(root/'FINAL_INDEPENDENT_AUDIT.json');window=read(root/'ROUND_WINDOW.json');completion=read(root/'repair01/COMPLETION.json')
assert window['round_closed'] and completion['round_closed']
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
lines=['# V704 初始化入口修复与原轨迹校准','',
       '本轮结论：**'+a['status']+'**。这是初始化工程修复及旧轨迹校准，不是新任务导航确认或RP-CCR独立优越性结论。',
       '', '修复只在新factory进入旧reset之前关闭无用旧detour分支；旧reset和任务门保留。线上RP-CCR/感知/网络/安全/执行/规划不变。原V702预检超时、V703结构化写出失败、原COMPLETION与截止保留。',
       '', '| 校准 | 实际功能 | 公开步 | 原轨迹等价 |', '|---|---|---:|---|']
comparisons={x['name']:x for x in a['comparisons']}
for x in a['records']:
    m=x['metrics'] or {};lines.append('| '+x['name']+' | '+str(m.get('outcome','未完成/未知'))+' | '+str(m.get('public_steps','未知'))+' | '+str(comparisons.get(x['name'],{}).get('passed',False))+' |')
pre=root/'PREFLIGHT_INDEPENDENT_AUDIT.json';p=read(pre) if pre.exists() else None
lines+=['','4原预检独立原始噪声/模型/初态/初始化证明审核：'+str(p.get('status') if p else '未完成')+'。原45/50秒上限不增加，原99010001–04及相位不换。',
        '','新增导航原生步 '+str(a['navigation_native_steps'])+'；完整重放 '+str(a['replay_native_steps'])+'；私有预测 '+str(a['private_integrations'])+'。三项精确标志分别为 '+str([a[k] for k in ['native_account_exact','replay_account_exact','private_account_exact']])+'；不精确时数字仅为已知部分。',
        '', '窗口实际 '+str(window['elapsed_s'])+' 秒，事前2700秒，绝对截止 '+str(window['absolute_deadline_unix'])+' 未延长。未执行校准 '+str(a['unexecuted_registered_executions'])+'。原4新任务主导航全部未执行，成功率与新机制触发率未评估，不报0/4。',
        '', '审核不通过项：'+str([k for k,v in a['checks'].items() if not v])+'。通过仅允许下一轮另立有界协议继续原4项成对任务；本轮不自动启动。REVIEW_PENDING恢复，训练/Stage/实机0，原始证据保留。']
report=repo/'docs/RPCCR_BOOTSTRAP_REPAIR_V704_REPORT.md';report.write_text('\n'.join(lines)+'\n')
c=read(repo/'CURRENT_EXPERIMENT.json');c.update(status='V704_'+a['status'],report=str(report.relative_to(repo)),active_automation=None,analysis_active=None,analysis_window_closed=True,v704_result=a)
dump(repo/'CURRENT_EXPERIMENT.json',c)
with (repo/'RESEARCH_STATUS.md').open('a') as f:f.write('\n- V704闭批 '+now+'：'+a['status']+'，4原种子预检及2旧锚点校准的实际执行/未执行见报告。新增原生/重放/私有 '+str([a[k] for k in ['navigation_native_steps','replay_native_steps','private_integrations']])+'，精确标志 '+str([a[k] for k in ['native_account_exact','replay_account_exact','private_account_exact']])+'。原4新任务导航0，不报成功率；初始化工程修复不算算法创新，旧V702/V703失败不改，REVIEW_PENDING恢复，不自动追加导航。报告docs/RPCCR_BOOTSTRAP_REPAIR_V704_REPORT.md。\n')
with (repo/'AGENTS.md').open('a') as f:f.write('\n- FINAL V704 '+a['status']+'；只修新factory reset之前旧detour开关，4预检/2旧slot14校准上限，全部实际/失败/未执行与原轨迹等价见docs/RPCCR_BOOTSTRAP_REPAIR_V704_REPORT.md。原4新任务导航仍0，旧失败/源码/截止不改；REVIEW_PENDING恢复，不自动追加新4对/距离/训练，Stage完全隔离。\n')
ar=subprocess.run([sys.executable,'-B',str(own/'archive_repair.py')],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150)
(root/'archive.console').write_bytes(ar.stdout);assert ar.returncode==0,'ARCHIVE_ERROR'
archive=json.loads(ar.stdout.decode().splitlines()[-1]);dump(root/'FINALIZED.json',{'status':a['status'],'finalized_at':now,'archive':archive,'report':str(report.relative_to(repo)),'verification_integrations':0,'review_guard_restored':True,'automatic_new_simulation':False})
print((root/'FINALIZED.json').read_text())
