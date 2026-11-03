"""Close this development without reopening or interpreting evidence completeness as acceptance."""
import datetime,fcntl,json,subprocess,sys
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v710_joint_field_development'
read=lambda p:json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
with (root/'finalize.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (root/'FINALIZED.json').exists():print((root/'FINALIZED.json').read_text());raise SystemExit(0)
 assert read(root/'ROUND_WINDOW.json')['round_closed']
 (repo/'REVIEW_PENDING').write_bytes((root/'REVIEW_PENDING.before').read_bytes())
 result=subprocess.run([sys.executable,'-B',str(own/'audit_field_final.py')],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
 (root/'independent_audit.console').write_bytes(result.stdout);assert result.returncode==0,'FINAL_AUDITOR_EXCEPTION'
 a=read(root/'FINAL_INDEPENDENT_AUDIT.json');now=datetime.datetime.now().astimezone().isoformat();w=read(root/'ROUND_WINDOW.json')
 lines=['# V710联合资格后的原完整场地开发','',a['status']+'，收尾'+now+'。仅同一原始布局上的3条固定起终点路线开发；不是独立24验收、不是算法优势。','', '| 执行 | 路线 | 结果 | 公开步 | 全证据 |','|---|---|---|---:|---|']
 for x in a['records']:lines.append('| '+x['name']+' | '+x['case_id']+' | '+x['outcome']+' | '+str(x['public_steps'])+' | '+str(x['passed'])+' |')
 lines+=['','未执行：'+str(a['unexecuted'])+'；失败审核：'+str([k for k,v in a['checks'].items() if not v])+'。','', '实际原生/重放/私有：'+str([a[k] for k in ['navigation_native_steps','replay_native_steps','private_integrations']])+'；精确性 '+str([a[k] for k in ['native_account_exact','replay_account_exact','private_account_exact']])+'。未知不填0。','', '5400秒开发窗口，实际'+str(w['elapsed_s'])+'秒，原绝对截止'+str(w['absolute_deadline_unix'])+'不延长。本轮为用户2026-11-03新授权的独立白天开发，旧夜间已封账，不重置旧截止。','', '小actor直径.20/振幅.25/最大速度.08不变；所有已知墙体/静态实体保留。完整扫掠非封路证据是真值离线几何证明，不进入在线感知、路径或控制。本修订加载V709冻结联合资格：东西两路线扫掠绕行，南北为附近观测且原参考扫掠外安全；不声称南北必需绕行。全部地图、运动、安全门与线上RP-CCR保持。3m初始排除先验原点仅随公开机器人起点平移，不声称任意遮挡突入。','', '仅当所有开发/重复/物理/因果/模型/重放审核通过，才允许事前冻结后另立原预留24项确认。失败保留，不自动换池/放宽阈值；本轮物理开发候选1个；失败后停止并诊断，不自动调参重跑。训练/Stage/实机0，当前REVIEW_PENDING已恢复。']
 report=repo/'docs/RPCCR_JOINT_FIELD_V710_REPORT.md';report.write_text('\n'.join(lines)+'\n')
 r=subprocess.run([sys.executable,'-B',str(own/'archive_field.py')],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150);(root/'archive.console').write_bytes(r.stdout);assert r.returncode==0,'ARCHIVE_EXCEPTION';archive=json.loads(r.stdout.decode().splitlines()[-1])
 dump(root/'FINALIZED.json',{'status':a['status'],'archive':archive,'report':str(report.relative_to(repo)),'finalized_at':now,'new_integrations_in_finalizer':0,'development_only':True})
 c=read(repo/'CURRENT_EXPERIMENT.json');c.update(status='V710_'+a['status'],active_run=None,active_pid=None,active_automation=None,entrypoint=None,analysis_active=None,analysis_window_closed=True,requires_user_review_before_next_experiment=True,report=str(report.relative_to(repo)),v710_result=a);dump(repo/'CURRENT_EXPERIMENT.json',c)
 with (repo/'RESEARCH_STATUS.md').open('a') as f:f.write('\n- V710闭批'+now+' '+a['status']+'，三固定路线开发，实际/失败/未执行/重复和准确或未知积分分账见docs/RPCCR_JOINT_FIELD_V710_REPORT.md；原独立24确认仍未执行。原始证据保留，REVIEW_PENDING恢复，本轮5400秒截止不延长，旧夜间封账和失败保持。\n')
 print((root/'FINALIZED.json').read_text())
