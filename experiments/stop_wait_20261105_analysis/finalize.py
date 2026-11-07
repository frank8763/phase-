"""Close the finite component, preserving both the failed and continued entry."""
import datetime,gzip,hashlib,json,signal
from pathlib import Path

repo=Path(__file__).resolve().parents[2];root=repo/'runs/v814_stop_wait_entry_continuation'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(root/'FINALIZED.json').exists()
assert (repo/'REVIEW_PENDING').read_bytes()==(root/'REVIEW_PENDING.before').read_bytes()
first=read(repo/'runs/v813_certified_stop_wait_probe/physical/COMPLETION.json')
second=read(root/'physical/COMPLETION.json');audit=read(root/'physical/FINAL_INDEPENDENT_AUDIT.json')
assert first['status']=='STOPPED_EXCEPTION' and first['counts']['original_replay']==4688
assert second['status']=='FIXED_STOP_WAIT_COMPONENT_NOT_QUALIFIED' and audit['status']=='FIXED_STOP_WAIT_ALL_SAVED_EVIDENCE_VERIFIED'
assert read(root/'physical/ROUND_WINDOW.json')['round_closed']
for version in ['v813_certified_stop_wait_probe','v814_stop_wait_entry_continuation']:
    assert all(sha(repo/n)==h for n,h in read(repo/'experiments'/version/'INPUT_FREEZE.json')['files'].items())
accounts={k:first['counts'][k]+second['counts'][k]for k in first['counts']}
assert accounts==dict(original_replay=9376,branch_native=1008,branch_replay=1008,private_native=90120,new_global_navigation=0,new_confirmation=0)
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
ledger_path=repo/'RPCCR_STOP_WAIT_LEDGER_20261105.json';ledger=read(ledger_path)
ledger.update(status='CLOSED_COMPONENT_NOT_QUALIFIED',closed=True,closed_at=now,active_simulation=False,
              accurate_integral_accounts=accounts,model_initializations=None,model_count_scope='Internal compilation/load count uninstrumented; unknown, not zero.',
              qualified_fixed_components='0/2; correlated diagnostic branches, not global navigation samples',
              no_more_physics=True,stop_reason='Fixed stop-observe-resume component did not reach preregistered .30m recovery; no new global candidate or navigation.',
              one_entry_repair_exception_recorded=True,source_unchanged=True,independent_evidence_verified=True,report='docs/RPCCR_STOP_WAIT_V813_V814_REPORT.md')
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
current_path=repo/'CURRENT_EXPERIMENT.json';current=read(current_path)
current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',current_experiment='V813_V814_FIXED_COMPONENT_CLOSED_NOT_QUALIFIED',active_automation=None)
current['stop_wait_20261105'].update(closed=True,outcome='COMPONENT_NOT_QUALIFIED',no_more_physics=True,master_pid=None,accurate_integral_accounts=accounts,report=ledger['report'])
current_path.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n')
with(repo/'RESEARCH_STATUS.md').open('a')as f:
    f.write('\n- FINAL V813/V814提前停车组件闭批NOT_QUALIFIED，非新全局导航：V813原4688重放精确后缺模块路径失败保留；V814只路径补全/namespace一次明确操作例外、沿用原900秒绝对截止、无科学逻辑改动，原402/586两固定分支已完成。402完整停车后6次8原生续行+最后320尾，净目标+.067047m，路线当前几何再失效；586停车后原9不同首命令均只能保留倒车后备，0新续行。两点均有新测距命中/age0；理想固定姿态3.28s下界分别.294237/.061207m，后者低于.155；两条19节点当前合格前向参考有13/19、19/19节点不具同3.28s几何停等裕量（非动力学等待证明）。不能说所有控制/更早停等无解，亦不能称简单停等已解决。原安全全部保存独立审核PASS：实际最低.293429m/坏接触0/1008分支全状态控制重放误差0、6完整328新证书/124236覆盖样本复核。累计9376旧重放（两入口各4688）/90120私有/1008真实分支/1008分支重放精确，模型内部加载数未知；新全局导航/确认0。原V812和所有旧失败截止不改，当前REVIEW_PENDING/锁空闲，无新物理；下一制动可停走廊/更早安全停靠点联合全局参考仅设计未验证。报告docs/RPCCR_STOP_WAIT_V813_V814_REPORT.md。\n')
