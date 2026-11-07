"""Zero-model closure of a failed fixed geometric qualification."""
import datetime,fcntl,gzip,hashlib,json,signal,zipfile
from pathlib import Path

repo=Path(__file__).resolve().parents[2]
root=repo/'runs/stopping_corridor_20261105';qual=repo/'runs/v815_stopping_corridor_qualification'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(root/'FINALIZED.json').exists()
assert(repo/'REVIEW_PENDING').exists()
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert read(qual/'ROUND_WINDOW.json')['round_closed']
assert not(repo/'runs/v816_stopping_corridor_global/ROUND_WINDOW.json').exists()
audit=read(qual/'FINAL_INDEPENDENT_AUDIT.json');assert audit['status']=='STOPPING_CORRIDOR_QUALIFICATION_NOT_PASSED'
permitted={'registered_functional_qualification','registered_gear_scope'}
for item in audit['records']:assert {k for k,v in item['checks'].items()if not v}<=permitted
freezes=[repo/'experiments'/name/'CANDIDATE_FREEZE.json'for name in['v815_stopping_corridor_qualification','v816_stopping_corridor_global']]
for p in freezes:assert all(sha(repo/n)==h for n,h in read(p)['files'].items())
rows=read(qual/'RESULTS.json');assert [x['label']for x in rows]==['OLD303','OLD375','STOP442','STOP626']
work=sum(x['stats']['spatial_soft_reference']['total_expanded']+x['stats'].get('preferred_search',{}).get('spatial_soft_reference',{}).get('total_expanded',0)for x in rows)
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
lp=repo/'RPCCR_STOPPING_CORRIDOR_LEDGER_20261105.json';ledger=read(lp)
ledger.update(status='CLOSED_ZERO_MODEL_QUALIFICATION_NOT_PASSED',closed=True,closed_at=now,active_simulation=False,
              candidates_started=1,qualification_passed=False,independent_nonfunctional_evidence_checks_passed=True,
              actual_navigation_native=0,actual_private_native=0,actual_replay_native=0,actual_model_initializations=0,
              physical_batches_started=0,physical_main_executed=0,physical_main_unexecuted=3,conditional_repeats_executed=0,conditional_repeats_unexecuted=3,
              fresh_confirmation=0,interface_repairs_used=0,no_more_physics=True,no_frozen_changes=True,
              geometric_search_expansions=work,qualification_wall_s=read(qual/'ROUND_WINDOW.json')['elapsed_s'],
              report='docs/RPCCR_STOPPING_CORRIDOR_V815_REPORT.md',physical_V816_status='PREPARED_FROZEN_DEPENDENCY_NOT_MET_NEVER_STARTED',
              no_navigation_success_rate_defined=True,stop_reason='OLD303 lacks registered full-goal path; OLD375 still has reverse nodes. Do not launch dependent V816 or revise frozen algorithm this round.')
lp.write_text(json.dumps(ledger,indent=2)+'\n')
cp=repo/'CURRENT_EXPERIMENT.json';current=read(cp)
current.update(status='REVIEW_PENDING',state='REVIEW_PENDING',current_experiment='V815_CLOSED_QUALIFICATION_NOT_PASSED_V816_UNEXECUTED',active_automation=None)
current['stopping_corridor_20261105'].update(closed=True,outcome='ZERO_MODEL_QUALIFICATION_NOT_PASSED',physical_started=False,
    physical_main_executed=0,physical_main_unexecuted=3,repeat_executed=0,repeat_unexecuted=3,no_more_physics=True,
    models=0,integrations=0,report=ledger['report'],independent_nonfunctional_evidence_checks_passed=True)
