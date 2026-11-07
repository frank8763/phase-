"""Zero-model closure checks and operational records for the completed V820 batch."""
import fcntl
import gzip
import hashlib
import json
import signal
from datetime import datetime
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
root = repo / 'runs/v820_tracked_norm_global'
out = repo / 'runs/tracked_norm_20261105/CLOSURE_CHECKS.json'
assert not out.exists(), 'CLOSURE_ALREADY_RECORDED'
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('600S_CLOSURE_LIMIT')))
signal.alarm(600)
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, value):
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


final = read(root / 'FINALIZED.json')
audit = read(root / 'FINAL_INDEPENDENT_AUDIT.json')
assert final['development_passed'] and audit['development_passed']
assert read(root / 'ROUND_WINDOW.json')['round_closed']
assert not Path('/proc/164434').exists(), 'REGISTERED_DRIVER_STILL_PRESENT'
assert (repo / 'REVIEW_PENDING').read_bytes() == (root / 'REVIEW_PENDING.before').read_bytes()
with (repo / 'runs/v648_static_unknown/execution.lock').open('rb') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    fcntl.flock(lock, fcntl.LOCK_UN)
freeze = read(repo / 'experiments/v820_tracked_norm_global/CANDIDATE_FREEZE.json')
assert all(sha(repo / p) == h for p, h in freeze['files'].items())
repeat = read(root / 'repeat_slot01/paired/EXACT_REPEAT_AUDIT.json')
assert repeat['passed'] and all(repeat['checks'].values())
assert max(repeat['errors'].values()) == 0
chains = {}
for name in ['main_slot01', 'repeat_slot01']:
    chain = read(root / name / 'paired/discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json')
    assert chain['status'] == 'PASS' and all(chain['checks'].values())
    chains[name] = chain['details']

archives = []
for name in ['qualification', 'component', 'global_v820']:
    directory = repo / f'evidence/rpccr_tracked_norm_{name}_20261105'
    manifest = read(directory / 'MANIFEST.json')
    for item in manifest:
        p = directory / item['path']
        assert p.stat().st_size == item['bytes'] and sha(p) == item['sha256']
    inventory = json.loads(gzip.decompress((directory / 'RAW_INVENTORY.json.gz').read_bytes()))
    decoded = {}
    for item in inventory:
        source = (repo / item['path']).resolve()
        assert source.is_relative_to(repo), 'SOURCE_OUTSIDE_PHASE'
        assert sha(source) == item['sha256']
        key = (item['blob'], item.get('encoding', 'gzip'))
        if key not in decoded:
            data = (directory / item['blob']).read_bytes()
            raw = data if key[1] == 'identity' else gzip.decompress(data)
            decoded[key] = (len(raw), hashlib.sha256(raw).hexdigest())
        assert decoded[key] == (item['bytes'], item['sha256'])
    transport = read(repo / f'evidence/rpccr_tracked_norm_{name}_20261105_transport/TRANSPORT_MANIFEST.json')
    for entry in transport['entries']:
        digest = hashlib.sha256()
        length = 0
        for chunk in entry['chunks']:
            data = (repo / chunk['path']).read_bytes()
            assert len(data) == chunk['bytes'] and hashlib.sha256(data).hexdigest() == chunk['sha256']
            digest.update(data)
            length += len(data)
        assert length == entry['bytes'] and digest.hexdigest() == entry['sha256']
        assert sha(repo / entry['original_blob']) == entry['sha256']
    archives.append(dict(archive=str(directory.relative_to(repo)), sources=len(inventory),
                         raw_bytes=sum(x['bytes'] for x in inventory), manifest_entries=len(manifest),
                         source_and_decompressed_sha_verified=True, transport_reassembly_verified=True))

stamp = datetime.now().astimezone().isoformat()
summary = dict(status='CLOSED_ONE_DEVELOPMENT_AND_EXACT_REPEAT_VERIFIED', closed_at=stamp,
               main_successes=1, main_attempts=1, complete_repeats_passed=1, new_confirmation_tasks=0,
               execution_lock_free=True, review_guard_exact=True, scientific_source_unchanged=True,
               repeated_qpos_qvel_ctrl_mocap_max_error=0.0, discovery_chains=chains, archives=archives,
               accounts=dict(old_replay_native=4784, component_private_native=656,
                             component_scene_native=656, component_repeat_native=656,
                             full_navigation_native=audit['actual_navigation_native'],
                             full_navigation_private_native=audit['private_native'],
                             full_navigation_replay_native=audit['replay_native']),
               model_initialization_count=None, new_models_this_closure=0, new_integrations_this_closure=0,
               automation_deleted=True, automation_id='phase-v820',
               stop_reason='Registered original task and success-conditional repeat completed; no further simulations authorized in this batch.',
               remote_verification='PENDING_SINGLE_BOUNDED_FINAL_SYNC')
dump(out, summary)

p = repo / 'CURRENT_EXPERIMENT.json'
current = read(p)
current.update(status='REVIEW_PENDING', state='REVIEW_PENDING', active_automation=None,
               active_entrypoint=None, active_run=None, active_window=None, execution_window_closed=True,
               requires_user_review_before_next_experiment=True,
               protocol='experiments/v820_tracked_norm_global/PROTOCOL.md',
               decision_freeze='experiments/v820_tracked_norm_global/CANDIDATE_FREEZE.json',
               source_revision='V820_DECLARED_NORM_REFINED_COMPLETE_CAUSAL_PREFIX_TAIL',
               report='docs/RPCCR_TRACKED_NORM_V820_REPORT.md',
               evidence='evidence/rpccr_tracked_norm_global_v820_20261105')