with(repo/'runs/v813_certified_stop_wait_probe/HANDOFF.md').open('a')as f:
    f.write('\n## LATEST OVERRIDE\n\n'+now+' V813/V814均已闭批。原V813缺模块路径STOPPED_EXCEPTION/4688重放保留；一次V814路径接续同截止完成原两分支，组件0/2合格，非整场样本。独立audit_saved全证据通过/最低实际.293429/坏接触0/完整状态误差0；累计原重放9376/私有90120/实际分支1008/分支重放1008，新全局/确认0。两停车方案未达.30m资格，严格停止本轮物理，不开第三入口或新算法。REVIEW_PENDING原字节恢复。只收尾归档与本轮一次有界同步，原始数据不删。\n')
report=repo/'docs/RPCCR_STOP_WAIT_V813_V814_REPORT.md'
report.write_text('''# RP-CCR完整场地：提前停车与续行固定状态诊断

结论：提前刹停这一个组件尚未通过资格，完整场地动态仍未验收通过。本轮没有新整场导航或新确认，两个分支取自已观察的V812失败任务，不能当独立成功率样本。

## 实际做了什么

固定旧402（首次反向全局路线）与586（首次仅倒车后备获准）两个状态，分别完整执行之前已认证的BRAKE_ONLY剩余320原生步。之后只用真实新姿态的原有有噪测距更新原tracker，以原前向全局搜索、原候选/评分和完整8+320动态安全门尝试续行，最后执行保留整尾停车。没有使用真实actor未来来授权控制。

| 固定状态 | 停车后结果 | 实际净目标进展 | 停稳末速 | 组件资格 |
|---|---|---:|---:|---|
| 402 | 6次8原生前缀后参考当前几何失效，完整执行保留尾 | 0.067047m | 6.68e-7m/s | 未过0.30m |
| 586 | 有前向空间前缀，但9个不同首命令都不能保留BRAKE_ONLY完整后备 | 0m | 1.29e-5m/s | 未通过 |

两例在停车后的首次查询均有前向空间参考，故协议中“空间无路才额外等两段”的分支没有触发；不能声称已经检验了所有更长停等策略。第586例获准的反向后备只被诊断计算，没有在此干预分支执行。

## 新证据与原因

两个停车点都有新的真实测距命中，测量年龄0。第402分支停车点的当前与3.28秒理想固定姿态预测下界均约0.294237m，仍有停等空间，但其新19节点前向参考中13个节点没有0.155m的同期限几何停等下界；实际续行很快再触发参考失效。第586分支停车点当前下界约0.494842m，3.28秒理想固定姿态未来下界却只有0.061207m；新参考19个节点全部没有同期限停等下界。9个候选的BRAKE_ONLY完整尾均在第328原生点被拒，早拒绝见证约0.05937–0.06158m。

这些是因果可达外集合下的预测下界，不是实际碰撞。理想固定姿态不是电机命令轨迹，相关查询只用于诊断，不能替代原生安全证明。这也不证明所有实际控制、更早停靠或其他有界规划均无解。

当前主要缺口是：全局参考的“此刻几何能过”，与局部控制需要的“前进后仍有完整制动/等待余地”没有对齐。仅在接近瓶颈后停止，并不自动产生可持续等待的位置；空间路线出现也不等于可立即恢复安全前进。

下一步应在进入瓶颈前联合选择绕行走廊和可停靠位置，用原生完整刹停合同验证这些位置；恢复通行应由新的前向完整证书触发，不能只看空间A*有路。此方法尚未实现或验证；不能直接声称RP-CCR创新、全面优势或动态全场通过。

## 安全、真实性与账目

V814两分支共1008原生验证及1008完整分支重放，最大完整积分状态误差0。最低实际净空0.293429m，障碍接触/穿透/未知接触0，自体/控制幅度及速率/固定静态模型门通过；6个新完整328证书、124236个329执行与657规划覆盖样本及新原始测距原因果均经独立零模型保存审核。安全和证据通过不等于功能通过。

累计精确账目：旧前缀重放9376（两入口各4688）、私有预测90120、真实分支1008、完整分支重放1008；新整场导航0、新确认0、训练/SAC/实机0，Stage完全隔离。模型内部加载/编译次数没有单独计数，保持未知。

操作异常永久保留：V813在完成4688原生精确重放后，导入全局场模块缺hybrid_planner搜索路径而失败，分支与私有0。随后V814作了一次明确的路径/输出目录接口接续，未遵守原“零修补”操作计划，不能隐瞒为原V813通过。科学逻辑与阈值差异0，沿用原900秒绝对截止，无重置。原ERROR、COMPLETION、冻结源及所有旧失败保留；此次没有第二次接续或新任务。

独立审核：`runs/v814_stop_wait_entry_continuation/physical/FINAL_INDEPENDENT_AUDIT.json`。完整来源/解压SHA归档与闭批结果：`runs/v814_stop_wait_entry_continuation/FINALIZED.json`。原始证据在远端验证之前不删除。
''')
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('600S_SOURCE_ARCHIVE_CAP')));signal.alarm(600)
snap=root/'closure_snapshots';snap.mkdir(exist_ok=False)
for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','RPCCR_STOP_WAIT_LEDGER_20261105.json','runs/v813_certified_stop_wait_probe/HANDOFF.md']:
    (snap/Path(name).name).write_bytes((repo/name).read_bytes())