cp.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n')
report=repo/'docs/RPCCR_STOPPING_CORRIDOR_V815_REPORT.md'
report.write_text('''# RP-CCR：制动期限走廊固定资格结果

**结论：V815资格未通过，依赖的V816完整场地导航没有启动。** 本轮全部零模型、零导航、零私有预测、零物理重放，不能报动态成功率0/3或0/24。原三主和条件三完整重复均未执行；没有新24确认。原V812动态功能失败、V813入口失败与V814组件未合格永久保持。

## 做了什么与实际结果

新轮由用户2026-11-05“下一步继续推进”授权，唯一总截止14:02:50+0800。唯一科学变化在全局参考层：保留原19静态体与当前actor外矩形，加入原联合位置—速度单元在完整3.28秒制动期限内的连续扫掠外包。没有用真实actor未来/相位或真实0.08m/s缩小原估计器每轴0.12m/s、加速度0.04m/s²的可达类。原实际8+320原生控制准入、估计器、原329执行/657规划、动作候选评分、模型、传感、网络均未修改。

| 固定保存输入 | 事前要求 | 新参考实际结果 | 资格 |
|---|---|---|---|
| OLD303：首次停车后 | 前向完整目标<=0.28m | 无倒车分段参考，末距1.824903m | 未通过完整目标要求 |
| OLD375：接近瓶颈 | 前向完整目标或意义进展 | 分段参考，末距1.679792m、12个倒车节点 | 未通过前向要求 |
| STOP442：原402分支停稳后 | 描述性检查，合法参考或明确拒绝 | 分段参考，末距1.628814m、12倒车节点 | 如实记录，不能当功能成功 |
| STOP626：原586分支停稳后 | 拒绝已无停靠底线的起点 | START_BELOW_HARD_FLOOR | 正确拒绝，不能当导航成功 |

这些都是旧任务保存输入的几何提案，均未实际执行。数学/代码正确不等于功能达到要求，不统计“2/4成功”。254.533秒资格工作共50742次搜索扩展；部分双向精化到16000扩展上限。OLD303前向精化10532扩展返回前缀，也不能由有限离散搜索推断所有连续车辆控制无解。

## 对失败原因的新约束

旧OLD303完整参考在当前几何下最低约0.180210m，但放入制动期限扫掠外包后最低约-0.353035m，沿原参考约1.528m开始低于0.155m。原参考终点本身仍在该扫掠区外，问题出在途中穿越与姿态约束，不是把目标本身删掉。负下界表示保守因果外包冲突，不是实际障碍发生碰撞。

只用当前占据的参考会进入缺少长期停车余地的区域；把全部未来3.28秒运动范围冻结为沿全线的静态禁行区，又会排除很多原本可能随时间通行的走廊。本轮证据否定“单纯加厚全局障碍，就足以恢复完整前向到达”这一候选资格。原生运动/安全滤波如何跟随这些新参考尚未测试，不能把零模型资格失败说成车辆又走失败一次。

![固定资格对照图](../runs/report_materials_v815_20261105/v815_stopping_corridor_qualification.png)

图中蓝虚线是保存的旧参考，绿线是新参考前缀，橙色是同原因果单元在原制动期限内的扫掠空间，紫点是倒车节点。这是几何提案图，非MuJoCo成功轨迹或执行视频。

## 独立验证与保存

初始未发现时原A*参考精确一致；四个因果输入SHA、原当前占据和静态几何、独立未删重包络的完整加密几何误差0、软代价最大误差1.25e-16、94536个联合单元—时刻包含样本、原1316执行覆盖和2628规划覆盖检查全部通过。源冻结和所有原生安全控制模块字节未变；独立审核只有登记的功能/前向门失败，没有源码/模型/真值/覆盖异常。

连续包络还依赖声明的解析端点极值证明；有限时刻包含样本是独立数值检查，不能当一般运动理论或递归安全证明。新走廊仅是当前估计时刻的几何参考，不替代原生接近、刹停、后续观测或实际到达的证明。

原始来源和解压SHA归档回读、最终结果、报告包见`runs/stopping_corridor_20261105/FINALIZED.json`。原始证据远端未验证前不删除。此次没有操作入口修复、没有重复物理实例、没有训练/SAC/实机或Stage访问。所有旧失败和硬截止未改。

## 下一步设计，尚未实现

需要联合表示通行时刻与可停靠状态：从瓶颈前的实际低速/停车状态出发，区分等待位置和通过走廊，对每次推进/等待都验证完整原生制动后备，并用真实新测距更新原因果集合。不能用固定虚拟速度给路线加一个时间标签后就当可执行，也不能把未来预计观测当已获得的安全证据。

后续资格应同时要求：完整目标的空间—时间路线、可以实际达到的制动/等待状态、实际观测后可续行，以及原全状态重放和固定重复。只增加空间安全膨胀、只禁止倒车或只延长墙钟均未被本轮证据支持。该设计不能冒称已实现、动态全场通过、算法全面优势或RAS创新成立。本轮已封账，不自动启动第二候选或V816导航。
''')
design=repo/'docs/RPCCR_STOPPING_TIME_NEXT_DESIGN_20261105.md'
design.write_text('''# 后续接口设计：通行时间、可停靠状态与原生完整尾

状态：设计草案，未实现、未运行、无新成功样本。依据V815固定资格失败与V814真实停车分支，不修改旧结果。

1. 规划节点至少区分姿态、速度/停稳标志和相对真实测量时刻。等待边只允许从实际可停稳节点出发，并有原完整3.28秒控制证书；不能直接把当前姿态复制成未来安全等待。
2. 空间提案仍可用原Hybrid A*；候选走廊的通行时间必须由原生动力学推进得到或有经核验的保守界，不能用固定0.2m/s虚拟时钟解锁。
3. 每次接近瓶颈前选择能实际达到的停车位置。完整旧尾在新完整尾获证前保持有效，提交动作只走有限前缀；停车/继续均须原合法控制、完整自体、329/657集合、原生净空和无根改写审核。
4. 未来测距/漏检只用于离线评价；在线规划不得假定未来必定看见障碍或外集合必定收缩。真正继续只能依据停车/推进后的真实有噪包以及新原因果证书。未来观测若无信息，必须保持有界拒绝或执行旧安全尾，不能宣称最终必到达。
5. 先固定旧首次停车后的同状态，验证完整路线与至少一个非退让的原生完整前缀+尾，再进入从t0同任务/相位的单候选开发。不能选择成功片段替换全分母，后续开发和新确认分开。
6. 公平工作量包括全部路径搜索、私有原生推进和真实墙钟；不能把规划复杂度增加后的局部成功当同计算增益。任何新协议须先冻结失败停止条件、最大尝试数、绝对截止和独立审计，禁止批量扫描。

这不是对原RP-CCR安全定理、广泛泛化或RAS新颖性的证明。当前瓶颈是空间参考与原生可制动时序的一致性；该草案将其变成可测试的接口，而不是继续调松安全阈值。
''')
with(repo/'RESEARCH_STATUS.md').open('a')as f:
    f.write('\n- FINAL V815唯一制动期限扫掠参考零模型资格NOT_PASSED，V816依赖物理未启动：OLD303无倒车但仅分段末1.824903m/未满足完整目标；OLD375分段末1.679792m且12倒车节点/未满足前向要求，STOP442描述性分段12倒车不当功能成功，STOP626正确拒绝过近起点。初始A*精确，四输入源/当前几何/软值/原329执行657规划/94536单元时刻包含独立审核均PASS（几何误差0/软值最大1.25e-16），仅登记功能门FAIL。254.533s/50742搜索扩展，部分双向16000上限，不能说全连续控制无解。单纯静态膨胀完整制动期限未恢复前向整线，下一通行时间+实际停靠状态接口仅设计。所有模型/导航/私有/重放0，三主/三重复未执行、无新24，不报0/3或0/24；冻结源未改/接口修复0，REVIEW_PENDING/锁空闲，旧失败和截止保持，不自动第二候选。报告docs/RPCCR_STOPPING_CORRIDOR_V815_REPORT.md。\n')