current['tracked_norm_20261105'].update(models_started=True, model_initializations=None,
    automation_id=None, monitor_deleted=True, closed_at=stamp,
    main_successes=1, main_attempts=1, complete_repeats_passed=1, fresh_confirmation=0,
    full_confirmation_passed=False, closure_checks=str(out.relative_to(repo)))
dump(p, current)
p = repo / 'RPCCR_TRACKED_NORM_LEDGER_20261105.json'
ledger = read(p)
ledger.update(closed_at=stamp, automation_id=None, monitor_deleted=True,
              main_successes=1, main_attempts=1, complete_repeats_passed=1,
              closure_checks=str(out.relative_to(repo)), raw_deleted=False,
              sync_status='PENDING_SINGLE_BOUNDED_FINAL_SYNC')
dump(p, ledger)

report = repo / 'docs/RPCCR_TRACKED_NORM_V820_REPORT.md'
main_wall = audit['records'][0]['result']['elapsed_s']
repeat_wall = audit['records'][1]['result']['elapsed_s']
report.write_text(report.read_text() + f'''
## 零模型闭批复核

主任务1/1成功，同一任务完整重复1/1通过；重复不计为新独立样本，新24确认未执行。
两次均847公开步/6776原生步，终点距离0.442654883m，满足原0.45m目标容差。
逐原生最低实际净空0.254123834m，障碍接触、穿透、未知接触均0；完整状态控制重放及主/重复qpos/qvel/ctrl/mocap最大误差均0。模型、规范初态、真实接触和发现事件匹配。

完整发现链：第262公开步/20.96s真实测距首次发现，此前车辆速度0.218961m/s、已前进4.350554m；随后完整执行328原生刹停，末速3.53394e-6m/s；第303步生成新原因果路线，停车后实际位移3.526009m，最终到达。两次各12项原审核、完整发现链和独立终审全部通过。
主/重复分别用{main_wall:.3f}s/{repeat_wall:.3f}s墙钟完成各67.76s仿真，不能称实时；私有工作量按实际10284544原生计，不与其他算法宣称等计算优势。

本轮前置组件另外记录4784旧重放/656私有/656实际分支/656完整分支重复，未混入完整导航13552/私有10284544/重放13552。内部模型初始化总数未知，未填成0。
V818缺模块路径、V820首次缺输出父目录及冻结前NumPy布尔序列化错误均保留原日志；路径接续和额外目录准备例外已分别记录，未覆盖失败、重跑已执行导航或修改冻结科学源。

反应式发现前静态合同继承V806/V812，本次新改动是跟踪后公开0.08m/s欧氏速度约束下的有效净空下界精化。0.155m预测/0.15m实际阈值和完整328时长保持；更宽每轴0.12m/s类未通过。单个已观察开发任务的成功不能代替三路线及新池验收、复杂地图泛化、任意遮挡突入或RP-CCR独立增量证据。
下一步应在用户审阅后另立有界协议验证其余固定路线及完整重复，开发全门通过后再冻结新任务确认；公平算法对比尚未执行。

全部三个阶段原归档再次核验来源/解压SHA；超大原blob以32MiB无损块传输并重组核验，原件和runs保留。执行锁空闲、REVIEW_PENDING原字节恢复；phase-v820监控已删除，停止原因是本批登记任务及重复完成，不追加模拟。
''')

with (repo / 'RESEARCH_STATUS.md').open('a') as stream:
    stream.write(f'\n- FINAL {stamp} V820原完整场地WEST_EAST/10010001开发1/1成功，条件完整重复1/1全状态控制误差0；两次847公开/6776原生、目标余.442654883m、最低实际.254123834m、障碍穿透未知0，原12审核/完整发现链/独立终审及全归档来源解压SHA回读通过。实际262发现/328刹停/303新原因果路线/停车后位移3.526009m/到达全链成立。完整导航13552/私有10284544/重放13552；组件4784旧重放/656私有/656分支/656重复另记，模型内部加载数未知。仅公开.08norm课程，原更宽.12轴类及全场新24未验收；原V818路径、V820父目录错误及全部旧失败保持。三个阶段原始归档与32MiB传输块核验，原件不删。REVIEW_PENDING原字节恢复/执行锁空闲，phase-v820已删除，本轮不追加模拟。报告docs/RPCCR_TRACKED_NORM_V820_REPORT.md；同步只按本轮一次有界计划进行。\n')
with (repo / 'runs/tracked_norm_20261105/HANDOFF.md').open('a') as stream:
    stream.write(f'\n## LATEST OVERRIDE\n\n{stamp} V820已独立闭批ONE_TRACKED_NORM_DEVELOPMENT_VERIFIED，原一主和条件完整重复均GOAL且全门/精确重复/来源解压SHA通过。REVIEW_PENDING原字节恢复、执行锁空闲、master已退出、phase-v820监控实际删除；停止该批，不启动任何追加模型/导航/预测/重放。新24确认0，原更宽每轴.12类未过。全部准确积分分账见CLOSURE_CHECKS.json及根台账；原失败/窗口及原始大blob保留。最后同步只允许本轮一次30s push+5s远端HEAD核验，先查runs/v820_git_sync_result.json避免重复。\n')
signal.alarm(0)
print(json.dumps({k:v for k,v in summary.items() if k != 'discovery_chains'}, ensure_ascii=False))
