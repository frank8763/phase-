"""Idempotent zero-integration closure with immutable raw evidence archive."""
import datetime,fcntl,json,subprocess,sys
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v724_progress_observation_recovery'
read=lambda p:json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
with (root/'finalize.lock').open('a+')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (root/'FINALIZED.json').exists():print((root/'FINALIZED.json').read_text());raise SystemExit(0)
 w=read(root/'ROUND_WINDOW.json');assert w['round_closed'];(repo/'REVIEW_PENDING').write_bytes((root/'REVIEW_PENDING.before').read_bytes())
 with (root/'independent_audit.console').open('w')as out:r=subprocess.run([sys.executable,'-B',str(own/'audit_field_final.py')],cwd=repo,stdout=out,stderr=subprocess.STDOUT,timeout=180)
 assert r.returncode==0,'FINAL_INDEPENDENT_AUDITOR_EXCEPTION';audit=read(root/'FINAL_INDEPENDENT_AUDIT.json');now=datetime.datetime.now().astimezone().isoformat()
 lines=['# V724 RP-CCR进展与观测恢复选择单任务开发','',audit['status']+'，闭批'+now+'。','', '一个原WEST_EAST任务及成功条件一个完整重复；原地图/actor/seed/phase/车辆/网络和全部物理安全门保持。保留V721时序未知域，只改未发现阶段反向尾的进展与可见性排序。不是独立24确认或三路线验收。','', '| 执行 | 结果 | 公开步 | 全证据 |','|---|---|---:|---|']
 for row in audit['records']:lines.append('| '+row['name']+' | '+row['outcome']+' | '+str(row['public_steps'])+' | '+str(row['passed'])+' |')
 lines+=['','未执行：'+str(audit['unexecuted'])+'；未通过终审项：'+str([k for k,v in audit['checks'].items()if not v])+'。','', '导航/重放/私有：'+str([audit[k]for k in ['navigation_native_steps','replay_native_steps','private_integrations']])+'；精确标志：'+str([audit[k]for k in ['native_account_exact','replay_account_exact','private_account_exact']])+'，未知不填0。','', '窗口上限2700秒，原绝对截止'+str(w['absolute_deadline_unix'])+'不延长，实际'+str(w['elapsed_s'])+'秒。V714–V723离线/诊断及原V712失败分账，不能混成独立成功率。','', '初始3m先验仍是公开任务假设，最大量程/dropout仍未知，未插入真值。全部网格状态由实际历史测距在线重建，未来运动保守外扩；首次检测后仍沿原跟踪器，完整发现/制动/新路径/继续/到达链与每原生安全/状态重放必须全过才计完整功能。几何证明与新方法规划不是动态通过。','', '已停止，REVIEW_PENDING恢复，原始证据保留；不自动追加修订/物理接续/新池/训练。外部公平对比未执行。']
 report=repo/'docs/RPCCR_PROGRESS_OBSERVATION_V724_REPORT.md';report.write_text('\n'.join(lines)+'\n')
 with (root/'archive.console').open('w')as stream:r=subprocess.run([sys.executable,'-B',str(own/'archive_field.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=150)
 assert r.returncode==0,'ARCHIVE_EXCEPTION';archive=json.loads((root/'archive.console').read_text().splitlines()[-1]);write(root/'FINALIZED.json',dict(status=audit['status'],archive=archive,report=str(report.relative_to(repo)),finalized_at=now,new_integrations_in_finalizer=0,development_only=True))
 c=read(repo/'CURRENT_EXPERIMENT.json');c.update(status='V724_'+audit['status'],active_run=None,active_pid=None,entrypoint=None,active_entrypoint=None,active_automation=None,analysis_active=None,analysis_window_closed=True,execution_window_closed=True,requires_user_review_before_next_experiment=True,report=str(report.relative_to(repo)),v724_result=audit);write(repo/'CURRENT_EXPERIMENT.json',c)
 with (repo/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- V724闭批'+now+' '+audit['status']+'；实际/失败/未执行和准确未知账目见docs/RPCCR_PROGRESS_OBSERVATION_V724_REPORT.md。原V712/V714–V723结果不改，REVIEW_PENDING恢复，无自动追加候选/积分。\n')
 print((root/'FINALIZED.json').read_text())