with(root/'HANDOFF.md').open('a')as f:
    f.write('\n## LATEST OVERRIDE\n\n'+now+' V815已全部四资格和独立审核，功能NOT_PASSED，只有OLD303完整目标/OLD375前向门FAIL，其余源/几何/原因果/329/657包含均PASS。V816仅准备冻结、从未启动；原3主/3重复全部未执行，新24无。模型及所有积分精确0，累计搜索50742/254.533s。禁止依赖失败启动V816或改被冻结科学源/重试任务。当前只允许报告图与来源/解压SHA归档及本轮一次有界同步，结束恢复REVIEW_PENDING，所有旧失败不变。\n')
snap=root/'closure_snapshots';snap.mkdir(exist_ok=False)
for name in ['CURRENT_EXPERIMENT.json','RPCCR_STOPPING_CORRIDOR_LEDGER_20261105.json','RESEARCH_STATUS.md','runs/stopping_corridor_20261105/HANDOFF.md']:
    (snap/Path(name).name).write_bytes((repo/name).read_bytes())
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('600S_ZERO_MODEL_ARCHIVE_CAP')));signal.alarm(600)
dest=repo/'evidence/rpccr_stopping_corridor_v815_20261105';assert not dest.exists();dest.mkdir();(dest/'blobs').mkdir()
files=set()
for directory in ['experiments/v815_stopping_corridor_qualification','experiments/v816_stopping_corridor_global','experiments/stopping_corridor_20261105_analysis','runs/v815_stopping_corridor_qualification','runs/stopping_corridor_20261105/closure_snapshots','runs/report_materials_v815_20261105']:
    files.update(p for p in(repo/directory).rglob('*')if p.is_file()and p.suffix not in['.pyc','.lock']and '__pycache__'not in p.parts)