dest=repo/'evidence/rpccr_stop_wait_v813_v814_20261105';assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir()
files=[]
for directory in ['experiments/v813_certified_stop_wait_probe','experiments/v814_stop_wait_entry_continuation','experiments/stop_wait_20261105_analysis','runs/v813_certified_stop_wait_probe','runs/v814_stop_wait_entry_continuation']:
    files += [p for p in(repo/directory).rglob('*')if p.is_file()and p.suffix not in['.pyc','.lock']and '__pycache__'not in p.parts and p.name!='HANDOFF.md']
files += [repo/n for n in read(repo/'experiments/v814_stop_wait_entry_continuation/INPUT_FREEZE.json')['files']]
files += [repo/'RPCCR_STOP_WAIT_AUTHORIZATION_20261105.json',repo/'RPCCR_STOP_WAIT_ENTRY_CONTINUATION_20261105.json',report]
files += [p for p in(repo/'runs').glob('v81[34]*.console')if p.is_file()]
inventory=[]
for p in sorted(set(files)):
    raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();blob=dest/'blobs'/(h+'.gz')
    if not blob.exists():blob.write_bytes(gzip.compress(raw,mtime=0))
    inventory.append(dict(path=str(p.relative_to(repo)),sha256=h,bytes=len(raw),blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for row in inventory:
    raw=gzip.decompress((dest/row['blob']).read_bytes())
    assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']and sha(repo/row['path'])==row['sha256']
manifest=[dict(path=str(p.relative_to(dest)),sha256=sha(p),bytes=p.stat().st_size)for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for row in manifest:assert sha(dest/row['path'])==row['sha256']
closed=dict(status='FIXED_COMPONENT_NOT_QUALIFIED_EVIDENCE_COMPLETE',component_qualified=False,full_global_dynamic_passed=False,
            accurate_accounts=accounts,models=None,source_unchanged=True,one_operational_entry_exception_preserved=True,
            independent_saved_audit_verified=True,archive=str(dest.relative_to(repo)),source_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),
            all_source_and_decompressed_sha_readback=True,raw_deleted=False,report=str(report.relative_to(repo)),finalizer_models=0,finalizer_integrations=0)
(root/'FINALIZED.json').write_text(json.dumps(closed,indent=2)+'\n');signal.alarm(0);print(json.dumps(closed))