for freeze in freezes:files.update(repo/p for p in read(freeze)['files'])
files.update([repo/'RPCCR_STOPPING_CORRIDOR_AUTHORIZATION_20261105.json',report,design,repo/'runs/stopping_corridor_20261105/PRE_FREEZE_INTERFACE_CHECK.json'])
files.update(p for p in(repo/'runs').glob('v815*.console')if p.is_file())
inventory=[]
for p in sorted(files):
    raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();blob=dest/'blobs'/(h+'.gz')
    if not blob.exists():blob.write_bytes(gzip.compress(raw,mtime=0))
    inventory.append(dict(path=str(p.relative_to(repo)),sha256=h,bytes=len(raw),blob=str(blob.relative_to(dest))))
(dest/'RAW_INVENTORY.json.gz').write_bytes(gzip.compress(json.dumps(inventory,indent=2).encode(),mtime=0))
for row in inventory:
    raw=gzip.decompress((dest/row['blob']).read_bytes())
    assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']and sha(repo/row['path'])==row['sha256']
bundle=dest/'V815_stopping_corridor_report_and_figure.zip'
with zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED)as z:
    for p in [report,design,qual/'FINAL_INDEPENDENT_AUDIT.json',*sorted((repo/'runs/report_materials_v815_20261105').glob('*'))]:
        z.write(p,str(p.relative_to(repo)))
with zipfile.ZipFile(bundle)as z:
    assert z.testzip()is None
    for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==sha(repo/name)
manifest=[dict(path=str(p.relative_to(dest)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(dest.rglob('*'))if p.is_file()]
(dest/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
for x in manifest:assert sha(dest/x['path'])==x['sha256']
closed=dict(status='ZERO_MODEL_QUALIFICATION_NOT_PASSED_EVIDENCE_COMPLETE',qualification_passed=False,all_nonfunctional_evidence_checks_passed=True,
    physical_V816_started=False,models=0,navigation_native=0,private_native=0,replay_native=0,main_unexecuted=3,conditional_repeat_unexecuted=3,fresh_confirmation=0,
    geometric_search_expansions=work,source_freezes_unchanged=True,archive=str(dest.relative_to(repo)),source_files=len(inventory),raw_bytes=sum(x['bytes']for x in inventory),
    manifest_entries=len(manifest),all_source_and_decompressed_sha_readback=True,report=str(report.relative_to(repo)),bundle=str(bundle.relative_to(repo)),raw_deleted=False)
(root/'FINALIZED.json').write_text(json.dumps(closed,indent=2)+'\n')
signal.alarm(0);print(json.dumps(closed))
